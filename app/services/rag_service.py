import hashlib

from fastapi import Depends
from google.genai import types
from redis.asyncio import Redis

from ..config import settings
from ..redis import get_redis
from ..schemas import RAGResponse
from .embedding_service import client
from .post_service import PostService

SYSTEM_PROMPT = """Sen yardımcı bir soru-cevap (RAG) asistanısın.
    Görevin, kullanıcının sorusunu SADECE aşağıda sana verilen 'Bağlam (Postlar)' içindeki bilgileri
    kullanarak yanıtlamaktır.

    Kurallar:
    1. Kesinlikle kendi dış bilgini kullanma ve varsayımda bulunma.
    2. Eğer verilen postlar soruyu yanıtlamak için yeterli bilgi içermiyorsa veya soruyla alakasızsa,
    `enough_context` alanını `false`, `source_post_ids` alanını `[]` yap ve `answer` alanında mevcut
    gönderilerde bu bilgiye ulaşılamadığını belirt.
    3. Yalnızca yanıtı oluştururken gerçekten kullandığın postların ID'lerini `source_post_ids`
    listesine ekle.
    """


class RagService:
    def __init__(
        self,
        post_service: PostService = Depends(PostService),
        redis: Redis = Depends(get_redis),
    ):
        self.post_service = post_service
        self.redis = redis

    async def ask(self, question: str, limit: int = 5) -> RAGResponse:
        cleaned_question = question.strip().lower()
        cache_key = f"rag:cache:{hashlib.sha256(cleaned_question.encode()).hexdigest()}"
        cached = await self.redis.get(cache_key)

        if cached:
            return RAGResponse.model_validate_json(cached)

        posts = await self.post_service.semantic_search(
            query_text=question, limit=limit
        )

        if not posts:
            return RAGResponse(
                thought_process=[
                    "Veritabanında benzerlik eşiğinin altında alakalı hiçbir post bulunamadı."
                ],
                answer="Veritabanındaki gönderilerde bu soruyla ilgili herhangi bir bilgi bulunamadı.",
                enough_context=False,
                source_post_ids=[],
            )

        context_text = "\n\n---\n\n".join(
            f"Post ID: {p.id}\nYazar: {p.owner.name}\nBaşlık: {p.title}\nİçerik: {p.content}\nMesafe Skoru:{p.distance:.4f}"
            for p in posts
        )

        prompt = f"Bağlam (Postlar:\n{context_text}\n\nKullanıcı Sorusu: {question})"

        response = await client.aio.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RAGResponse,
                temperature=0.0,
            ),
        )

        output = RAGResponse.model_validate_json(response.text)
        await self.redis.set(cache_key, output.model_dump_json(), ex=3600)
        return output

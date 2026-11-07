from fastapi import Depends
from google.genai import types

from ..config import settings
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
    def __init__(self, post_service: PostService = Depends(PostService)):
        self.post_service = post_service

    async def ask(self, question: str, limit: int = 5) -> RAGResponse:
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

        return RAGResponse.model_validate_json(response.text)

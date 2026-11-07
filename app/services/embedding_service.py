from google import genai
from google.genai import types

from ..config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class EmbeddingService:
    async def get_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[float]:

        response = await client.aio.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.EMBEDDING_DIMENSIONS,
            ),
        )

        return response.embeddings[0].values

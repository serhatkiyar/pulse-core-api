from fastapi import APIRouter, Depends, Request

from .. import models
from ..limiter import limiter
from ..oauth2 import get_current_user
from ..schemas import RAGRequest, RAGResponse
from ..services.rag_service import RagService

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/ask", response_model=RAGResponse)
@limiter.limit("10/minute")
async def ask_ai(
    request: Request,
    body: RAGRequest,
    user_credentials: models.User = Depends(get_current_user),
    rag_service: RagService = Depends(RagService),
):
    return await rag_service.ask(question=body.question, limit=body.limit)

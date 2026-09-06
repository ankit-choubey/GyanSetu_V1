from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.evening import ChatbotRequest, ChatbotResponse
from app.services.evening_interfaces import ChatRequest, RagProvider, UnavailableRagProvider

router = APIRouter(tags=["chatbot"])


def get_rag_provider() -> RagProvider:
    return UnavailableRagProvider()


@router.post("/chatbot/ask", response_model=ChatbotResponse)
def ask_chatbot(
    payload: ChatbotRequest,
    user: User = Depends(get_current_user),
    provider: RagProvider = Depends(get_rag_provider),
) -> ChatbotResponse:
    result = provider.answer(ChatRequest(question=payload.question, competency_id=payload.competency_id))
    return ChatbotResponse(
        status=result.status,
        answer=result.answer,
        sources=list(result.sources),
        source_mode=result.source_mode,
    )

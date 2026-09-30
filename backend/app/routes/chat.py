import os
import logging

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value


class ChatResponse(BaseModel):
    success: bool
    response: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Groq service is not configured",
            },
        )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a concise and helpful PocketCFO assistant.",
                    },
                    {"role": "user", "content": request.message},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        response_text = response.json()["choices"][0]["message"]["content"]
        return ChatResponse(success=True, response=response_text)
    except requests.exceptions.Timeout:
        logger.exception("Groq request timed out")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "The Groq service timed out",
            },
        )
    except requests.exceptions.RequestException:
        logger.exception("Groq request error")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "The Groq service is temporarily unavailable",
            },
        )
    except Exception as exc:
        logger.exception("Unexpected chat error")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Unexpected chat error",
            },
        )

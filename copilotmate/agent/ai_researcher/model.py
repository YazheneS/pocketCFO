"""Model configuration for the LangGraph research agent."""

import os
from langchain_groq import ChatGroq


def get_model():
    """Build the Groq chat model used by each graph node."""

    if not os.environ.get("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is required to run the StudyBuddy agent.")

    return ChatGroq(
        model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
    )

"""
This is the state definition for the AI.
It defines the state of the agent and the state of the conversation.
"""

from typing import List, TypedDict, Optional
from langgraph.graph import MessagesState

class Step(TypedDict):
    """
    Represents a step taken in the research process.
    """
    id: str
    description: str
    status: str
    type: str
    search_result: Optional[str]
    result: Optional[str]
    updates: Optional[List[str]]

class Reference(TypedDict):
    """
    Represents a source reference in the final answer.
    """
    title: str
    url: str

class Answer(TypedDict):
    """
    Represents the structured answer rendered by the frontend.
    """
    markdown: str
    references: List[Reference]

class AgentState(MessagesState):
    """
    This is the state of the agent.
    It is a subclass of the MessagesState class from langgraph.
    """
    steps: List[Step]
    answer: Optional[Answer]

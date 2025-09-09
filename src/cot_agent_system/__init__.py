"""
CoT Agent System - A Chain of Thought based agent system for task management and execution.

This package provides a complete agent system that uses Chain of Thought reasoning
to break down complex queries into manageable todos, execute them with feedback loops,
and continuously improve through self-reflection.

Main components:
- CoTAgent: The main agent interface
- TodoManager: Manages todo lifecycle and dependencies
- CoTEngine: Handles Chain of Thought processing
- Models: Pydantic models for data structures
"""

from .agent import CoTAgent
from .todo_manager import TodoManager
from .cot_engine import CoTEngine
from .models import (
    Todo,
    TodoStatus,
    CoTStep,
    CoTProcess,
    FeedbackEntry,
    AgentConfig
)

__version__ = "0.1.0"
__all__ = [
    "CoTAgent",
    "TodoManager", 
    "CoTEngine",
    "Todo",
    "TodoStatus",
    "CoTStep",
    "CoTProcess",
    "FeedbackEntry",
    "AgentConfig"
]

def hello() -> str:
    return "Hello from cot-agent-system!"

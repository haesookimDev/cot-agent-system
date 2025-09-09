from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Todo(BaseModel):
    id: str = Field(..., description="Unique identifier for the todo")
    content: str = Field(..., description="Description of the todo task")
    status: TodoStatus = Field(default=TodoStatus.PENDING, description="Current status of the todo")
    priority: int = Field(default=1, description="Priority level (1=highest, 5=lowest)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    dependencies: List[str] = Field(default_factory=list, description="List of todo IDs this depends on")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    reasoning: Optional[str] = Field(None, description="Reasoning behind this todo")
    feedback: Optional[str] = Field(None, description="Feedback from execution")


class CoTStep(BaseModel):
    step_id: str = Field(..., description="Unique identifier for the step")
    description: str = Field(..., description="Description of the reasoning step")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for this step")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data from this step")
    reasoning: str = Field(..., description="Chain of thought reasoning for this step")
    confidence: float = Field(default=0.0, description="Confidence score (0-1)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class CoTProcess(BaseModel):
    process_id: str = Field(..., description="Unique identifier for the CoT process")
    query: str = Field(..., description="Original user query")
    steps: List[CoTStep] = Field(default_factory=list, description="Chain of thought steps")
    todos: List[Todo] = Field(default_factory=list, description="Generated todos")
    final_answer: Optional[str] = Field(None, description="Final answer or result")
    status: str = Field(default="active", description="Process status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class FeedbackEntry(BaseModel):
    feedback_id: str = Field(..., description="Unique identifier for the feedback")
    todo_id: str = Field(..., description="Related todo ID")
    feedback_type: str = Field(..., description="Type of feedback (success, error, improvement)")
    message: str = Field(..., description="Feedback message")
    suggestions: List[str] = Field(default_factory=list, description="Suggested improvements")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class AgentConfig(BaseModel):
    model_name: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    temperature: float = Field(default=0.7, description="Temperature for LLM generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens for generation")
    max_iterations: int = Field(default=10, description="Maximum iterations for feedback loop")
    thinking_depth: int = Field(default=3, description="Depth of chain of thought reasoning")
import os
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv


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
    api_key: Optional[str] = Field(default=None, description="API key for LLM service")
    log_level: str = Field(default="INFO", description="Logging level")
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "AgentConfig":
        """
        Create AgentConfig from environment variables.
        
        Args:
            env_file: Path to .env file. If None, uses default .env file
            
        Returns:
            AgentConfig instance with values from environment variables
        """
        # Load environment variables
        load_dotenv(env_file)
        
        # Get values from environment with fallback to defaults
        config_data = {
            "model_name": os.getenv("COT_MODEL", "gpt-3.5-turbo"),
            "temperature": float(os.getenv("COT_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("COT_MAX_TOKENS", "1000")),
            "max_iterations": int(os.getenv("COT_MAX_ITERATIONS", "10")),
            "thinking_depth": int(os.getenv("COT_THINKING_DEPTH", "3")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
        
        # Handle API keys - try multiple possible environment variables
        api_key = (
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY") or 
            os.getenv("GOOGLE_API_KEY") or
            os.getenv("API_KEY")
        )
        
        if api_key:
            config_data["api_key"] = api_key
        
        return cls(**config_data)
    
    def update_from_env(self, env_file: Optional[str] = None) -> "AgentConfig":
        """
        Update current config with values from environment variables.
        
        Args:
            env_file: Path to .env file. If None, uses default .env file
            
        Returns:
            Updated AgentConfig instance
        """
        env_config = self.from_env(env_file)
        
        # Update only non-None values from environment
        for field_name, field_value in env_config.model_dump().items():
            if field_value is not None:
                setattr(self, field_name, field_value)
        
        return self
    
    def to_env_template(self) -> str:
        """
        Generate a .env template with current configuration values.
        
        Returns:
            String containing .env template
        """
        template = f"""# CoT Agent System Configuration

# LLM Model Configuration
COT_MODEL={self.model_name}
COT_TEMPERATURE={self.temperature}
COT_MAX_TOKENS={self.max_tokens}
COT_MAX_ITERATIONS={self.max_iterations}
COT_THINKING_DEPTH={self.thinking_depth}

# API Keys (uncomment and set the appropriate one)
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here

# Logging
LOG_LEVEL={self.log_level}

# Additional settings can be added here
"""
        return template
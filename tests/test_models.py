import pytest
from datetime import datetime
from cot_agent_system.models import Todo, TodoStatus, CoTStep, CoTProcess, FeedbackEntry, AgentConfig


class TestTodo:
    def test_todo_creation(self):
        todo = Todo(
            id="test-id",
            content="Test todo content"
        )
        
        assert todo.id == "test-id"
        assert todo.content == "Test todo content"
        assert todo.status == TodoStatus.PENDING
        assert todo.priority == 1
        assert isinstance(todo.created_at, datetime)
        assert todo.dependencies == []
        assert todo.metadata == {}
    
    def test_todo_with_dependencies(self):
        todo = Todo(
            id="test-id",
            content="Test todo",
            dependencies=["dep1", "dep2"],
            priority=2
        )
        
        assert todo.dependencies == ["dep1", "dep2"]
        assert todo.priority == 2
    
    def test_todo_status_enum(self):
        assert TodoStatus.PENDING == "pending"
        assert TodoStatus.IN_PROGRESS == "in_progress"
        assert TodoStatus.COMPLETED == "completed"
        assert TodoStatus.FAILED == "failed"


class TestCoTStep:
    def test_cot_step_creation(self):
        step = CoTStep(
            step_id="step-1",
            description="Test step",
            reasoning="This is test reasoning"
        )
        
        assert step.step_id == "step-1"
        assert step.description == "Test step"
        assert step.reasoning == "This is test reasoning"
        assert step.confidence == 0.0
        assert step.input_data == {}
        assert step.output_data == {}


class TestCoTProcess:
    def test_cot_process_creation(self):
        process = CoTProcess(
            process_id="proc-1",
            query="Test query"
        )
        
        assert process.process_id == "proc-1"
        assert process.query == "Test query"
        assert process.steps == []
        assert process.todos == []
        assert process.status == "active"
    
    def test_cot_process_with_steps_and_todos(self):
        step = CoTStep(
            step_id="step-1",
            description="Test step",
            reasoning="Test reasoning"
        )
        
        todo = Todo(
            id="todo-1",
            content="Test todo"
        )
        
        process = CoTProcess(
            process_id="proc-1",
            query="Test query",
            steps=[step],
            todos=[todo]
        )
        
        assert len(process.steps) == 1
        assert len(process.todos) == 1
        assert process.steps[0].step_id == "step-1"
        assert process.todos[0].id == "todo-1"


class TestFeedbackEntry:
    def test_feedback_entry_creation(self):
        feedback = FeedbackEntry(
            feedback_id="fb-1",
            todo_id="todo-1",
            feedback_type="success",
            message="Task completed successfully"
        )
        
        assert feedback.feedback_id == "fb-1"
        assert feedback.todo_id == "todo-1"
        assert feedback.feedback_type == "success"
        assert feedback.message == "Task completed successfully"
        assert feedback.suggestions == []


class TestAgentConfig:
    def test_agent_config_defaults(self):
        config = AgentConfig()
        
        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.max_iterations == 10
        assert config.thinking_depth == 3
    
    def test_agent_config_custom(self):
        config = AgentConfig(
            model_name="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )
        
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
import pytest
from cot_agent_system.todo_manager import TodoManager
from cot_agent_system.models import TodoStatus


class TestTodoManager:
    def setup_method(self):
        self.manager = TodoManager()
    
    def test_create_todo(self):
        todo = self.manager.create_todo("Test todo content")
        
        assert todo.content == "Test todo content"
        assert todo.status == TodoStatus.PENDING
        assert todo.priority == 1
        assert todo.id in self.manager.todos
    
    def test_create_todo_with_options(self):
        todo = self.manager.create_todo(
            content="Complex todo",
            priority=3,
            dependencies=["dep1"],
            metadata={"key": "value"},
            reasoning="Test reasoning"
        )
        
        assert todo.content == "Complex todo"
        assert todo.priority == 3
        assert todo.dependencies == ["dep1"]
        assert todo.metadata == {"key": "value"}
        assert todo.reasoning == "Test reasoning"
    
    def test_get_todo(self):
        todo = self.manager.create_todo("Test todo")
        retrieved = self.manager.get_todo(todo.id)
        
        assert retrieved is not None
        assert retrieved.id == todo.id
        assert retrieved.content == "Test todo"
    
    def test_get_nonexistent_todo(self):
        result = self.manager.get_todo("nonexistent-id")
        assert result is None
    
    def test_update_todo_status(self):
        todo = self.manager.create_todo("Test todo")
        
        success = self.manager.update_todo_status(todo.id, TodoStatus.IN_PROGRESS)
        assert success is True
        
        updated_todo = self.manager.get_todo(todo.id)
        assert updated_todo.status == TodoStatus.IN_PROGRESS
        assert updated_todo.updated_at is not None
    
    def test_update_todo_status_to_completed(self):
        todo = self.manager.create_todo("Test todo")
        
        success = self.manager.update_todo_status(todo.id, TodoStatus.COMPLETED)
        assert success is True
        
        updated_todo = self.manager.get_todo(todo.id)
        assert updated_todo.status == TodoStatus.COMPLETED
        assert updated_todo.completed_at is not None
    
    def test_update_nonexistent_todo_status(self):
        result = self.manager.update_todo_status("nonexistent-id", TodoStatus.COMPLETED)
        assert result is False
    
    def test_add_feedback(self):
        todo = self.manager.create_todo("Test todo")
        
        success = self.manager.add_feedback(todo.id, "Great job!")
        assert success is True
        
        updated_todo = self.manager.get_todo(todo.id)
        assert updated_todo.feedback == "Great job!"
        assert updated_todo.updated_at is not None
    
    def test_get_todos_by_status(self):
        # Create todos with different statuses
        todo1 = self.manager.create_todo("Pending todo 1")
        todo2 = self.manager.create_todo("Pending todo 2")
        todo3 = self.manager.create_todo("In progress todo")
        
        self.manager.update_todo_status(todo3.id, TodoStatus.IN_PROGRESS)
        
        pending_todos = self.manager.get_pending_todos()
        in_progress_todos = self.manager.get_in_progress_todos()
        
        assert len(pending_todos) == 2
        assert len(in_progress_todos) == 1
        assert todo1 in pending_todos
        assert todo2 in pending_todos
        assert todo3 in in_progress_todos
    
    def test_get_ready_todos_no_dependencies(self):
        todo1 = self.manager.create_todo("Todo 1", priority=2)
        todo2 = self.manager.create_todo("Todo 2", priority=1)
        
        ready_todos = self.manager.get_ready_todos()
        
        assert len(ready_todos) == 2
        # Should be sorted by priority (1 = highest priority)
        assert ready_todos[0].priority == 1
        assert ready_todos[1].priority == 2
    
    def test_get_ready_todos_with_dependencies(self):
        todo1 = self.manager.create_todo("Independent todo")
        todo2 = self.manager.create_todo("Dependent todo", dependencies=[todo1.id])
        
        ready_todos = self.manager.get_ready_todos()
        
        # Only todo1 should be ready (todo2 depends on todo1)
        assert len(ready_todos) == 1
        assert ready_todos[0].id == todo1.id
        
        # Complete todo1
        self.manager.update_todo_status(todo1.id, TodoStatus.COMPLETED)
        
        # Now todo2 should be ready
        ready_todos = self.manager.get_ready_todos()
        assert len(ready_todos) == 1
        assert ready_todos[0].id == todo2.id
    
    def test_get_next_todo(self):
        todo1 = self.manager.create_todo("Todo 1", priority=2)
        todo2 = self.manager.create_todo("Todo 2", priority=1)
        
        next_todo = self.manager.get_next_todo()
        
        assert next_todo is not None
        assert next_todo.priority == 1  # Highest priority
    
    def test_get_next_todo_empty(self):
        next_todo = self.manager.get_next_todo()
        assert next_todo is None
    
    def test_create_feedback_entry(self):
        todo = self.manager.create_todo("Test todo")
        
        feedback_entry = self.manager.create_feedback_entry(
            todo_id=todo.id,
            feedback_type="success",
            message="Task completed well",
            suggestions=["Keep it up"]
        )
        
        assert feedback_entry.todo_id == todo.id
        assert feedback_entry.feedback_type == "success"
        assert feedback_entry.message == "Task completed well"
        assert feedback_entry.suggestions == ["Keep it up"]
        assert feedback_entry.feedback_id in self.manager.feedback_entries
    
    def test_get_feedback_for_todo(self):
        todo = self.manager.create_todo("Test todo")
        
        feedback1 = self.manager.create_feedback_entry(
            todo_id=todo.id,
            feedback_type="success",
            message="Good job"
        )
        
        feedback2 = self.manager.create_feedback_entry(
            todo_id=todo.id,
            feedback_type="improvement",
            message="Could be better"
        )
        
        # Create feedback for different todo
        other_todo = self.manager.create_todo("Other todo")
        self.manager.create_feedback_entry(
            todo_id=other_todo.id,
            feedback_type="error",
            message="Failed"
        )
        
        feedback_entries = self.manager.get_feedback_for_todo(todo.id)
        
        assert len(feedback_entries) == 2
        assert feedback1 in feedback_entries
        assert feedback2 in feedback_entries
    
    def test_get_statistics(self):
        # Create todos with different statuses
        todo1 = self.manager.create_todo("Pending todo")
        todo2 = self.manager.create_todo("In progress todo")
        todo3 = self.manager.create_todo("Completed todo")
        todo4 = self.manager.create_todo("Failed todo")
        
        self.manager.update_todo_status(todo2.id, TodoStatus.IN_PROGRESS)
        self.manager.update_todo_status(todo3.id, TodoStatus.COMPLETED)
        self.manager.update_todo_status(todo4.id, TodoStatus.FAILED)
        
        stats = self.manager.get_statistics()
        
        assert stats["total"] == 4
        assert stats["pending"] == 1
        assert stats["in_progress"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
    
    def test_clear_all(self):
        # Create some todos and feedback
        todo = self.manager.create_todo("Test todo")
        self.manager.create_feedback_entry(
            todo_id=todo.id,
            feedback_type="test",
            message="Test message"
        )
        
        assert len(self.manager.todos) == 1
        assert len(self.manager.feedback_entries) == 1
        
        self.manager.clear_all()
        
        assert len(self.manager.todos) == 0
        assert len(self.manager.feedback_entries) == 0
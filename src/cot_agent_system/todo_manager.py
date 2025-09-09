import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Todo, TodoStatus, FeedbackEntry


class TodoManager:
    def __init__(self):
        self.todos: Dict[str, Todo] = {}
        self.feedback_entries: Dict[str, FeedbackEntry] = {}
    
    def create_todo(
        self, 
        content: str, 
        priority: int = 1, 
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None
    ) -> Todo:
        todo_id = str(uuid.uuid4())
        todo = Todo(
            id=todo_id,
            content=content,
            priority=priority,
            dependencies=dependencies or [],
            metadata=metadata or {},
            reasoning=reasoning
        )
        self.todos[todo_id] = todo
        return todo
    
    def get_todo(self, todo_id: str) -> Optional[Todo]:
        return self.todos.get(todo_id)
    
    def update_todo_status(self, todo_id: str, status: TodoStatus) -> bool:
        if todo_id not in self.todos:
            return False
        
        todo = self.todos[todo_id]
        todo.status = status
        todo.updated_at = datetime.now()
        
        if status == TodoStatus.COMPLETED:
            todo.completed_at = datetime.now()
        
        return True
    
    def add_feedback(self, todo_id: str, feedback: str) -> bool:
        if todo_id not in self.todos:
            return False
        
        self.todos[todo_id].feedback = feedback
        self.todos[todo_id].updated_at = datetime.now()
        return True
    
    def get_pending_todos(self) -> List[Todo]:
        return [todo for todo in self.todos.values() if todo.status == TodoStatus.PENDING]
    
    def get_in_progress_todos(self) -> List[Todo]:
        return [todo for todo in self.todos.values() if todo.status == TodoStatus.IN_PROGRESS]
    
    def get_completed_todos(self) -> List[Todo]:
        return [todo for todo in self.todos.values() if todo.status == TodoStatus.COMPLETED]
    
    def get_failed_todos(self) -> List[Todo]:
        return [todo for todo in self.todos.values() if todo.status == TodoStatus.FAILED]
    
    def get_ready_todos(self) -> List[Todo]:
        """Get todos that are ready to be executed (dependencies satisfied)"""
        ready_todos = []
        completed_todo_ids = {todo.id for todo in self.get_completed_todos()}
        
        for todo in self.get_pending_todos():
            if all(dep_id in completed_todo_ids for dep_id in todo.dependencies):
                ready_todos.append(todo)
        
        return sorted(ready_todos, key=lambda x: x.priority)
    
    def get_next_todo(self) -> Optional[Todo]:
        """Get the next todo to execute based on priority and dependencies"""
        ready_todos = self.get_ready_todos()
        return ready_todos[0] if ready_todos else None
    
    def get_todos_by_status(self, status: TodoStatus) -> List[Todo]:
        return [todo for todo in self.todos.values() if todo.status == status]
    
    def get_all_todos(self) -> List[Todo]:
        return list(self.todos.values())
    
    def create_feedback_entry(
        self,
        todo_id: str,
        feedback_type: str,
        message: str,
        suggestions: Optional[List[str]] = None
    ) -> FeedbackEntry:
        feedback_id = str(uuid.uuid4())
        feedback_entry = FeedbackEntry(
            feedback_id=feedback_id,
            todo_id=todo_id,
            feedback_type=feedback_type,
            message=message,
            suggestions=suggestions or []
        )
        self.feedback_entries[feedback_id] = feedback_entry
        return feedback_entry
    
    def get_feedback_for_todo(self, todo_id: str) -> List[FeedbackEntry]:
        return [
            feedback for feedback in self.feedback_entries.values() 
            if feedback.todo_id == todo_id
        ]
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about todos"""
        stats = {
            "total": len(self.todos),
            "pending": len(self.get_pending_todos()),
            "in_progress": len(self.get_in_progress_todos()),
            "completed": len(self.get_completed_todos()),
            "failed": len(self.get_failed_todos())
        }
        return stats
    
    def clear_all(self):
        """Clear all todos and feedback entries"""
        self.todos.clear()
        self.feedback_entries.clear()
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatOpenAI

from .models import CoTProcess, Todo, TodoStatus, AgentConfig
from .todo_manager import TodoManager
from .cot_engine import CoTEngine


class CoTAgent:
    def __init__(self, config: Optional[AgentConfig] = None, llm: Optional[BaseChatModel] = None):
        self.config = config or AgentConfig()
        self.llm = llm or self._create_default_llm()
        self.cot_engine = CoTEngine(self.llm, self.config)
        self.todo_manager = self.cot_engine.todo_manager
        self.current_process: Optional[CoTProcess] = None
        self.execution_history: List[Dict[str, Any]] = []
    
    def _create_default_llm(self) -> BaseChatModel:
        """Create default LLM instance"""
        return ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main entry point for processing user queries"""
        print(f"\n🔍 Processing query: {query}")
        
        # Create and analyze the query using CoT
        self.current_process = await self.cot_engine.analyze_query(query)
        
        print(f"\n📋 Generated {len(self.current_process.todos)} todos:")
        for i, todo in enumerate(self.current_process.todos, 1):
            print(f"  {i}. {todo.content} (Priority: {todo.priority})")
        
        # Start the execution loop
        result = await self._execute_feedback_loop()
        
        return {
            "process": self.current_process,
            "result": result,
            "execution_history": self.execution_history
        }
    
    async def _execute_feedback_loop(self) -> Dict[str, Any]:
        """Execute the main feedback loop"""
        iteration = 0
        max_iterations = self.config.max_iterations
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Iteration {iteration}")
            
            # Get the next todo to execute
            next_todo = self.todo_manager.get_next_todo()
            if not next_todo:
                # Check if we have any in-progress todos
                in_progress = self.todo_manager.get_in_progress_todos()
                if not in_progress:
                    print("✅ All todos completed!")
                    break
                else:
                    print("⏳ Waiting for in-progress todos...")
                    # In a real implementation, you might wait or check status
                    break
            
            print(f"📝 Executing: {next_todo.content}")
            
            # Mark as in progress
            self.todo_manager.update_todo_status(next_todo.id, TodoStatus.IN_PROGRESS)
            
            # Simulate todo execution (in real implementation, this would be actual execution)
            execution_result = await self._execute_todo(next_todo)
            
            # Record execution
            self.execution_history.append({
                "iteration": iteration,
                "todo_id": next_todo.id,
                "todo_content": next_todo.content,
                "result": execution_result,
                "timestamp": datetime.now()
            })
            
            # Process the execution result
            if execution_result["success"]:
                self.todo_manager.update_todo_status(next_todo.id, TodoStatus.COMPLETED)
                print(f"✅ Completed: {next_todo.content}")
            else:
                self.todo_manager.update_todo_status(next_todo.id, TodoStatus.FAILED)
                print(f"❌ Failed: {next_todo.content}")
                
                # Process feedback and potentially create new todos
                await self._handle_failure_feedback(next_todo, execution_result)
        
        # Generate final result
        stats = self.todo_manager.get_statistics()
        return {
            "iterations": iteration,
            "final_stats": stats,
            "completed": stats["completed"] == stats["total"] - stats["failed"],
            "process_status": self.cot_engine.get_process_status(self.current_process)
        }
    
    async def _execute_todo(self, todo: Todo) -> Dict[str, Any]:
        """Simulate todo execution - in real implementation, this would do actual work"""
        # This is a simulation - in a real system, you would:
        # 1. Parse the todo content to understand what action to take
        # 2. Execute the actual action (API calls, file operations, etc.)
        # 3. Return the real result
        
        print(f"  🔧 Simulating execution of: {todo.content}")
        
        # Simulate some processing time
        await asyncio.sleep(0.5)
        
        # Simulate different outcomes based on todo content
        if "error" in todo.content.lower() or "fail" in todo.content.lower():
            return {
                "success": False,
                "error": "Simulated failure for testing",
                "feedback": "This todo failed during execution. Consider breaking it down into smaller steps."
            }
        else:
            return {
                "success": True,
                "output": f"Successfully completed: {todo.content}",
                "feedback": "Todo completed successfully."
            }
    
    async def _handle_failure_feedback(self, todo: Todo, execution_result: Dict[str, Any]):
        """Handle feedback from failed todo execution"""
        feedback = execution_result.get("feedback", "Todo execution failed")
        
        print(f"  🔄 Processing failure feedback...")
        
        # Add feedback to the todo
        self.todo_manager.add_feedback(todo.id, feedback)
        
        # Use CoT engine to analyze the failure and suggest improvements
        feedback_analysis = await self.cot_engine.process_feedback(
            todo_id=todo.id,
            feedback=feedback,
            todo_status="failed"
        )
        
        print(f"  💡 Feedback analysis: {len(feedback_analysis.get('suggestions', []))} suggestions")
        
        # Create new todos based on suggestions
        new_todos = await self.cot_engine.update_todos_based_on_feedback(
            feedback_analysis["feedback_entry"].feedback_id
        )
        
        if new_todos:
            print(f"  ➕ Created {len(new_todos)} new todos from feedback")
            for new_todo in new_todos:
                print(f"    - {new_todo.content}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        if not self.current_process:
            return {"status": "idle", "message": "No active process"}
        
        return self.cot_engine.get_process_status(self.current_process)
    
    def get_todos_summary(self) -> Dict[str, Any]:
        """Get a summary of all todos"""
        stats = self.todo_manager.get_statistics()
        
        return {
            "statistics": stats,
            "pending_todos": [
                {"id": t.id, "content": t.content, "priority": t.priority}
                for t in self.todo_manager.get_pending_todos()
            ],
            "in_progress_todos": [
                {"id": t.id, "content": t.content}
                for t in self.todo_manager.get_in_progress_todos()
            ],
            "completed_todos": [
                {"id": t.id, "content": t.content, "completed_at": t.completed_at}
                for t in self.todo_manager.get_completed_todos()
            ],
            "failed_todos": [
                {"id": t.id, "content": t.content, "feedback": t.feedback}
                for t in self.todo_manager.get_failed_todos()
            ]
        }
    
    async def add_manual_feedback(self, todo_id: str, feedback: str) -> Dict[str, Any]:
        """Allow manual feedback input for a todo"""
        todo = self.todo_manager.get_todo(todo_id)
        if not todo:
            return {"error": "Todo not found"}
        
        # Process the manual feedback
        feedback_analysis = await self.cot_engine.process_feedback(
            todo_id=todo_id,
            feedback=feedback,
            todo_status=todo.status.value
        )
        
        # Update the todo with feedback
        self.todo_manager.add_feedback(todo_id, feedback)
        
        return feedback_analysis
    
    def reset(self):
        """Reset the agent state"""
        self.current_process = None
        self.execution_history.clear()
        self.todo_manager.clear_all()
        print("🔄 Agent state reset")
    
    async def continue_process(self) -> Dict[str, Any]:
        """Continue the current process if it was interrupted"""
        if not self.current_process:
            return {"error": "No active process to continue"}
        
        return await self._execute_feedback_loop()
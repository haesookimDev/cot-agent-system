import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatOpenAI

from .models import CoTProcess, Todo, TodoStatus, AgentConfig
from .todo_manager import TodoManager
from .cot_engine import CoTEngine
from .todo_executor import TodoExecutor
from .interactive_feedback import InteractiveFeedbackManager, FeedbackType


class CoTAgent:
    def __init__(self, config: Optional[AgentConfig] = None, llm: Optional[BaseChatModel] = None, interactive: bool = False):
        self.config = config or AgentConfig()
        self.llm = llm or self._create_default_llm()
        self.cot_engine = CoTEngine(self.llm, self.config)
        self.todo_manager = self.cot_engine.todo_manager
        self.todo_executor = TodoExecutor()
        self.feedback_manager = InteractiveFeedbackManager()
        self.feedback_manager.set_interactive_mode(interactive)
        self.current_process: Optional[CoTProcess] = None
        self.execution_history: List[Dict[str, Any]] = []
    
    def _create_default_llm(self) -> BaseChatModel:
        """Create default LLM instance"""
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=self.config.api_key
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize LLM: {e}")
            print("    Using mock LLM for demonstration...")
            return MockLLM()
    
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
        """Execute the main feedback loop with interactive feedback support"""
        iteration = 0
        max_iterations = self.config.max_iterations
        
        # Request initial plan approval if interactive
        if self.feedback_manager.interactive_mode and self.current_process:
            todos = self.current_process.todos
            guidance = await self.feedback_manager.request_plan_guidance(todos, 0)
            
            if not guidance["continue_execution"]:
                if guidance["modify_plan"]:
                    await self._handle_plan_modification(guidance["action"])
                else:
                    print("⏸️  Execution paused by user")
                    return {"iterations": 0, "final_stats": self.todo_manager.get_statistics(), "user_paused": True}
        
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
                    break
            
            print(f"📝 Next todo: {next_todo.content}")
            
            # Request approval before execution if interactive
            execution_context = {
                "iteration": iteration,
                "execution_type": "standard",
                "estimated_impact": "low"
            }
            
            if self.feedback_manager.interactive_mode:
                should_proceed = await self.feedback_manager.request_todo_approval(
                    next_todo, execution_context
                )
                
                if not should_proceed:
                    print("⏭️  Skipping todo per user request")
                    self.todo_manager.update_todo_status(next_todo.id, TodoStatus.FAILED)
                    # Add feedback about skipping
                    self.todo_manager.add_feedback(next_todo.id, "Skipped by user request")
                    continue
            
            # Mark as in progress
            self.todo_manager.update_todo_status(next_todo.id, TodoStatus.IN_PROGRESS)
            
            # Execute the todo
            execution_result = await self._execute_todo(next_todo)
            
            # Request result validation if interactive
            if self.feedback_manager.interactive_mode:
                validation_result = await self.feedback_manager.request_result_validation(
                    next_todo, execution_result
                )
                
                if validation_result["requires_retry"]:
                    print("🔄 Retrying todo per user request")
                    self.todo_manager.update_todo_status(next_todo.id, TodoStatus.PENDING)
                    continue
                elif validation_result["requires_modification"]:
                    print("✏️  Todo requires modification")
                    await self._handle_todo_modification(next_todo, execution_result)
                    continue
                elif not validation_result["user_satisfied"]:
                    print("❌ User not satisfied with result")
                    execution_result["success"] = False
                    execution_result["feedback"] = "User rejected the result"
            
            # Record execution
            self.execution_history.append({
                "iteration": iteration,
                "todo_id": next_todo.id,
                "todo_content": next_todo.content,
                "result": execution_result,
                "timestamp": datetime.now(),
                "user_validation": validation_result if self.feedback_manager.interactive_mode else None
            })
            
            # Process the execution result
            if execution_result["success"]:
                self.todo_manager.update_todo_status(next_todo.id, TodoStatus.COMPLETED)
                print(f"✅ Completed: {next_todo.content}")
            else:
                self.todo_manager.update_todo_status(next_todo.id, TodoStatus.FAILED)
                print(f"❌ Failed: {next_todo.content}")
                
                # Handle failure with interactive feedback
                await self._handle_failure_feedback_interactive(next_todo, execution_result)
            
            # Request guidance for next steps if interactive and not final iteration
            if (self.feedback_manager.interactive_mode and 
                iteration < max_iterations and 
                iteration % 3 == 0):  # Every 3 iterations
                
                remaining_todos = self.todo_manager.get_pending_todos()
                if remaining_todos:
                    current_index = len(self.current_process.todos) - len(remaining_todos)
                    guidance = await self.feedback_manager.request_plan_guidance(
                        self.current_process.todos, current_index
                    )
                    
                    if not guidance["continue_execution"]:
                        if guidance["modify_plan"]:
                            await self._handle_plan_modification(guidance["action"])
                        else:
                            print("⏸️  Execution paused by user")
                            break
        
        # Generate final result
        stats = self.todo_manager.get_statistics()
        return {
            "iterations": iteration,
            "final_stats": stats,
            "completed": stats["completed"] == stats["total"] - stats["failed"],
            "process_status": self.cot_engine.get_process_status(self.current_process),
            "feedback_summary": self.feedback_manager.get_feedback_summary()
        }
    
    async def _execute_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute todo using the TodoExecutor"""
        print(f"  🔧 Executing: {todo.content}")
        
        try:
            # Use the TodoExecutor to actually execute the todo
            result = await self.todo_executor.execute_todo(todo)
            
            # Display execution result
            if result["success"]:
                print(f"    ✅ Success: {result.get('feedback', 'Completed')}")
                if result.get("output"):
                    # Show output (truncated if too long)
                    output = result["output"]
                    if len(output) > 200:
                        print(f"    📄 Output: {output[:200]}...")
                    else:
                        print(f"    📄 Output: {output}")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            print(f"    💥 Exception during execution: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "feedback": f"Exception occurred during execution: {str(e)}"
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
        """Get a comprehensive summary of all todos and execution"""
        stats = self.todo_manager.get_statistics()
        execution_summary = self.todo_executor.get_execution_summary()
        
        return {
            "statistics": stats,
            "execution_summary": execution_summary,
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
            ],
            "all_todos": [
                {"id": t.id, "content": t.content, "status": t.status, "priority": t.priority}
                for t in self.todo_manager.get_all_todos()
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
    
    async def _handle_failure_feedback_interactive(self, todo: Todo, execution_result: Dict[str, Any]):
        """Handle failure feedback with interactive support"""
        error = execution_result.get("error", "Unknown error")
        
        if self.feedback_manager.interactive_mode:
            # Generate suggestions for error handling
            suggestions = self._generate_error_suggestions(todo, error)
            
            # Request user guidance on error handling
            error_guidance = await self.feedback_manager.request_error_handling(
                todo, error, suggestions
            )
            
            if error_guidance["retry"]:
                print("🔄 Retrying todo due to user request")
                self.todo_manager.update_todo_status(todo.id, TodoStatus.PENDING)
            elif error_guidance["break_down"]:
                await self._break_down_todo(todo)
            elif error_guidance["modify"]:
                await self._modify_todo_interactive(todo)
            elif error_guidance["use_suggestion"]:
                suggestion_index = int(error_guidance["action"].split("_")[1]) - 1
                await self._apply_suggestion(todo, suggestions[suggestion_index])
            # Skip is handled by leaving todo as failed
        else:
            # Non-interactive mode - use original feedback handling
            await self._handle_failure_feedback(todo, execution_result)
    
    async def _handle_todo_modification(self, todo: Todo, execution_result: Dict[str, Any]):
        """Handle todo modification requests"""
        if self.feedback_manager.interactive_mode:
            await self._modify_todo_interactive(todo)
        else:
            print(f"Todo modification requested but not in interactive mode: {todo.content}")
    
    async def _modify_todo_interactive(self, todo: Todo):
        """Interactively modify a todo"""
        new_content = await self.feedback_manager.request_custom_input(
            f"Current todo: '{todo.content}'\nEnter new content (or press Enter to keep current):",
            {"current_todo": todo.dict()},
            validation_fn=lambda x: len(x.strip()) > 0 or x.strip() == ""
        )
        
        if new_content.strip():
            old_content = todo.content
            todo.content = new_content
            print(f"✏️  Modified todo: '{old_content}' → '{new_content}'")
            # Reset status to pending for re-execution
            self.todo_manager.update_todo_status(todo.id, TodoStatus.PENDING)
    
    async def _handle_plan_modification(self, action: str):
        """Handle plan modification requests"""
        if action == "add_todo":
            await self._add_todo_interactive()
        elif action == "remove_todo":
            await self._remove_todo_interactive()
        elif action == "reorder":
            await self._reorder_todos_interactive()
        else:
            print(f"Plan modification '{action}' not implemented yet")
    
    async def _add_todo_interactive(self):
        """Interactively add a new todo"""
        new_todo_content = await self.feedback_manager.request_custom_input(
            "Enter new todo content:",
            validation_fn=lambda x: len(x.strip()) > 3
        )
        
        priority_str = await self.feedback_manager.request_custom_input(
            "Enter priority (1-5, default 3):",
            validation_fn=lambda x: x.isdigit() and 1 <= int(x) <= 5 or x.strip() == ""
        )
        
        priority = int(priority_str) if priority_str.strip() else 3
        
        new_todo = self.todo_manager.create_todo(
            content=new_todo_content,
            priority=priority,
            reasoning="Added by user request"
        )
        
        # Add to current process
        if self.current_process:
            self.current_process.todos.append(new_todo)
        
        print(f"➕ Added new todo: '{new_todo_content}' (Priority: {priority})")
    
    async def _remove_todo_interactive(self):
        """Interactively remove a todo"""
        pending_todos = self.todo_manager.get_pending_todos()
        
        if not pending_todos:
            print("No pending todos to remove")
            return
        
        print("\nPending todos:")
        for i, todo in enumerate(pending_todos):
            print(f"{i+1}. {todo.content}")
        
        selection = await self.feedback_manager.request_custom_input(
            f"Select todo to remove (1-{len(pending_todos)}):",
            validation_fn=lambda x: x.isdigit() and 1 <= int(x) <= len(pending_todos)
        )
        
        todo_to_remove = pending_todos[int(selection) - 1]
        self.todo_manager.todos.pop(todo_to_remove.id, None)
        
        # Remove from current process
        if self.current_process:
            self.current_process.todos = [
                t for t in self.current_process.todos if t.id != todo_to_remove.id
            ]
        
        print(f"➖ Removed todo: '{todo_to_remove.content}'")
    
    async def _reorder_todos_interactive(self):
        """Interactively reorder todos"""
        pending_todos = self.todo_manager.get_pending_todos()
        
        if len(pending_todos) < 2:
            print("Need at least 2 pending todos to reorder")
            return
        
        print("\nCurrent todo order:")
        for i, todo in enumerate(pending_todos):
            print(f"{i+1}. {todo.content}")
        
        new_order = await self.feedback_manager.request_custom_input(
            f"Enter new order (e.g., '2,1,3' for {len(pending_todos)} todos):",
            validation_fn=lambda x: self._validate_reorder_input(x, len(pending_todos))
        )
        
        order_indices = [int(x.strip()) - 1 for x in new_order.split(',')]
        reordered_todos = [pending_todos[i] for i in order_indices]
        
        # Update priorities based on new order
        for i, todo in enumerate(reordered_todos):
            todo.priority = i + 1
        
        print("✅ Todos reordered successfully")
    
    def _validate_reorder_input(self, input_str: str, expected_count: int) -> bool:
        """Validate reorder input string"""
        try:
            parts = [x.strip() for x in input_str.split(',')]
            if len(parts) != expected_count:
                return False
            
            indices = [int(x) for x in parts]
            return set(indices) == set(range(1, expected_count + 1))
        except:
            return False
    
    async def _break_down_todo(self, todo: Todo):
        """Break down a complex todo into smaller ones"""
        breakdown_prompt = f"The todo '{todo.content}' failed. How should we break it down into smaller tasks?"
        
        breakdown_input = await self.feedback_manager.request_custom_input(
            breakdown_prompt + "\nEnter subtasks (one per line, or press Enter twice to finish):"
        )
        
        # Parse subtasks (simple implementation)
        subtasks = [line.strip() for line in breakdown_input.split('\n') if line.strip()]
        
        if subtasks:
            print(f"🔧 Breaking down '{todo.content}' into {len(subtasks)} subtasks:")
            
            for i, subtask_content in enumerate(subtasks):
                subtodo = self.todo_manager.create_todo(
                    content=subtask_content,
                    priority=todo.priority,
                    reasoning=f"Breakdown of failed todo: {todo.content}"
                )
                
                # Add to current process
                if self.current_process:
                    self.current_process.todos.append(subtodo)
                
                print(f"  {i+1}. {subtask_content}")
    
    def _generate_error_suggestions(self, todo: Todo, error: str) -> List[str]:
        """Generate suggestions for handling execution errors"""
        suggestions = []
        
        error_lower = error.lower()
        content_lower = todo.content.lower()
        
        # Math-related errors
        if any(word in content_lower for word in ['calculate', 'compute', 'math']) or any(op in todo.content for op in ['+', '-', '*', '/']):
            if 'expression' in error_lower:
                suggestions.append("Break down the mathematical expression into simpler parts")
            if 'syntax' in error_lower or 'invalid' in error_lower:
                suggestions.append("Rewrite the mathematical expression with clearer syntax")
            suggestions.append("Verify the mathematical notation and operators")
        
        # Research-related errors
        elif any(word in content_lower for word in ['research', 'find', 'search']):
            suggestions.append("Try a more specific search query")
            suggestions.append("Break down the research into smaller topics")
            suggestions.append("Consider alternative information sources")
        
        # Planning-related errors
        elif any(word in content_lower for word in ['plan', 'organize', 'schedule']):
            suggestions.append("Break down the planning task into specific components")
            suggestions.append("Start with a simpler, more focused plan")
            suggestions.append("Gather more information before planning")
        
        # Generic suggestions
        suggestions.extend([
            "Simplify the task description",
            "Add more context or details to the task",
            "Skip this task for now and return to it later"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    async def _apply_suggestion(self, todo: Todo, suggestion: str):
        """Apply a specific suggestion to handle a failed todo"""
        print(f"📝 Applying suggestion: {suggestion}")
        
        if "break down" in suggestion.lower():
            await self._break_down_todo(todo)
        elif "rewrite" in suggestion.lower() or "simplify" in suggestion.lower():
            await self._modify_todo_interactive(todo)
        elif "skip" in suggestion.lower():
            print(f"⏭️  Skipping todo: {todo.content}")
            self.todo_manager.add_feedback(todo.id, f"Skipped due to suggestion: {suggestion}")
        else:
            # Generic suggestion application
            self.todo_manager.add_feedback(todo.id, f"Suggestion applied: {suggestion}")
            # Reset to pending for retry
            self.todo_manager.update_todo_status(todo.id, TodoStatus.PENDING)
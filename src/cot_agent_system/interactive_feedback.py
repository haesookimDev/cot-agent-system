"""
Interactive Feedback Manager - Handles user feedback during todo execution.

This module provides functionality to request user feedback during the execution
process, allowing for dynamic adjustment and user guidance.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from datetime import datetime

from .models import Todo, TodoStatus


class FeedbackType(str, Enum):
    """Types of feedback that can be requested"""
    APPROVAL = "approval"           # Yes/No approval for proceeding
    GUIDANCE = "guidance"           # Request for direction or clarification
    VALIDATION = "validation"       # Validate results or approach
    CHOICE = "choice"              # Choose from multiple options
    INPUT = "input"                # Provide additional information
    REVIEW = "review"              # Review and potentially modify results


class FeedbackRequest:
    """Represents a request for user feedback"""
    
    def __init__(
        self,
        request_id: str,
        feedback_type: FeedbackType,
        message: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
        default_response: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.request_id = request_id
        self.feedback_type = feedback_type
        self.message = message
        self.context = context
        self.options = options or []
        self.default_response = default_response
        self.timeout = timeout
        self.created_at = datetime.now()
        self.response: Optional[str] = None
        self.responded_at: Optional[datetime] = None


class InteractiveFeedbackManager:
    """Manages interactive feedback requests during todo execution"""
    
    def __init__(self, feedback_handler: Optional[Callable] = None):
        self.feedback_handler = feedback_handler or self._default_feedback_handler
        self.feedback_history: List[FeedbackRequest] = []
        self.interactive_mode = True
        self.auto_approve_simple = False
    
    async def request_feedback(
        self,
        feedback_type: FeedbackType,
        message: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
        default_response: Optional[str] = None,
        timeout: Optional[int] = 30
    ) -> str:
        """Request feedback from the user"""
        
        request_id = f"feedback_{len(self.feedback_history)}"
        
        request = FeedbackRequest(
            request_id=request_id,
            feedback_type=feedback_type,
            message=message,
            context=context,
            options=options,
            default_response=default_response,
            timeout=timeout
        )
        
        self.feedback_history.append(request)
        
        if not self.interactive_mode:
            # Non-interactive mode - use defaults or auto-approve
            response = self._handle_non_interactive(request)
        else:
            # Interactive mode - ask user
            response = await self.feedback_handler(request)
        
        request.response = response
        request.responded_at = datetime.now()
        
        return response
    
    async def request_todo_approval(self, todo: Todo, execution_context: Dict[str, Any]) -> bool:
        """Request approval before executing a todo"""
        
        message = f"About to execute todo: '{todo.content}'"
        if execution_context.get("execution_type"):
            message += f"\nExecution type: {execution_context['execution_type']}"
        if execution_context.get("estimated_impact"):
            message += f"\nEstimated impact: {execution_context['estimated_impact']}"
        
        message += "\nProceed with execution?"
        
        response = await self.request_feedback(
            feedback_type=FeedbackType.APPROVAL,
            message=message,
            context={"todo": todo.dict(), "execution_context": execution_context},
            options=["yes", "no", "skip", "modify"],
            default_response="yes",
            timeout=30
        )
        
        return response.lower() in ["yes", "y", "proceed", "ok"]
    
    async def request_result_validation(
        self, 
        todo: Todo, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request validation of execution results"""
        
        message = f"Todo '{todo.content}' executed with result:"
        if result.get("output"):
            output = result["output"]
            if len(output) > 200:
                message += f"\n{output[:200]}..."
            else:
                message += f"\n{output}"
        
        message += f"\nSuccess: {result.get('success', 'Unknown')}"
        message += "\n\nIs this result acceptable?"
        
        response = await self.request_feedback(
            feedback_type=FeedbackType.VALIDATION,
            message=message,
            context={"todo": todo.dict(), "result": result},
            options=["accept", "retry", "modify", "skip"],
            default_response="accept"
        )
        
        return {
            "validation_result": response.lower(),
            "user_satisfied": response.lower() in ["accept", "good", "yes", "ok"],
            "requires_retry": response.lower() in ["retry", "redo"],
            "requires_modification": response.lower() in ["modify", "change"]
        }
    
    async def request_plan_guidance(
        self, 
        todos: List[Todo], 
        current_index: int
    ) -> Dict[str, Any]:
        """Request guidance on execution plan"""
        
        message = "Current execution plan:\n"
        for i, todo in enumerate(todos):
            status_icon = "🔄" if i == current_index else ("✅" if i < current_index else "⏳")
            message += f"{i+1}. {status_icon} {todo.content}\n"
        
        message += f"\nCurrently at step {current_index + 1}. How would you like to proceed?"
        
        response = await self.request_feedback(
            feedback_type=FeedbackType.GUIDANCE,
            message=message,
            context={
                "todos": [t.dict() for t in todos],
                "current_index": current_index
            },
            options=["continue", "skip_current", "reorder", "add_todo", "remove_todo", "pause"],
            default_response="continue"
        )
        
        return {
            "action": response.lower(),
            "continue_execution": response.lower() in ["continue", "proceed", "next"],
            "skip_current": response.lower() in ["skip_current", "skip"],
            "modify_plan": response.lower() in ["reorder", "add_todo", "remove_todo", "modify"]
        }
    
    async def request_error_handling(
        self, 
        todo: Todo, 
        error: str, 
        suggestions: List[str]
    ) -> Dict[str, Any]:
        """Request guidance on handling execution errors"""
        
        message = f"Error executing todo: '{todo.content}'\n"
        message += f"Error: {error}\n\n"
        
        if suggestions:
            message += "Suggested actions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                message += f"{i}. {suggestion}\n"
        
        message += "\nHow would you like to handle this error?"
        
        options = ["retry", "skip", "modify_todo", "break_down"]
        if suggestions:
            options.extend([f"suggestion_{i}" for i in range(1, len(suggestions) + 1)])
        
        response = await self.request_feedback(
            feedback_type=FeedbackType.CHOICE,
            message=message,
            context={
                "todo": todo.dict(),
                "error": error,
                "suggestions": suggestions
            },
            options=options,
            default_response="retry"
        )
        
        return {
            "action": response.lower(),
            "retry": response.lower() in ["retry", "try_again"],
            "skip": response.lower() in ["skip", "ignore"],
            "modify": response.lower() in ["modify_todo", "modify"],
            "break_down": response.lower() in ["break_down", "split"],
            "use_suggestion": response.lower().startswith("suggestion_")
        }
    
    async def request_custom_input(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        validation_fn: Optional[Callable[[str], bool]] = None
    ) -> str:
        """Request custom input from the user"""
        
        response = await self.request_feedback(
            feedback_type=FeedbackType.INPUT,
            message=prompt,
            context=context or {},
            timeout=60
        )
        
        # Validate response if validation function provided
        if validation_fn and not validation_fn(response):
            return await self.request_custom_input(
                f"Invalid input. {prompt}",
                context,
                validation_fn
            )
        
        return response
    
    def _handle_non_interactive(self, request: FeedbackRequest) -> str:
        """Handle feedback requests in non-interactive mode"""
        
        if request.default_response:
            return request.default_response
        
        # Auto-approve simple operations if enabled
        if self.auto_approve_simple and request.feedback_type == FeedbackType.APPROVAL:
            return "yes"
        
        # Default responses by type
        defaults = {
            FeedbackType.APPROVAL: "no",
            FeedbackType.VALIDATION: "accept",
            FeedbackType.GUIDANCE: "continue",
            FeedbackType.CHOICE: request.options[0] if request.options else "skip",
            FeedbackType.INPUT: "",
            FeedbackType.REVIEW: "accept"
        }
        
        return defaults.get(request.feedback_type, "skip")
    
    async def _default_feedback_handler(self, request: FeedbackRequest) -> str:
        """Default feedback handler - prints to console and waits for input"""
        
        print(f"\n🤖 {request.feedback_type.value.upper()} REQUESTED")
        print("=" * 50)
        print(request.message)
        
        if request.options:
            print(f"\nOptions: {', '.join(request.options)}")
        
        if request.default_response:
            print(f"Default: {request.default_response}")
        
        print(f"Timeout: {request.timeout}s" if request.timeout else "No timeout")
        print("-" * 50)
        
        try:
            if request.timeout:
                # Implement timeout logic
                response = await asyncio.wait_for(
                    self._get_user_input("Your response: "),
                    timeout=request.timeout
                )
            else:
                response = await self._get_user_input("Your response: ")
            
            # Use default if empty response and default available
            if not response.strip() and request.default_response:
                response = request.default_response
                print(f"Using default: {response}")
            
            return response.strip()
            
        except asyncio.TimeoutError:
            print(f"\nTimeout reached. Using default: {request.default_response}")
            return request.default_response or "skip"
    
    async def _get_user_input(self, prompt: str) -> str:
        """Get user input asynchronously"""
        # This is a simple implementation - in a real async environment,
        # you might want to use proper async input handling
        return await asyncio.to_thread(input, prompt)
    
    def set_interactive_mode(self, enabled: bool):
        """Enable or disable interactive mode"""
        self.interactive_mode = enabled
    
    def set_auto_approve_simple(self, enabled: bool):
        """Enable or disable auto-approval of simple operations"""
        self.auto_approve_simple = enabled
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get a summary of all feedback requests"""
        
        if not self.feedback_history:
            return {"message": "No feedback requests made"}
        
        total_requests = len(self.feedback_history)
        by_type = {}
        response_times = []
        
        for request in self.feedback_history:
            # Count by type
            type_name = request.feedback_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            # Calculate response times
            if request.responded_at:
                response_time = (request.responded_at - request.created_at).total_seconds()
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_requests": total_requests,
            "by_type": by_type,
            "average_response_time": avg_response_time,
            "interactive_mode": self.interactive_mode,
            "recent_requests": [
                {
                    "type": req.feedback_type.value,
                    "message": req.message[:100] + "..." if len(req.message) > 100 else req.message,
                    "response": req.response,
                    "response_time": (req.responded_at - req.created_at).total_seconds() if req.responded_at else None
                }
                for req in self.feedback_history[-5:]
            ]
        }
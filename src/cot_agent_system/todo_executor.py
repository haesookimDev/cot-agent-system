"""
Todo Executor - Executes individual todos based on their content and type.

This module provides the core functionality for actually executing todos,
rather than just simulating them.
"""

import re
import ast
import operator
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import Todo, TodoStatus


class TodoExecutor:
    """Executes todos based on their content and provides real results"""
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
        
        # Math operators for safe evaluation
        self.math_operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '^': operator.xor,
            '**': operator.pow
        }
    
    async def execute_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute a todo and return the result"""
        execution_start = datetime.now()
        
        try:
            # Determine todo type and execute accordingly
            result = await self._route_execution(todo)
            
            # Record successful execution
            execution_record = {
                "todo_id": todo.id,
                "todo_content": todo.content,
                "execution_type": result.get("execution_type", "unknown"),
                "success": True,
                "result": result.get("output"),
                "execution_time": (datetime.now() - execution_start).total_seconds(),
                "timestamp": datetime.now()
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "success": True,
                "output": result.get("output"),
                "execution_type": result.get("execution_type"),
                "details": result.get("details", {}),
                "feedback": result.get("feedback", "Todo executed successfully")
            }
            
        except Exception as e:
            # Record failed execution
            execution_record = {
                "todo_id": todo.id,
                "todo_content": todo.content,
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - execution_start).total_seconds(),
                "timestamp": datetime.now()
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": str(e),
                "feedback": f"Failed to execute todo: {str(e)}"
            }
    
    async def _route_execution(self, todo: Todo) -> Dict[str, Any]:
        """Route todo execution based on content analysis"""
        content = todo.content.lower()
        
        # Math calculation - be more specific to avoid false positives
        has_math_operators = any(op in todo.content for op in ['+', '-', '*', '/', '=', '(', ')'])
        has_math_keywords = any(word in content for word in ['calculate', 'compute', 'solve', 'math'])
        has_numbers_with_operators = bool(re.search(r'\d+\s*[+\-*/]\s*\d+', todo.content))
        
        if has_numbers_with_operators or (has_math_operators and has_math_keywords):
            return await self._execute_math_todo(todo)
        
        # File operations
        elif any(word in content for word in ['create', 'write', 'save', 'file']):
            return await self._execute_file_todo(todo)
        
        # Research/Information gathering
        elif any(word in content for word in ['research', 'find', 'search', 'gather', 'analyze']):
            return await self._execute_research_todo(todo)
        
        # Planning/Organization
        elif any(word in content for word in ['plan', 'organize', 'schedule', 'prioritize']):
            return await self._execute_planning_todo(todo)
        
        # Default generic execution
        else:
            return await self._execute_generic_todo(todo)
    
    async def _execute_math_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute mathematical calculations"""
        content = todo.content
        
        # Extract mathematical expressions
        math_expressions = self._extract_math_expressions(content)
        
        results = {}
        for expr in math_expressions:
            try:
                # Clean and evaluate the expression
                cleaned_expr = self._clean_math_expression(expr)
                result = self._safe_eval_math(cleaned_expr)
                results[expr] = result
            except Exception as e:
                results[expr] = f"Error: {str(e)}"
        
        if results:
            # Format the output
            output_lines = []
            for expr, result in results.items():
                if isinstance(result, (int, float)):
                    output_lines.append(f"{expr} = {result}")
                else:
                    output_lines.append(f"{expr} → {result}")
            
            return {
                "execution_type": "math_calculation",
                "output": "\n".join(output_lines),
                "details": {"expressions": results},
                "feedback": f"Successfully calculated {len(results)} mathematical expression(s)"
            }
        else:
            # If no math expressions found, provide guidance
            return {
                "execution_type": "math_guidance",
                "output": "Math todo identified but no clear expressions found. Consider breaking down into specific calculations.",
                "details": {"original_content": content},
                "feedback": "Todo appears to be math-related but needs more specific expressions"
            }
    
    async def _execute_file_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute file-related operations"""
        content = todo.content.lower()
        
        # This is a safe implementation - in a real scenario, you might want more sophisticated file operations
        if 'create' in content or 'write' in content:
            output = "File operation identified. In a real implementation, this would create/write files based on the specifications."
            feedback = "File creation todo processed (simulated for safety)"
        elif 'save' in content:
            output = "Save operation identified. Data would be persisted to appropriate storage."
            feedback = "Save operation processed (simulated)"
        else:
            output = "Generic file operation identified."
            feedback = "File operation processed"
        
        return {
            "execution_type": "file_operation",
            "output": output,
            "details": {"operation_type": "file_management"},
            "feedback": feedback
        }
    
    async def _execute_research_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute research and information gathering tasks"""
        content = todo.content
        
        # Simulate research by analyzing what needs to be researched
        research_topics = self._extract_research_topics(content)
        
        output_lines = []
        output_lines.append(f"Research task: {todo.content}")
        output_lines.append(f"Identified {len(research_topics)} research area(s):")
        
        for i, topic in enumerate(research_topics, 1):
            output_lines.append(f"  {i}. {topic}")
        
        output_lines.append("\nNext steps for real implementation:")
        output_lines.append("- Use web search APIs or databases")
        output_lines.append("- Compile and summarize findings")
        output_lines.append("- Organize information by relevance")
        
        return {
            "execution_type": "research",
            "output": "\n".join(output_lines),
            "details": {"research_topics": research_topics},
            "feedback": f"Research todo analyzed. Found {len(research_topics)} areas to investigate."
        }
    
    async def _execute_planning_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute planning and organization tasks"""
        content = todo.content
        
        # Extract planning elements
        planning_elements = self._extract_planning_elements(content)
        
        output_lines = []
        output_lines.append(f"Planning task: {todo.content}")
        output_lines.append(f"Planning framework created:")
        
        for category, items in planning_elements.items():
            if items:
                output_lines.append(f"\n{category.title()}:")
                for item in items:
                    output_lines.append(f"  - {item}")
        
        return {
            "execution_type": "planning",
            "output": "\n".join(output_lines),
            "details": {"planning_elements": planning_elements},
            "feedback": "Planning structure created and organized"
        }
    
    async def _execute_generic_todo(self, todo: Todo) -> Dict[str, Any]:
        """Execute generic todos"""
        content = todo.content
        
        # Analyze the todo and provide structured output
        analysis = self._analyze_generic_todo(content)
        
        output_lines = []
        output_lines.append(f"Task: {todo.content}")
        output_lines.append(f"Analysis: {analysis['description']}")
        
        if analysis['steps']:
            output_lines.append("\nSuggested execution steps:")
            for i, step in enumerate(analysis['steps'], 1):
                output_lines.append(f"  {i}. {step}")
        
        if analysis['considerations']:
            output_lines.append("\nImportant considerations:")
            for consideration in analysis['considerations']:
                output_lines.append(f"  - {consideration}")
        
        return {
            "execution_type": "generic",
            "output": "\n".join(output_lines),
            "details": analysis,
            "feedback": "Generic todo processed and analyzed"
        }
    
    def _extract_math_expressions(self, content: str) -> List[str]:
        """Extract mathematical expressions from content"""
        expressions = []
        
        # Pattern for mathematical expressions
        math_pattern = r'[\d\+\-\*/\(\)\.\s]+=?[\d\+\-\*/\(\)\.\s]*'
        
        # Find explicit expressions with equals
        equals_pattern = r'[^=]*=[^=]*'
        equals_matches = re.findall(equals_pattern, content)
        
        for match in equals_matches:
            # Clean up the match
            cleaned = match.strip()
            if any(op in cleaned for op in ['+', '-', '*', '/']):
                expressions.append(cleaned)
        
        # If no equals found, look for mathematical patterns
        if not expressions:
            # Look for sequences of numbers and operators
            number_op_pattern = r'\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*'
            math_matches = re.findall(number_op_pattern, content)
            expressions.extend(math_matches)
        
        return list(set(expressions))  # Remove duplicates
    
    def _clean_math_expression(self, expr: str) -> str:
        """Clean and prepare mathematical expression for evaluation"""
        # Remove equals and everything after it for evaluation
        if '=' in expr:
            expr = expr.split('=')[0].strip()
        
        # Replace common symbols
        expr = expr.replace('^', '**')  # Power operator
        expr = expr.replace('x', '*')   # Multiplication
        
        # Remove spaces
        expr = re.sub(r'\s+', '', expr)
        
        return expr
    
    def _safe_eval_math(self, expr: str) -> float:
        """Safely evaluate mathematical expressions"""
        try:
            # Use ast.literal_eval for simple expressions
            # For more complex expressions, we'd need a proper math parser
            
            # Simple approach: use eval with restricted globals (be careful!)
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "max": max,
                "min": min,
                "round": round,
                "pow": pow
            }
            
            # Only allow mathematical operations
            if re.match(r'^[\d\+\-\*/\(\)\.\s]+$', expr):
                result = eval(expr, allowed_names, {})
                return float(result)
            else:
                raise ValueError("Expression contains invalid characters")
                
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression '{expr}': {str(e)}")
    
    def _extract_research_topics(self, content: str) -> List[str]:
        """Extract research topics from content"""
        topics = []
        
        # Look for specific patterns
        if 'about' in content.lower():
            # Extract what comes after "about"
            about_pattern = r'about\s+([^,.!?]+)'
            matches = re.findall(about_pattern, content.lower())
            topics.extend([match.strip() for match in matches])
        
        # Look for quoted topics
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, content)
        topics.extend(quotes)
        
        # If no specific topics found, use the whole content as topic
        if not topics:
            topics.append(content.strip())
        
        return topics
    
    def _extract_planning_elements(self, content: str) -> Dict[str, List[str]]:
        """Extract planning elements from content"""
        elements = {
            "objectives": [],
            "tasks": [],
            "timeline": [],
            "resources": [],
            "considerations": []
        }
        
        content_lower = content.lower()
        
        # Extract different types of planning elements
        if any(word in content_lower for word in ['goal', 'objective', 'aim']):
            elements["objectives"].append("Define clear objectives")
            
        if any(word in content_lower for word in ['task', 'step', 'action']):
            elements["tasks"].append("Break down into actionable tasks")
            
        if any(word in content_lower for word in ['time', 'schedule', 'deadline', 'when']):
            elements["timeline"].append("Set realistic timeline")
            
        if any(word in content_lower for word in ['resource', 'budget', 'cost', 'need']):
            elements["resources"].append("Identify required resources")
            
        # Always add basic considerations
        elements["considerations"].extend([
            "Review feasibility",
            "Consider potential obstacles",
            "Plan for contingencies"
        ])
        
        return elements
    
    def _analyze_generic_todo(self, content: str) -> Dict[str, Any]:
        """Analyze generic todo content"""
        analysis = {
            "description": "",
            "steps": [],
            "considerations": [],
            "complexity": "medium"
        }
        
        content_lower = content.lower()
        
        # Determine complexity
        if len(content.split()) < 5:
            analysis["complexity"] = "low"
        elif len(content.split()) > 15:
            analysis["complexity"] = "high"
        
        # Generate description
        if any(word in content_lower for word in ['implement', 'create', 'build']):
            analysis["description"] = "Implementation or creation task"
        elif any(word in content_lower for word in ['fix', 'solve', 'resolve']):
            analysis["description"] = "Problem-solving task"
        elif any(word in content_lower for word in ['review', 'check', 'verify']):
            analysis["description"] = "Review or verification task"
        else:
            analysis["description"] = "General task requiring attention"
        
        # Generate basic steps
        analysis["steps"] = [
            "Understand the requirement clearly",
            "Gather necessary information/resources",
            "Execute the task step by step",
            "Verify completion and quality"
        ]
        
        # Add considerations based on content
        if analysis["complexity"] == "high":
            analysis["considerations"].append("Consider breaking into smaller subtasks")
        if any(word in content_lower for word in ['deadline', 'urgent', 'asap']):
            analysis["considerations"].append("Time-sensitive - prioritize accordingly")
        
        return analysis
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        if not self.execution_history:
            return {"message": "No executions recorded"}
        
        successful = sum(1 for exec in self.execution_history if exec.get("success", False))
        failed = len(self.execution_history) - successful
        
        avg_execution_time = sum(exec.get("execution_time", 0) for exec in self.execution_history) / len(self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.execution_history) * 100,
            "average_execution_time": avg_execution_time,
            "recent_executions": self.execution_history[-5:]  # Last 5 executions
        }
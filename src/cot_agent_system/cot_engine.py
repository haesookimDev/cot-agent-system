import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from .models import CoTStep, CoTProcess, Todo, AgentConfig
from .todo_manager import TodoManager


class CoTEngine:
    def __init__(self, llm: BaseChatModel, config: AgentConfig):
        self.llm = llm
        self.config = config
        self.todo_manager = TodoManager()
        
        self.cot_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant that uses Chain of Thought reasoning to break down complex problems into manageable todos.

Your task is to:
1. Analyze the user's query carefully
2. Break it down into logical steps using chain of thought reasoning
3. Create specific, actionable todos for each step
4. Consider dependencies between todos
5. Provide reasoning for each decision

For each step, you should:
- Explain your thinking process
- Identify what needs to be done
- Consider potential challenges or dependencies
- Create clear, actionable todos

Return your response in a structured format that includes:
- Your reasoning steps
- The todos you've identified
- Dependencies between todos
- Priority levels for each todo

Format your response with clear sections like:
## Step 1: [Step name]
[Your reasoning]

## Step 2: [Step name]
[Your reasoning]

And include actionable todos like:
Action: [specific actionable task]
Action: [another specific actionable task]"""),
            ("human", "Please analyze this query: {query}")
        ])
        
        self.feedback_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
You are analyzing feedback from todo execution to improve the process.

Based on the feedback provided, you should:
1. Analyze what went wrong or what could be improved
2. Suggest modifications to existing todos
3. Suggest new todos if needed
4. Update priorities or dependencies
5. Provide clear reasoning for your suggestions

Be specific and actionable in your recommendations.
"""),
            HumanMessage(content="""
Todo: {todo_content}
Status: {todo_status}
Feedback: {feedback}
Current todos: {current_todos}

Please analyze this feedback and suggest improvements.
""")
        ])
    
    def create_cot_process(self, query: str) -> CoTProcess:
        """Create a new Chain of Thought process for the given query"""
        process_id = str(uuid.uuid4())
        process = CoTProcess(
            process_id=process_id,
            query=query
        )
        return process
    
    async def analyze_query(self, query: str) -> CoTProcess:
        """Analyze a query using Chain of Thought reasoning and generate todos"""
        process = self.create_cot_process(query)
        
        try:
            # Generate initial chain of thought
            formatted_prompt = self.cot_prompt.format_messages(query=query)
            response = await self.llm.ainvoke(formatted_prompt)
            
            # Handle response content
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the response and create CoT steps
            steps = self._parse_cot_response(response_content)
            process.steps.extend(steps)
            
            # Generate todos based on the analysis
            todos = self._generate_todos_from_steps(steps)
            process.todos.extend(todos)
            
            # Add todos to the manager
            for todo in todos:
                self.todo_manager.todos[todo.id] = todo
            
            print(f"✅ Successfully analyzed query and created {len(todos)} todos")
            
        except Exception as e:
            print(f"⚠️  Error during LLM analysis: {e}")
            print("Creating fallback todos based on query analysis...")
            
            # Create fallback todos when LLM fails
            fallback_todos = self._create_fallback_todos(query)
            process.todos.extend(fallback_todos)
            
            for todo in fallback_todos:
                self.todo_manager.todos[todo.id] = todo
        
        process.updated_at = datetime.now()
        return process
    
    def _parse_cot_response(self, response) -> List[CoTStep]:
        """Parse the LLM response into CoT steps"""
        steps = []
        
        # Handle different response types safely
        if hasattr(response, 'content'):
            response_text = response.content
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        # This is a simplified parser - in a real implementation,
        # you might want to use more sophisticated NLP or structured output
        lines = response_text.split('\n')
        current_step = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Step ') or line.startswith('## Step'):
                if current_step:
                    steps.append(current_step)
                
                step_id = str(uuid.uuid4())
                current_step = CoTStep(
                    step_id=step_id,
                    description=line,
                    reasoning=line
                )
            elif current_step and line:
                current_step.reasoning += f"\n{line}"
        
        if current_step:
            steps.append(current_step)
        
        return steps
    
    def _generate_todos_from_steps(self, steps: List[CoTStep]) -> List[Todo]:
        """Generate todos from CoT steps"""
        todos = []
        
        for i, step in enumerate(steps):
            todo_id = str(uuid.uuid4())
            
            # Extract actionable items from the step reasoning
            todo_content = self._extract_todo_content(step.reasoning)
            
            # Determine dependencies (each todo depends on the previous one)
            dependencies = []
            if i > 0 and todos:
                dependencies = [todos[i-1].id]
            
            todo = Todo(
                id=todo_id,
                content=todo_content,
                priority=i + 1,  # Earlier steps have higher priority
                dependencies=dependencies,
                reasoning=step.reasoning,
                metadata={"step_id": step.step_id}
            )
            
            todos.append(todo)
        
        return todos
    
    def _create_fallback_todos(self, query: str) -> List[Todo]:
        """Create fallback todos when LLM is unavailable"""
        todos = []
        
        # Detect query type and create appropriate todos
        if any(op in query for op in ['+', '-', '*', '/', '=', 'calculate', 'compute']):
            # Math problem - create a direct calculation todo
            # Extract the math expression from the query
            math_expr = query.strip()
            if math_expr.endswith('='):
                math_expr = math_expr[:-1].strip()
                
            todos.append(Todo(
                id=str(uuid.uuid4()),
                content=f"Calculate {math_expr}",
                priority=1,
                reasoning=f"Perform mathematical calculation: {math_expr}"
            ))
            
            # Add verification step if it's a complex expression
            if len(math_expr.split()) > 3 or any(op in math_expr for op in ['*', '/', '(', ')']):
                todos.append(Todo(
                    id=str(uuid.uuid4()),
                    content=f"Verify calculation result for {math_expr}",
                    priority=2,
                    reasoning="Double-check the calculation for accuracy"
                ))
        elif any(word in query.lower() for word in ['plan', 'organize', 'schedule', 'prepare']):
            # Planning task
            todos.extend([
                Todo(
                    id=str(uuid.uuid4()),
                    content="Research and gather information about the topic",
                    priority=1,
                    reasoning="Good planning starts with thorough research"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Break down the plan into major components",
                    priority=2,
                    reasoning="Decomposing complex plans makes them manageable"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Set priorities and establish timeline",
                    priority=3,
                    reasoning="Prioritization and timing are key to successful execution"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Create detailed action items for each component",
                    priority=4,
                    reasoning="Specific actions make plans actionable"
                )
            ])
        else:
            # Generic analysis task
            todos.extend([
                Todo(
                    id=str(uuid.uuid4()),
                    content="Analyze and understand the request",
                    priority=1,
                    reasoning="Understanding the core request is essential"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Research relevant information and context",
                    priority=2,
                    reasoning="Background research provides necessary context"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Develop a structured approach to address the request",
                    priority=3,
                    reasoning="A systematic approach ensures comprehensive coverage"
                ),
                Todo(
                    id=str(uuid.uuid4()),
                    content="Implement the solution step by step",
                    priority=4,
                    reasoning="Step-by-step implementation reduces complexity"
                )
            ])
        
        # Set up dependencies (each todo depends on the previous one)
        for i in range(1, len(todos)):
            todos[i].dependencies = [todos[i-1].id]
        
        return todos
    
    def _extract_todo_content(self, reasoning: str) -> str:
        """Extract actionable todo content from reasoning text"""
        # This is a simplified extraction - in practice, you might use more sophisticated NLP
        lines = reasoning.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['todo:', 'action:', 'task:', 'do:', 'create:', 'implement:']):
                return line
        
        # If no explicit todo found, use the first meaningful line
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not line.startswith('#'):
                return line
        
        return reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
    
    async def process_feedback(
        self, 
        todo_id: str, 
        feedback: str, 
        todo_status: str
    ) -> Dict[str, Any]:
        """Process feedback and suggest improvements"""
        todo = self.todo_manager.get_todo(todo_id)
        if not todo:
            return {"error": "Todo not found"}
        
        # Get current todos context
        current_todos = [
            f"- {t.content} (Status: {t.status})" 
            for t in self.todo_manager.get_all_todos()
        ]
        current_todos_str = "\n".join(current_todos)
        
        # Generate feedback analysis
        response = await self.llm.ainvoke(
            self.feedback_prompt.format_messages(
                todo_content=todo.content,
                todo_status=todo_status,
                feedback=feedback,
                current_todos=current_todos_str
            )
        )
        
        # Parse suggestions from the response
        suggestions = self._parse_feedback_suggestions(response.content)
        
        # Create feedback entry
        feedback_entry = self.todo_manager.create_feedback_entry(
            todo_id=todo_id,
            feedback_type="analysis",
            message=feedback,
            suggestions=suggestions
        )
        
        return {
            "feedback_entry": feedback_entry,
            "suggestions": suggestions,
            "analysis": response.content
        }
    
    def _parse_feedback_suggestions(self, analysis) -> List[str]:
        """Parse suggestions from feedback analysis"""
        suggestions = []
        
        # Handle different response types safely
        if hasattr(analysis, 'content'):
            analysis_text = analysis.content
        elif isinstance(analysis, str):
            analysis_text = analysis
        else:
            analysis_text = str(analysis)
        
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                suggestions.append(line[2:])
            elif 'suggest' in line.lower() or 'recommend' in line.lower():
                suggestions.append(line)
        
        return suggestions
    
    async def update_todos_based_on_feedback(
        self, 
        feedback_entry_id: str
    ) -> List[Todo]:
        """Update todos based on feedback analysis"""
        feedback_entry = self.todo_manager.feedback_entries.get(feedback_entry_id)
        if not feedback_entry:
            return []
        
        new_todos = []
        
        # Create new todos based on suggestions
        for suggestion in feedback_entry.suggestions:
            if any(keyword in suggestion.lower() for keyword in ['create', 'add', 'new', 'implement']):
                todo = self.todo_manager.create_todo(
                    content=suggestion,
                    reasoning=f"Generated from feedback: {feedback_entry.message}"
                )
                new_todos.append(todo)
        
        return new_todos
    
    def get_process_status(self, process: CoTProcess) -> Dict[str, Any]:
        """Get the current status of a CoT process"""
        stats = self.todo_manager.get_statistics()
        
        return {
            "process_id": process.process_id,
            "query": process.query,
            "total_steps": len(process.steps),
            "total_todos": len(process.todos),
            "todo_stats": stats,
            "next_todo": self.todo_manager.get_next_todo(),
            "status": process.status
        }
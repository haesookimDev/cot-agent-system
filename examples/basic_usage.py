"""
Basic usage example of the CoT Agent System.

This example demonstrates how to:
1. Initialize the agent
2. Process a query using Chain of Thought
3. Execute todos with feedback loops
4. Monitor progress and results
"""

import asyncio
import os
from dotenv import load_dotenv

from cot_agent_system import CoTAgent, AgentConfig

# Load environment variables (for API keys)
load_dotenv()


async def basic_example():
    """Basic example of using the CoT Agent System"""
    
    print("🚀 CoT Agent System - Basic Usage Example")
    print("=" * 50)
    
    # Configure the agent from environment variables
    try:
        config = AgentConfig.from_env()
        print("✅ Configuration loaded from environment variables")
        print(f"   Model: {config.model_name}")
        print(f"   Temperature: {config.temperature}")
        print(f"   Max Iterations: {config.max_iterations}")
        if config.api_key:
            print("   API Key: ✅ Found")
        else:
            print("   API Key: ❌ Not found (required for LLM functionality)")
    except Exception as e:
        print(f"⚠️  Error loading from environment: {e}")
        print("Using default configuration...")
        config = AgentConfig()
    
    # Initialize the agent
    print("\n🔧 Initializing CoT Agent...")
    agent = CoTAgent(config=config)
    
    # Example query
    query = """
    I want to plan a weekend trip to a nearby city. Help me organize everything I need to do,
    from researching destinations to booking accommodations and planning activities.
    """
    
    print(f"\n📝 Processing Query:")
    print(f"'{query.strip()}'")
    
    try:
        # Process the query
        result = await agent.process_query(query)
        
        print(f"\n📊 Processing Complete!")
        print(f"- Process ID: {result['process'].process_id}")
        print(f"- Total CoT Steps: {len(result['process'].steps)}")
        print(f"- Generated Todos: {len(result['process'].todos)}")
        print(f"- Execution Iterations: {result['result']['iterations']}")
        
        # Show final statistics
        final_stats = result['result']['final_stats']
        print(f"\n📈 Final Statistics:")
        print(f"- Total Todos: {final_stats['total']}")
        print(f"- Completed: {final_stats['completed']}")
        print(f"- Failed: {final_stats['failed']}")
        print(f"- Pending: {final_stats['pending']}")
        
        # Show todos summary
        print(f"\n📋 Todos Summary:")
        todos_summary = agent.get_todos_summary()
        
        if todos_summary['completed_todos']:
            print("✅ Completed Todos:")
            for todo in todos_summary['completed_todos']:
                print(f"  - {todo['content']}")
        
        if todos_summary['failed_todos']:
            print("❌ Failed Todos:")
            for todo in todos_summary['failed_todos']:
                print(f"  - {todo['content']}")
                if todo['feedback']:
                    print(f"    Feedback: {todo['feedback']}")
        
        if todos_summary['pending_todos']:
            print("⏳ Pending Todos:")
            for todo in todos_summary['pending_todos']:
                print(f"  - {todo['content']}")
        
        print("\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        print("💡 Note: This example requires proper LLM configuration.")
        print("   In a real scenario, you'd need to set up your API keys.")


async def manual_feedback_example():
    """Example showing manual feedback functionality"""
    
    print("\n🔄 Manual Feedback Example")
    print("=" * 30)
    
    # Load config from environment and override max_iterations
    config = AgentConfig.from_env()
    config.max_iterations = 3
    agent = CoTAgent(config=config)
    
    # Create a simple process
    query = "Help me organize my desk workspace for better productivity"
    
    try:
        result = await agent.process_query(query)
        
        # Get the first todo for manual feedback
        todos_summary = agent.get_todos_summary()
        
        if todos_summary['completed_todos']:
            first_todo_id = todos_summary['completed_todos'][0]['id']
            
            # Add manual feedback
            feedback_result = await agent.add_manual_feedback(
                todo_id=first_todo_id,
                feedback="This todo was completed well, but we could add more specific organization tips."
            )
            
            print(f"📝 Manual feedback added:")
            print(f"- Suggestions: {len(feedback_result.get('suggestions', []))}")
            print(f"- Analysis available: {bool(feedback_result.get('analysis'))}")
        
        print("✅ Manual feedback example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def simulate_without_llm():
    """Simulate the system without requiring actual LLM calls"""
    
    print("\n🎭 Simulation Mode (No LLM Required)")
    print("=" * 40)
    
    from cot_agent_system import TodoManager, CoTProcess, CoTStep, Todo
    import uuid
    
    # Create a mock process
    process = CoTProcess(
        process_id=str(uuid.uuid4()),
        query="Plan a healthy meal prep for the week"
    )
    
    # Create some CoT steps
    steps = [
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 1: Research healthy recipes",
            reasoning="First, I need to research healthy recipes that are suitable for meal prep..."
        ),
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 2: Create shopping list", 
            reasoning="Based on the recipes, I'll create a comprehensive shopping list..."
        ),
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 3: Plan preparation schedule",
            reasoning="I need to plan when to do the actual meal preparation..."
        )
    ]
    
    process.steps.extend(steps)
    
    # Create corresponding todos
    todo_manager = TodoManager()
    
    todos = [
        todo_manager.create_todo(
            content="Research 5 healthy recipes suitable for meal prep",
            priority=1,
            reasoning="Need nutritious, prep-friendly recipes"
        ),
        todo_manager.create_todo(
            content="Create detailed shopping list with quantities",
            priority=2,
            dependencies=[],  # In real scenario, would depend on first todo
            reasoning="Organized shopping saves time"
        ),
        todo_manager.create_todo(
            content="Schedule 3-hour meal prep session for Sunday",
            priority=3,
            reasoning="Need dedicated time for preparation"
        )
    ]
    
    process.todos.extend(todos)
    
    print(f"📋 Created simulated process:")
    print(f"- Process ID: {process.process_id}")
    print(f"- Query: {process.query}")
    print(f"- CoT Steps: {len(process.steps)}")
    print(f"- Generated Todos: {len(process.todos)}")
    
    print(f"\n🧠 Chain of Thought Steps:")
    for i, step in enumerate(process.steps, 1):
        print(f"  {i}. {step.description}")
        print(f"     Reasoning: {step.reasoning[:80]}...")
    
    print(f"\n✅ Generated Todos:")
    for i, todo in enumerate(process.todos, 1):
        print(f"  {i}. {todo.content}")
        print(f"     Priority: {todo.priority}")
        print(f"     Status: {todo.status}")
    
    # Simulate executing todos
    print(f"\n🔄 Simulating Todo Execution:")
    for todo in todos:
        print(f"  Executing: {todo.content}")
        todo_manager.update_todo_status(todo.id, "completed")
        print(f"  ✅ Completed")
    
    # Show final stats
    stats = todo_manager.get_statistics()
    print(f"\n📊 Final Statistics:")
    print(f"- Total: {stats['total']}")
    print(f"- Completed: {stats['completed']}")
    print(f"- Success Rate: {stats['completed']/stats['total']*100:.1f}%")
    
    print("\n🎉 Simulation completed successfully!")


async def main():
    """Run all examples"""
    
    print("🤖 CoT Agent System Examples")
    print("=" * 50)
    
    # Run simulation first (no LLM required)
    simulate_without_llm()
    
    # Uncomment these to run with actual LLM (requires API setup)
    # await basic_example()
    # await manual_feedback_example()
    
    print(f"\n💡 To run examples with actual LLM:")
    print(f"1. Set up your OpenAI API key in environment variables")
    print(f"2. Uncomment the LLM example calls in main()")
    print(f"3. Run: uv run python examples/basic_usage.py")


if __name__ == "__main__":
    asyncio.run(main())
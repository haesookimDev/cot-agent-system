#!/usr/bin/env python3
"""
Test script to demonstrate interactive feedback functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cot_agent_system import CoTAgent, AgentConfig, InteractiveFeedbackManager


async def demo_interactive_feedback():
    """Demonstrate interactive feedback with simulated responses"""
    
    print("🎭 Interactive Feedback Demo")
    print("=" * 40)
    
    # Create config
    config = AgentConfig.from_env()
    
    # Create agent with interactive feedback enabled
    agent = CoTAgent(config=config, interactive=True)
    
    # Set up a simple mock feedback handler for demo
    async def mock_feedback_handler(request):
        print(f"\n🤖 FEEDBACK REQUEST: {request.feedback_type.value.upper()}")
        print(f"Message: {request.message}")
        if request.options:
            print(f"Options: {', '.join(request.options)}")
        
        # Auto-respond for demo purposes
        if request.feedback_type.value == "approval":
            response = "yes"
            print(f"Auto-response: {response}")
            return response
        elif request.feedback_type.value == "validation":
            response = "accept"
            print(f"Auto-response: {response}")
            return response
        elif request.feedback_type.value == "guidance":
            response = "continue"
            print(f"Auto-response: {response}")
            return response
        else:
            response = request.default_response or "ok"
            print(f"Auto-response: {response}")
            return response
    
    # Set the mock handler
    agent.feedback_manager.feedback_handler = mock_feedback_handler
    
    # Process a simple query
    query = "Calculate 15*3+10-5"
    
    print(f"\n🔄 Processing with interactive feedback: {query}")
    print("-" * 50)
    
    try:
        result = await agent.process_query(query)
        
        print("\n" + "=" * 50)
        print("📊 RESULTS:")
        print(f"- Process ID: {result['process'].process_id}")
        print(f"- Total Todos: {len(result['process'].todos)}")
        print(f"- Iterations: {result['result']['iterations']}")
        
        # Show feedback summary
        feedback_summary = result['result'].get('feedback_summary', {})
        if feedback_summary and not feedback_summary.get('message'):
            print(f"\n💬 Feedback Summary:")
            print(f"- Total Requests: {feedback_summary['total_requests']}")
            print(f"- Average Response Time: {feedback_summary['average_response_time']:.2f}s")
            
            if feedback_summary.get('by_type'):
                print("- Request Types:")
                for req_type, count in feedback_summary['by_type'].items():
                    print(f"  • {req_type}: {count}")
        
        print("\n✅ Interactive feedback demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


async def demo_basic_functionality():
    """Demonstrate basic functionality without interactive feedback"""
    
    print("\n🚀 Basic Functionality Demo")
    print("=" * 30)
    
    config = AgentConfig.from_env()
    agent = CoTAgent(config=config, interactive=False)  # Non-interactive
    
    query = "Calculate 25*4+15"
    
    print(f"Processing: {query}")
    
    result = await agent.process_query(query)
    
    print(f"\n📊 Results:")
    print(f"- Generated {len(result['process'].todos)} todos")
    print(f"- Completed in {result['result']['iterations']} iterations")
    print(f"- Success: {result['result']['completed']}")
    
    # Show completed todos with their results
    todos_summary = agent.get_todos_summary()
    if todos_summary['completed_todos']:
        print(f"\n✅ Completed todos:")
        for todo in todos_summary['completed_todos']:
            print(f"  - {todo['content']}")


async def main():
    """Run all demos"""
    
    print("🤖 CoT Agent Interactive Feedback System Demo")
    print("=" * 50)
    
    # Run basic demo first
    await demo_basic_functionality()
    
    # Then interactive demo
    await demo_interactive_feedback()
    
    print(f"\n🎉 All demos completed!")
    print("\n💡 To try interactive feedback manually:")
    print("   python run.py process --interactive-feedback")
    print("   (Note: This will actually prompt you for input)")


if __name__ == "__main__":
    asyncio.run(main())
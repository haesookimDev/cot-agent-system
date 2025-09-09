#!/usr/bin/env python3
"""
CLI interface for the CoT Agent System.

This module provides a command-line interface for users to interact with
the Chain of Thought agent system.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from .agent import CoTAgent
from .models import AgentConfig


@click.group()
@click.version_option()
def cli():
    """CoT Agent System - Chain of Thought based agent for task management."""
    pass


@cli.command()
@click.argument('query', required=False)
@click.option('--model', '-m', default='gpt-3.5-turbo', help='LLM model to use')
@click.option('--temperature', '-t', default=0.7, help='Temperature for LLM')
@click.option('--max-tokens', default=1000, help='Maximum tokens for LLM response')
@click.option('--max-iterations', default=5, help='Maximum execution iterations')
@click.option('--thinking-depth', default=3, help='Depth of Chain of Thought reasoning')
@click.option('--config-file', '-c', help='Path to configuration file')
@click.option('--save-result', '-s', help='Save result to JSON file')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
def process(query: Optional[str], model: str, temperature: float, max_tokens: int,
           max_iterations: int, thinking_depth: int, config_file: Optional[str],
           save_result: Optional[str], interactive: bool):
    """Process a query using Chain of Thought reasoning."""
    
    # Load environment variables (done automatically in AgentConfig.from_env())
    
    # Load configuration
    config = _load_config(config_file, model, temperature, max_tokens, 
                         max_iterations, thinking_depth)
    
    if interactive or not query:
        asyncio.run(_interactive_mode(config, save_result))
    else:
        asyncio.run(_process_single_query(query, config, save_result))


@cli.command()
@click.option('--output', '-o', default='config.json', help='Output configuration file')
@click.option('--env-template', '-e', is_flag=True, help='Generate .env template instead')
def init_config(output: str, env_template: bool):
    """Initialize a configuration file with default values."""
    
    if env_template:
        # Generate .env template
        config = AgentConfig()
        env_content = config.to_env_template()
        
        env_path = Path('.env.template')
        if env_path.exists():
            click.confirm(f"Template file {env_path} already exists. Overwrite?", abort=True)
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        click.echo(f"Environment template created: {env_path}")
        click.echo("Copy to .env and edit to customize your settings.")
    else:
        # Generate JSON config file
        config = AgentConfig()
        config_data = config.model_dump()
        
        config_path = Path(output)
        
        if config_path.exists():
            click.confirm(f"Configuration file {output} already exists. Overwrite?", abort=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        click.echo(f"Configuration file created: {output}")
        click.echo("Edit the file to customize your settings.")


@cli.command()
def example():
    """Run a built-in example without requiring LLM setup."""
    
    click.echo("🎭 Running CoT Agent System Example")
    click.echo("=" * 40)
    
    from .todo_manager import TodoManager
    from .models import CoTProcess, CoTStep, Todo
    import uuid
    
    # Create a mock process
    process = CoTProcess(
        process_id=str(uuid.uuid4()),
        query="Plan a productive workday schedule"
    )
    
    # Create CoT steps
    steps = [
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 1: Analyze current commitments",
            reasoning="First, I need to understand existing commitments and deadlines..."
        ),
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 2: Prioritize tasks by importance and urgency",
            reasoning="Using the Eisenhower matrix to categorize tasks..."
        ),
        CoTStep(
            step_id=str(uuid.uuid4()),
            description="Step 3: Create time-blocked schedule",
            reasoning="Allocating specific time blocks for focused work..."
        )
    ]
    
    process.steps.extend(steps)
    
    # Create todos
    todo_manager = TodoManager()
    
    todos = [
        todo_manager.create_todo(
            content="Review calendar and list all commitments for today",
            priority=1,
            reasoning="Need to understand current obligations"
        ),
        todo_manager.create_todo(
            content="Categorize tasks using importance/urgency matrix",
            priority=2,
            reasoning="Prioritization helps focus on what matters most"
        ),
        todo_manager.create_todo(
            content="Create 2-hour time blocks for deep work",
            priority=3,
            reasoning="Time blocking improves focus and productivity"
        )
    ]
    
    process.todos.extend(todos)
    
    click.echo(f"📋 Process Details:")
    click.echo(f"- Process ID: {process.process_id}")
    click.echo(f"- Query: {process.query}")
    click.echo(f"- CoT Steps: {len(process.steps)}")
    click.echo(f"- Generated Todos: {len(process.todos)}")
    
    click.echo(f"\n🧠 Chain of Thought Steps:")
    for i, step in enumerate(process.steps, 1):
        click.echo(f"  {i}. {step.description}")
        click.echo(f"     💭 {step.reasoning[:60]}...")
    
    click.echo(f"\n✅ Generated Todos:")
    for i, todo in enumerate(process.todos, 1):
        click.echo(f"  {i}. {todo.content}")
        click.echo(f"     Priority: {todo.priority}")
    
    # Simulate execution
    click.echo(f"\n🔄 Simulating Execution:")
    for todo in todos:
        click.echo(f"  ⏳ Processing: {todo.content}")
        todo_manager.update_todo_status(todo.id, "completed")
        click.echo(f"  ✅ Completed")
    
    stats = todo_manager.get_statistics()
    click.echo(f"\n📊 Final Statistics:")
    click.echo(f"- Total: {stats['total']}")
    click.echo(f"- Completed: {stats['completed']}")
    click.echo(f"- Success Rate: {stats['completed']/stats['total']*100:.1f}%")
    
    click.echo("\n🎉 Example completed! This demonstrates the system structure.")
    click.echo("💡 To use with actual LLM, set up API keys and use 'cot-agent process' command.")


async def _interactive_mode(config: AgentConfig, save_result: Optional[str]):
    """Run the agent in interactive mode."""
    
    click.echo("🤖 CoT Agent Interactive Mode")
    click.echo("Type 'quit' or 'exit' to stop, 'help' for commands.")
    click.echo("-" * 50)
    
    agent = CoTAgent(config=config)
    
    while True:
        try:
            query = click.prompt("\n📝 Enter your query", type=str)
            
            if query.lower() in ['quit', 'exit']:
                break
            
            if query.lower() == 'help':
                _show_help()
                continue
            
            if query.lower() == 'stats':
                _show_stats(agent)
                continue
            
            click.echo(f"\n🔄 Processing: {query}")
            
            result = await agent.process_query(query)
            _display_result(result)
            
            if save_result:
                _save_result_to_file(result, save_result)
                
        except KeyboardInterrupt:
            click.echo("\n👋 Goodbye!")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}")


async def _process_single_query(query: str, config: AgentConfig, save_result: Optional[str]):
    """Process a single query and display results."""
    
    click.echo(f"🔄 Processing query: {query}")
    
    try:
        agent = CoTAgent(config=config)
        result = await agent.process_query(query)
        
        _display_result(result)
        
        if save_result:
            _save_result_to_file(result, save_result)
            click.echo(f"💾 Result saved to: {save_result}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


def _load_config(config_file: Optional[str], model: str, temperature: float,
                max_tokens: int, max_iterations: int, thinking_depth: int) -> AgentConfig:
    """Load configuration from file or command line arguments."""
    
    # First try to load from environment variables
    try:
        config = AgentConfig.from_env()
    except Exception:
        config = AgentConfig()
    
    # Override with config file if provided
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Update config with file values
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Override with command line arguments if they differ from defaults
    if model != "gpt-3.5-turbo":
        config.model_name = model
    if temperature != 0.7:
        config.temperature = temperature
    if max_tokens != 1000:
        config.max_tokens = max_tokens
    if max_iterations != 5:
        config.max_iterations = max_iterations
    if thinking_depth != 3:
        config.thinking_depth = thinking_depth
    
    return config


def _display_result(result: dict):
    """Display processing results in a formatted way."""
    
    process = result['process']
    execution_result = result['result']
    
    click.echo(f"\n📊 Processing Complete!")
    click.echo(f"- Process ID: {process.process_id}")
    click.echo(f"- Total CoT Steps: {len(process.steps)}")
    click.echo(f"- Generated Todos: {len(process.todos)}")
    click.echo(f"- Execution Iterations: {execution_result['iterations']}")
    
    # Show final statistics
    final_stats = execution_result['final_stats']
    click.echo(f"\n📈 Final Statistics:")
    click.echo(f"- Total Todos: {final_stats['total']}")
    click.echo(f"- Completed: {final_stats['completed']}")
    click.echo(f"- Failed: {final_stats['failed']}")
    click.echo(f"- Pending: {final_stats['pending']}")


def _save_result_to_file(result: dict, filename: str):
    """Save result to JSON file."""
    
    # Convert to JSON-serializable format
    json_result = {
        'process_id': result['process'].process_id,
        'query': result['process'].query,
        'steps': [step.dict() for step in result['process'].steps],
        'todos': [todo.dict() for todo in result['process'].todos],
        'execution_result': result['result']
    }
    
    with open(filename, 'w') as f:
        json.dump(json_result, f, indent=2, default=str)


def _show_help():
    """Show help for interactive mode."""
    
    click.echo("\n📚 Interactive Mode Commands:")
    click.echo("- Enter any query to process it")
    click.echo("- 'stats' - Show current agent statistics")  
    click.echo("- 'help' - Show this help")
    click.echo("- 'quit' or 'exit' - Exit interactive mode")


def _show_stats(agent: CoTAgent):
    """Show agent statistics."""
    
    stats = agent.get_todos_summary()
    click.echo(f"\n📊 Current Agent Statistics:")
    click.echo(f"- Total Todos: {len(stats.get('all_todos', []))}")
    click.echo(f"- Completed: {len(stats.get('completed_todos', []))}")
    click.echo(f"- Failed: {len(stats.get('failed_todos', []))}")
    click.echo(f"- Pending: {len(stats.get('pending_todos', []))}")


if __name__ == '__main__':
    cli()
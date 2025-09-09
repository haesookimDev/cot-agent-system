#!/usr/bin/env python3
"""
Configuration examples for the CoT Agent System.

This example demonstrates different ways to configure the CoT Agent System:
1. Using environment variables
2. Using configuration files
3. Programmatic configuration
4. Configuration validation and templates
"""

import asyncio
import json
import os
from pathlib import Path

from cot_agent_system import CoTAgent, AgentConfig


def example_env_config():
    """Example 1: Loading configuration from environment variables"""
    
    print("📋 Example 1: Environment Variable Configuration")
    print("=" * 50)
    
    # Load configuration from environment variables
    try:
        config = AgentConfig.from_env()
        
        print("✅ Configuration loaded successfully:")
        print(f"   Model: {config.model_name}")
        print(f"   Temperature: {config.temperature}")
        print(f"   Max Tokens: {config.max_tokens}")
        print(f"   Max Iterations: {config.max_iterations}")
        print(f"   Thinking Depth: {config.thinking_depth}")
        print(f"   Log Level: {config.log_level}")
        
        if config.api_key:
            print(f"   API Key: {'*' * 10}...{config.api_key[-4:] if len(config.api_key) > 4 else '****'}")
        else:
            print("   API Key: ❌ Not found")
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("💡 Make sure you have a .env file or environment variables set")


def example_config_file():
    """Example 2: Using configuration files"""
    
    print("\n📋 Example 2: Configuration File Usage")
    print("=" * 40)
    
    # Create a sample config file
    sample_config = {
        "model_name": "gpt-4",
        "temperature": 0.8,
        "max_tokens": 1500,
        "max_iterations": 8,
        "thinking_depth": 4,
        "log_level": "DEBUG"
    }
    
    config_path = Path("sample_config.json")
    
    print("📝 Creating sample configuration file...")
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample config created: {config_path}")
    
    # Load configuration from file
    print("\n🔄 Loading configuration from file...")
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config = AgentConfig(**config_data)
        
        print("✅ Configuration loaded from file:")
        print(f"   Model: {config.model_name}")
        print(f"   Temperature: {config.temperature}")
        print(f"   Max Iterations: {config.max_iterations}")
        
    except Exception as e:
        print(f"❌ Error loading from file: {e}")
    
    # Cleanup
    if config_path.exists():
        config_path.unlink()
        print("🗑️  Sample config file cleaned up")


def example_programmatic_config():
    """Example 3: Programmatic configuration"""
    
    print("\n📋 Example 3: Programmatic Configuration")
    print("=" * 40)
    
    # Create configuration programmatically
    config = AgentConfig(
        model_name="gpt-3.5-turbo",
        temperature=0.6,
        max_tokens=800,
        max_iterations=3,
        thinking_depth=2,
        log_level="INFO"
    )
    
    print("✅ Configuration created programmatically:")
    print(f"   Model: {config.model_name}")
    print(f"   Temperature: {config.temperature}")
    print(f"   Customized for quick responses")
    
    # Update configuration from environment if available
    print("\n🔄 Updating with environment variables...")
    try:
        config.update_from_env()
        print("✅ Configuration updated with environment values")
    except Exception as e:
        print(f"⚠️  Could not update from environment: {e}")


def example_config_templates():
    """Example 4: Configuration templates and validation"""
    
    print("\n📋 Example 4: Configuration Templates")
    print("=" * 35)
    
    # Generate environment template
    config = AgentConfig()
    env_template = config.to_env_template()
    
    print("📝 Generated environment template:")
    print("-" * 30)
    # Show first few lines of template
    lines = env_template.split('\n')[:15]
    for line in lines:
        print(line)
    print("... (truncated)")
    
    # Save template to file
    template_path = Path(".env.example")
    with open(template_path, 'w') as f:
        f.write(env_template)
    
    print(f"\n✅ Template saved to: {template_path}")
    print("💡 Copy this file to .env and customize your settings")
    
    # Configuration validation example
    print("\n🔍 Configuration validation:")
    try:
        # Valid config
        valid_config = AgentConfig(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        print("✅ Valid configuration created")
        
        # Invalid config (this would raise an error)
        # invalid_config = AgentConfig(temperature=2.0)  # Invalid temperature
        
    except Exception as e:
        print(f"❌ Invalid configuration: {e}")
    
    # Cleanup
    if template_path.exists():
        template_path.unlink()
        print("🗑️  Template file cleaned up")


async def example_config_in_agent():
    """Example 5: Using different configurations with agents"""
    
    print("\n📋 Example 5: Configuration with Agents")
    print("=" * 35)
    
    # Quick response config
    quick_config = AgentConfig(
        model_name="gpt-3.5-turbo",
        temperature=0.3,
        max_tokens=500,
        max_iterations=2,
        thinking_depth=2
    )
    
    # Detailed response config  
    detailed_config = AgentConfig(
        model_name="gpt-4",
        temperature=0.8,
        max_tokens=2000,
        max_iterations=10,
        thinking_depth=5
    )
    
    print("⚡ Quick response agent configuration:")
    print(f"   Low temperature ({quick_config.temperature}) for consistent results")
    print(f"   Fewer iterations ({quick_config.max_iterations}) for speed")
    
    print("\n🔍 Detailed response agent configuration:")
    print(f"   Higher temperature ({detailed_config.temperature}) for creativity")
    print(f"   More iterations ({detailed_config.max_iterations}) for thoroughness")
    
    # Note: In a real scenario, you would create agents with these configs
    # quick_agent = CoTAgent(config=quick_config)
    # detailed_agent = CoTAgent(config=detailed_config)
    
    print("\n💡 Choose configuration based on your use case:")
    print("   - Quick config: Simple queries, fast responses")
    print("   - Detailed config: Complex analysis, comprehensive results")


def main():
    """Run all configuration examples"""
    
    print("🤖 CoT Agent System - Configuration Examples")
    print("=" * 50)
    
    # Run all examples
    example_env_config()
    example_config_file() 
    example_programmatic_config()
    example_config_templates()
    
    # Run async example
    asyncio.run(example_config_in_agent())
    
    print("\n🎉 Configuration examples completed!")
    print("\n💡 Key takeaways:")
    print("1. Environment variables provide flexible configuration")
    print("2. Configuration files enable preset configurations")
    print("3. Programmatic config allows runtime customization")
    print("4. Templates help document configuration options")
    print("5. Different configs suit different use cases")


if __name__ == "__main__":
    main()
"""
Command Runner - Dispatcher for console commands similar to Laravel Artisan.
"""

import asyncio
import sys
from typing import Dict, Any, Type, Optional

from app.commands.base_command import BaseCommand
from app.commands.populate_leads_score import PopulateLeadsScoreCommand
from app.commands.process_leads_openai import ProcessLeadsOpenAICommand


class CommandRunner:
    """Command runner that manages and executes console commands."""
    
    def __init__(self):
        # Register available commands
        self.commands: Dict[str, Type[BaseCommand]] = {
            "populate:leads-score": PopulateLeadsScoreCommand,
            "process:leads-openai": ProcessLeadsOpenAICommand,
        }
    
    def list_commands(self):
        """List all available commands."""
        print("🚀 Available Commands:")
        print("=" * 50)
        
        for signature, command_class in self.commands.items():
            instance = command_class()
            print(f"  {signature}")
            print(f"    {instance.description}")
            print()
    
    async def run_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a specific command.
        
        Args:
            command_name: Name of the command to run
            **kwargs: Command arguments
            
        Returns:
            Dict with command execution results
        """
        if command_name not in self.commands:
            available = ", ".join(self.commands.keys())
            raise ValueError(f"Command '{command_name}' not found. Available commands: {available}")
        
        command_class = self.commands[command_name]
        command_instance = command_class()
        
        return await command_instance.execute(**kwargs)
    
    def run_command_sync(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a command synchronously (wrapper for async run_command).
        
        Args:
            command_name: Name of the command to run
            **kwargs: Command arguments
            
        Returns:
            Dict with command execution results
        """
        return asyncio.run(self.run_command(command_name, **kwargs))


# Global command runner instance
command_runner = CommandRunner()


def run_console_command(command_name: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to run a console command.
    
    Args:
        command_name: Name of the command to run
        **kwargs: Command arguments
        
    Returns:
        Dict with command execution results
    """
    return command_runner.run_command_sync(command_name, **kwargs)


if __name__ == "__main__":
    """
    CLI entry point for running commands from terminal.
    
    Usage:
        python -m app.commands.command_runner list
        python -m app.commands.command_runner populate:leads-score
        python -m app.commands.command_runner populate:leads-score --dry-run
        python -m app.commands.command_runner populate:leads-score --batch-size=100
    """
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.commands.command_runner <command> [options]")
        print("\nAvailable commands:")
        command_runner.list_commands()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        command_runner.list_commands()
        sys.exit(0)
    
    # Parse command line options
    options = {}
    for arg in sys.argv[2:]:
        if arg.startswith('--'):
            if '=' in arg:
                key, value = arg[2:].split('=', 1)
                # Try to convert to appropriate type
                if value.lower() in ('true', 'false'):
                    options[key.replace('-', '_')] = value.lower() == 'true'
                elif value.isdigit():
                    options[key.replace('-', '_')] = int(value)
                else:
                    options[key.replace('-', '_')] = value
            else:
                # Boolean flag
                options[arg[2:].replace('-', '_')] = True
    
    try:
        result = command_runner.run_command_sync(command, **options)
        
        if result.get('success', False):
            print(f"\n🎉 Command completed successfully!")
            if 'total_processed' in result:
                print(f"📊 Processed: {result['total_processed']} items")
            if 'elapsed_time' in result:
                print(f"⏱️  Time taken: {result['elapsed_time']}")
        else:
            print(f"\n💥 Command failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error running command: {str(e)}")
        sys.exit(1)

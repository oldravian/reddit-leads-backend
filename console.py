#!/usr/bin/env python3
"""
Console Script - Laravel Artisan-like command runner for the leads sniffer application.

Usage:
    python console.py list                                    # List all commands
    python console.py populate:leads-score                   # Run populate command
    python console.py populate:leads-score --dry-run         # Run in dry-run mode
    python console.py populate:leads-score --batch-size=100  # Custom batch size
    python console.py process:leads-openai                   # Process leads with OpenAI
    python console.py process:leads-openai --all             # Process all posts
    python console.py process:leads-openai --batch-size=5    # Custom batch size
    python console.py process:leads-openai --max-rows=200    # Process max 200 rows
    python console.py process:leads-openai --all --max-rows=500  # Process max 500 from all posts
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commands.command_runner import CommandRunner


def main():
    """Main CLI entry point."""
    runner = CommandRunner()
    
    if len(sys.argv) < 2:
        print("🚀 Leads Sniffer Console")
        print("=" * 40)
        print("Usage: python console.py <command> [options]")
        print()
        runner.list_commands()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        runner.list_commands()
        return
    
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
        print(f"🚀 Running command: {command}")
        if options:
            print(f"📋 Options: {options}")
        print()
        
        result = runner.run_command_sync(command, **options)
        
        if result.get('success', False):
            print(f"\n🎉 Command completed successfully!")
            print(f"📊 Statistics:")
            if 'total_processed' in result:
                print(f"   • Total Processed: {result['total_processed']}")
            if 'updated' in result:
                print(f"   • Updated: {result['updated']}")
            if 'skipped' in result:
                print(f"   • Skipped: {result['skipped']}")
            if 'errors' in result:
                print(f"   • Errors: {result['errors']}")
            if 'elapsed_time' in result:
                print(f"   • Time Taken: {result['elapsed_time']}")
            if result.get('dry_run'):
                print(f"   • Mode: DRY RUN (no database changes)")
        else:
            print(f"\n💥 Command failed!")
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error running command: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Console Commands

Laravel Artisan-like console commands for the Leads Sniffer application.

## Available Commands

### `populate:leads-score`

Calculates and updates the `leads_score` column for all Reddit posts in the database.

**Features:**

- ✅ **Batch Processing**: Processes posts in configurable batches (default: 50)
- ✅ **Progress Tracking**: Real-time progress bar and statistics
- ✅ **Error Handling**: Graceful error handling with detailed logging
- ✅ **Dry Run Mode**: Test mode without database updates
- ✅ **Background Processing**: Can run as background task via API
- ✅ **Memory Efficient**: Processes large datasets without memory issues

**Usage:**

```bash
# Run the command
uv run python console.py populate:leads-score

# Run with custom batch size
uv run python console.py populate:leads-score --batch-size=100

# Run in dry-run mode (no database updates)
uv run python console.py populate:leads-score --dry-run

# Run with both options
uv run python console.py populate:leads-score --batch-size=75 --dry-run
```

# Small test run - process 5 posts in batches of 2

uv run python console.py process:leads-openai --max-rows=5 --batch-size=2

**Performance:**

- ~30-60 seconds for 1500 posts
- ~50 posts/second processing rate
- Memory usage: <100MB for large datasets

## Command Structure

### Base Command (`BaseCommand`)

All commands extend the `BaseCommand` class which provides:

- **Logging Methods**: `info()`, `success()`, `error()`, `warn()`
- **Progress Tracking**: `progress()` with visual progress bar
- **Timing**: `start_timer()`, `get_elapsed_time()`
- **Error Handling**: Automatic exception catching and reporting

### Command Runner (`CommandRunner`)

The command runner manages and dispatches commands:

- **Registration**: Auto-registers available commands
- **Execution**: Handles command execution with error handling
- **CLI Interface**: Provides command-line interface

## Adding New Commands

1. **Create Command Class:**

```python
from app.commands.base_command import BaseCommand

class MyNewCommand(BaseCommand):
    signature = "my:command"
    description = "Description of what this command does"

    async def handle(self, **kwargs):
        self.info("Starting my command...")

        # Your command logic here

        return {
            "success": True,
            "processed": 100
        }
```

2. **Register Command:**

Add to `CommandRunner.__init__()`:

```python
self.commands = {
    "my:command": MyNewCommand,
    # ... other commands
}
```

3. **Use Command:**

```bash
uv run python console.py my:command
```

## Examples

### Basic Usage

```bash
# List all available commands
uv run python console.py list

# Run populate command
uv run python console.py populate:leads-score
```

### Programmatic Usage

```python
from app.commands.command_runner import command_runner

# Run synchronously
result = command_runner.run_command_sync(
    "populate:leads-score",
    batch_size=50,
    dry_run=True
)

# Run asynchronously
result = await command_runner.run_command(
    "populate:leads-score",
    batch_size=50
)
```

## Output Format

Commands return structured results:

```python
{
    "success": True,
    "elapsed_time": "45.2s",
    "total_processed": 1500,
    "updated": 1450,
    "skipped": 30,
    "errors": 20,
    "dry_run": False
}
```

## Error Handling

- **Graceful Degradation**: Individual post errors don't stop the entire process
- **Detailed Logging**: All errors are logged with context
- **Progress Continuation**: Processing continues after errors
- **Final Statistics**: Complete summary of successes, skips, and errors

"""
Base Command Class - Similar to Laravel's Command base class.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any
import time


class BaseCommand(ABC):
    """Base class for all console commands."""
    
    # Command signature (to be overridden by subclasses)
    signature: str = ""
    description: str = ""
    
    def __init__(self):
        self.start_time = None
        self.processed_count = 0
        
    def info(self, message: str):
        """Print info message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ℹ️  {message}")
    
    def success(self, message: str):
        """Print success message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ✅ {message}")
    
    def error(self, message: str):
        """Print error message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ❌ {message}")
    
    def warn(self, message: str):
        """Print warning message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ⚠️  {message}")
    
    def progress(self, current: int, total: int, message: str = ""):
        """Show progress information."""
        percentage = (current / total * 100) if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        rate = current / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\r🔄 [{bar}] {percentage:.1f}% ({current}/{total}) {message} | Rate: {rate:.1f}/sec", end='', flush=True)
        
        if current == total:
            print()  # New line when complete
    
    def start_timer(self):
        """Start timing the command execution."""
        self.start_time = time.time()
    
    def get_elapsed_time(self) -> str:
        """Get elapsed time as formatted string."""
        if not self.start_time:
            return "0s"
        
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        elif elapsed < 3600:
            return f"{elapsed/60:.1f}m"
        else:
            return f"{elapsed/3600:.1f}h"
    
    @abstractmethod
    async def handle(self, **kwargs) -> Dict[str, Any]:
        """
        Handle the command execution.
        
        Returns:
            Dict with command execution results
        """
        pass
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the command with timing and error handling.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Dict with execution results
        """
        self.info(f"Starting command: {self.signature}")
        self.info(f"Description: {self.description}")
        self.start_timer()
        
        try:
            result = await self.handle(**kwargs)
            
            self.success(f"Command completed successfully in {self.get_elapsed_time()}")
            return {
                "success": True,
                "elapsed_time": self.get_elapsed_time(),
                "processed_count": self.processed_count,
                **result
            }
            
        except Exception as e:
            self.error(f"Command failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": self.get_elapsed_time(),
                "processed_count": self.processed_count
            }

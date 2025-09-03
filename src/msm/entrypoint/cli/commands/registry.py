"""Command registry for managing CLI commands."""

from typing import Dict, List, Optional

from .base import BaseCommand


class CommandRegistry:
    """Registry for managing CLI commands."""

    def __init__(self) -> None:
        self._commands: Dict[str, BaseCommand] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in commands."""
        try:
            from .core import ExitCommand, HelpCommand, ListCommand, StatusCommand
            from .graph import (
                DrawCommand,
                InfoCommand,
                LoadCommand,
                ReloadCommand,
                TaskCommand,
                UnloadCommand,
                UseCommand,
            )
            from .mcp import MCPCommand
            from .model import ModelCommand
            from .tools import ToolsCommand

            commands = [
                HelpCommand(),
                StatusCommand(),
                ExitCommand(),
                ListCommand(),
                LoadCommand(),
                InfoCommand(),
                UseCommand(),
                TaskCommand(),
                UnloadCommand(),
                ReloadCommand(),
                DrawCommand(),
                MCPCommand(),
                ModelCommand(),
                ToolsCommand(),
            ]

            for cmd in commands:
                self.register(cmd)
        except ImportError as e:
            # Handle import errors gracefully during development
            print(f"Warning: Failed to import some commands: {e}")

    def register(self, command: BaseCommand) -> None:
        """Register a command."""
        self._commands[command.definition.name] = command

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get command by name."""
        return self._commands.get(name.lower())

    def get_all_commands(self) -> Dict[str, BaseCommand]:
        """Get all registered commands."""
        return self._commands.copy()

    def get_command_names(self) -> List[str]:
        """Get list of command names for completion."""
        return list(self._commands.keys())

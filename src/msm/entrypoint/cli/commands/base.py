"""Base classes for CLI commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class ArgumentType(Enum):
    """Types of command arguments for validation and completion."""

    STRING = "string"
    FILE_PATH = "file_path"
    GRAPH_ID = "graph_id"
    FLOAT = "float"
    INT = "int"


@dataclass
class CommandArgument:
    """Definition of a command argument."""

    name: str
    type: ArgumentType
    required: bool = True
    description: str = ""
    choices: Optional[List[str]] = None
    default: Any = None


@dataclass
class CommandDefinition:
    """Metadata definition for a command."""

    name: str
    description: str
    arguments: List[CommandArgument]
    examples: List[str]


class BaseCommand(ABC):
    """Base class for all CLI commands."""

    @property
    @abstractmethod
    def definition(self) -> CommandDefinition:
        """Command definition with metadata."""
        pass

    @abstractmethod
    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Execute the command. Return False to exit CLI."""
        pass

    def validate_args(self, args: List[str]) -> Dict[str, Any]:
        """Validate and parse arguments."""
        parsed = {}
        definition = self.definition

        # Check required argument count
        required_count = sum(1 for arg in definition.arguments if arg.required)
        if len(args) < required_count:
            raise ValueError(f"Usage: {self.get_usage()}")

        # Parse each argument
        for i, arg_def in enumerate(definition.arguments):
            if i < len(args):
                value = self._parse_argument(args[i], arg_def)
                parsed[arg_def.name] = value
            elif arg_def.default is not None:
                parsed[arg_def.name] = arg_def.default
            elif not arg_def.required:
                parsed[arg_def.name] = None

        return parsed

    def _parse_argument(self, value: str, arg_def: CommandArgument) -> Any:
        """Parse a single argument based on its type."""
        if arg_def.type == ArgumentType.FLOAT:
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"'{value}' is not a valid float for {arg_def.name}")
        elif arg_def.type == ArgumentType.INT:
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"'{value}' is not a valid integer for {arg_def.name}")
        elif arg_def.choices and value not in arg_def.choices:
            raise ValueError(f"'{value}' must be one of: {', '.join(arg_def.choices)}")
        return value

    def get_usage(self) -> str:
        """Generate usage string."""
        parts = [self.definition.name]
        for arg in self.definition.arguments:
            if arg.required:
                parts.append(f"<{arg.name}>")
            else:
                parts.append(f"[{arg.name}]")
        return " ".join(parts)

    def _print_usage_error(self, cli: "FenixaosCLI") -> None:
        """Print usage error message."""
        cli.console.print(f"[red]Usage: {self.get_usage()}[/red]")

    def _print_success(self, cli: "FenixaosCLI", message: str) -> None:
        """Print success message."""
        cli.console.print(f"[green]✓ {message}[/green]")

    def _print_error(self, cli: "FenixaosCLI", message: str) -> None:
        """Print error message."""
        cli.console.print(f"[red]Error: {message}[/red]")

    async def _handle_backend_response(
        self, cli: "FenixaosCLI", result: Dict[str, Any], success_key: str = "message"
    ) -> Optional[Dict[str, Any]]:
        """Handle common backend response patterns."""
        if result.get("status") == "success":
            self._print_success(cli, result.get(success_key, "Operation completed"))
            data = result.get("data")
            return data if data is not None else {}
        else:
            self._print_error(cli, result.get("detail", "Unknown error"))
            return None

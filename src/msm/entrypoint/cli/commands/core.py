"""Core CLI commands (help, status, exit, list)."""

from typing import TYPE_CHECKING, List

from rich.table import Table

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class HelpCommand(BaseCommand):
    """Show help for commands."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="help",
            description="Show available commands or help for a specific command",
            arguments=[
                CommandArgument(
                    "command",
                    ArgumentType.STRING,
                    required=False,
                    description="Command to show help for",
                )
            ],
            examples=["help", "help load"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if args:
            # Show help for specific command
            command_name = args[0].lower()
            command = cli.command_registry.get_command(command_name)
            if command:
                definition = command.definition
                cli.console.print(f"[cyan]Usage:[/cyan] {command.get_usage()}")
                cli.console.print(f"[cyan]Description:[/cyan] {definition.description}")
                if definition.examples:
                    cli.console.print("[cyan]Examples:[/cyan]")
                    for example in definition.examples:
                        cli.console.print(f"  {example}")
            else:
                self._print_error(cli, f"Unknown command: {command_name}")
        else:
            # Show all commands
            table = Table(title="Available Commands")
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="white")

            for name, command in cli.command_registry.get_all_commands().items():
                table.add_row(name, command.definition.description)

            cli.console.print(table)
            cli.console.print(
                "\nType 'help <command>' for detailed help on a specific command."
            )

        return True


class StatusCommand(BaseCommand):
    """Show CLI status."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="status",
            description="Show current CLI status and configuration",
            arguments=[],
            examples=["status"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        table = Table(title="CLI Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Backend URL", cli.client.base_url)
        table.add_row("Current Graph", cli.current_graph_id or "None")
        table.add_row("Loaded Graphs", str(len(cli.loaded_graphs)))

        cli.console.print(table)
        return True


class ExitCommand(BaseCommand):
    """Exit the CLI."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="exit",
            description="Exit the CLI application",
            arguments=[],
            examples=["exit"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        return False  # Signal to exit the CLI


class ListCommand(BaseCommand):
    """List all loaded graphs."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="list",
            description="List all loaded graphs",
            arguments=[],
            examples=["list"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        data = await cli.backend_operations.list_graphs()
        if data:
            graphs = data.get("loaded_graphs", [])
            if not graphs:
                cli.console.print("[yellow]No graphs loaded[/yellow]")
                return True

            table = Table(title="Loaded Graphs")
            table.add_column("Graph ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Nodes", style="green")
            table.add_column("Tools", style="blue")
            table.add_column("Current", style="yellow")

            for graph in graphs:
                current = "✓" if graph["graph_id"] == cli.current_graph_id else ""
                table.add_row(
                    graph["graph_id"],
                    graph["name"],
                    str(graph["node_count"]),
                    str(graph["tool_count"]),
                    current,
                )

            cli.console.print(table)

        return True

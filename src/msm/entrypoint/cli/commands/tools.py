"""Tools management CLI commands."""

from typing import TYPE_CHECKING, List

from rich.table import Table

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class ToolsCommand(BaseCommand):
    """Tools management command with subcommands."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="tools",
            description="Manage available tools",
            arguments=[
                CommandArgument(
                    "subcommand",
                    ArgumentType.STRING,
                    choices=["list", "reload"],
                    description="Tools operation",
                )
            ],
            examples=["tools list", "tools reload"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if not args:
            self._print_usage_error(cli)
            return True

        subcommand = args[0].lower()
        subargs = args[1:]

        if subcommand == "list":
            return await self._handle_list(subargs, cli)
        elif subcommand == "reload":
            return await self._handle_reload(subargs, cli)
        else:
            self._print_error(cli, f"Unknown tools subcommand: {subcommand}")
            cli.console.print("Available subcommands: list, reload")
            return True

    async def _handle_list(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle tools list subcommand."""
        data = await cli.backend_operations.list_tools()
        if data:
            tools = data.get("tools", [])
            if not tools:
                cli.console.print("[yellow]No tools available[/yellow]")
                return True

            table = Table(title="Available Tools")
            table.add_column("Tool Name", style="cyan")
            table.add_column("Status", style="green")

            for tool_name in sorted(tools):
                table.add_row(tool_name, "Available")

            cli.console.print(table)
            cli.console.print(f"[blue]Total: {len(tools)} tools[/blue]")

        return True

    async def _handle_reload(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle tools reload subcommand."""
        cli.console.print("Reloading tools...")
        data = await cli.backend_operations.reload_tools()

        if data:
            table = Table(title="Tool Reload Summary")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="white")
            table.add_column("Tools", style="green")

            if data.get("added"):
                table.add_row(
                    "Added", str(len(data["added"])), ", ".join(data["added"])
                )

            if data.get("removed"):
                table.add_row(
                    "Removed", str(len(data["removed"])), ", ".join(data["removed"])
                )

            table.add_row(
                "Total",
                str(data.get("total", 0)),
                ", ".join(data.get("new_tools", [])),
            )

            cli.console.print(table)

        return True

"""Graph-related CLI commands (load, info, use, task, unload, reload)."""

from typing import TYPE_CHECKING, List

from rich.table import Table

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class LoadCommand(BaseCommand):
    """Load a graph from YAML file."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="load",
            description="Load a graph from YAML file",
            arguments=[
                CommandArgument(
                    "file_path", ArgumentType.FILE_PATH, description="Path to YAML file"
                ),
                CommandArgument(
                    "graph_id",
                    ArgumentType.STRING,
                    required=False,
                    description="Graph ID (defaults to filename)",
                ),
            ],
            examples=["load graph.yaml", "load graph.yaml my_graph"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        try:
            parsed = self.validate_args(args)
        except ValueError as e:
            cli.console.print(f"[red]{e}[/red]")
            return True

        file_path = parsed["file_path"]
        graph_id = parsed["graph_id"]

        data = await cli.backend_operations.load_graph(file_path, graph_id)
        if data:
            cli.loaded_graphs[
                graph_id or file_path.split("/")[-1].replace(".yaml", "")
            ] = data

            # Set as current graph if none is set
            if not cli.current_graph_id:
                cli.current_graph_id = graph_id or file_path.split("/")[-1].replace(
                    ".yaml", ""
                )
                cli.console.print(
                    f"[blue]Current graph set to '{cli.current_graph_id}'[/blue]"
                )

        return True


class InfoCommand(BaseCommand):
    """Show information about a graph."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="info",
            description="Show detailed information about a graph",
            arguments=[
                CommandArgument(
                    "graph_id",
                    ArgumentType.GRAPH_ID,
                    required=False,
                    description="Graph ID (defaults to current graph)",
                )
            ],
            examples=["info", "info my_graph"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        graph_id = args[0] if args else cli.current_graph_id

        if not graph_id:
            self._print_error(cli, "No graph specified and no current graph set")
            return True

        data = await cli.backend_operations.get_graph_info(graph_id)
        if data:
            table = Table(title=f"Graph Info: {graph_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Name", data.get("name", "N/A"))
            table.add_row("Description", data.get("description", "N/A"))
            table.add_row("File Path", data.get("file_path", "N/A"))
            table.add_row("Loaded At", data.get("loaded_at", "N/A"))
            table.add_row("Node Count", str(data.get("node_count", 0)))
            table.add_row("Tool Count", str(data.get("tool_count", 0)))

            cli.console.print(table)

            # Show node types if available
            if data.get("node_types"):
                node_table = Table(title="Node Types")
                node_table.add_column("Type", style="cyan")
                node_table.add_column("Count", style="white")

                for node_type, count in data["node_types"].items():
                    node_table.add_row(node_type, str(count))

                cli.console.print(node_table)

        return True


class UseCommand(BaseCommand):
    """Set current graph for task execution."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="use",
            description="Set the current graph for task execution",
            arguments=[
                CommandArgument(
                    "graph_id", ArgumentType.GRAPH_ID, description="Graph ID to use"
                )
            ],
            examples=["use my_graph"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        try:
            parsed = self.validate_args(args)
        except ValueError as e:
            cli.console.print(f"[red]{e}[/red]")
            return True

        graph_id = parsed["graph_id"]

        # Check if graph exists by listing graphs
        data = await cli.backend_operations.list_graphs()
        if data:
            graph_ids = [g["graph_id"] for g in data.get("loaded_graphs", [])]
            if graph_id not in graph_ids:
                self._print_error(cli, f"Graph '{graph_id}' not found")
                return True

            cli.current_graph_id = graph_id
            self._print_success(cli, f"Current graph set to '{graph_id}'")

        return True


class TaskCommand(BaseCommand):
    """Execute a task using the current graph."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="task",
            description="Execute a task using the current graph",
            arguments=[
                CommandArgument(
                    "description", ArgumentType.STRING, description="Task description"
                )
            ],
            examples=["task 'analyze the data'", "task 'generate a report'"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if not args:
            self._print_usage_error(cli)
            return True

        if not cli.current_graph_id:
            self._print_error(cli, "No current graph set. Use 'use <graph_id>' first.")
            return True

        task = " ".join(args)

        cli.console.print(f"Executing task: [cyan]{task}[/cyan]")
        cli.console.print(f"Using graph: [blue]{cli.current_graph_id}[/blue]")

        with cli.console.status("[bold green]Processing..."):
            data = await cli.backend_operations.execute_task(task, cli.current_graph_id)

        if data:
            task_result = data.get("task_result", {})
            messages = task_result.get("messages", [])
            duration = data.get("duration", 0)

            cli.console.print(f"[green]✓ Task completed in {duration:.2f}s[/green]")

            # Display messages from the task execution
            for msg in messages:
                if msg.get("source") == "user":
                    cli.console.print(f"[cyan]User:[/cyan] {msg.get('content', '')}")
                else:
                    source = msg.get("source", "system")
                    content = msg.get("content", "")
                    cli.console.print(f"[yellow]{source}:[/yellow] {content}")

        return True


class UnloadCommand(BaseCommand):
    """Unload a graph from memory."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="unload",
            description="Unload a graph from memory",
            arguments=[
                CommandArgument(
                    "graph_id", ArgumentType.GRAPH_ID, description="Graph ID to unload"
                )
            ],
            examples=["unload my_graph"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        try:
            parsed = self.validate_args(args)
        except ValueError as e:
            cli.console.print(f"[red]{e}[/red]")
            return True

        graph_id = parsed["graph_id"]

        data = await cli.backend_operations.unload_graph(graph_id)
        if data:
            # Clear current graph if it's the one being unloaded
            if cli.current_graph_id == graph_id:
                cli.current_graph_id = None
                cli.console.print("[blue]Current graph cleared[/blue]")

            # Remove from loaded graphs
            cli.loaded_graphs.pop(graph_id, None)

        return True


class ReloadCommand(BaseCommand):
    """Reload a graph from its original file."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="reload",
            description="Reload a graph from its original file",
            arguments=[
                CommandArgument(
                    "graph_id", ArgumentType.GRAPH_ID, description="Graph ID to reload"
                )
            ],
            examples=["reload my_graph"],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        try:
            parsed = self.validate_args(args)
        except ValueError as e:
            cli.console.print(f"[red]{e}[/red]")
            return True

        graph_id = parsed["graph_id"]

        data = await cli.backend_operations.reload_graph(graph_id)
        if data:
            # Update loaded graphs with new data
            cli.loaded_graphs[graph_id] = data

        return True


class DrawCommand(BaseCommand):
    """Draw a graph as PNG image."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="draw",
            description="Draw a graph as PNG image",
            arguments=[
                CommandArgument(
                    "output_file",
                    ArgumentType.FILE_PATH,
                    description="Output PNG file path",
                ),
                CommandArgument(
                    "graph_id",
                    ArgumentType.GRAPH_ID,
                    required=False,
                    description="Graph ID (defaults to current graph)",
                ),
            ],
            examples=[
                "draw graph.png",
                "draw output.png my_graph",
            ],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if not args:
            self._print_error(cli, "Output file path is required")
            self._print_usage_error(cli)
            return True

        output_file = args[0]
        graph_id = args[1] if len(args) > 1 else cli.current_graph_id

        if not graph_id:
            self._print_error(cli, "No graph specified and no current graph set")
            return True

        cli.console.print(f"Drawing graph: [cyan]{graph_id}[/cyan]")
        cli.console.print(f"Output: [blue]{output_file}[/blue]")

        with cli.console.status("[bold green]Generating PNG image..."):
            data = await cli.backend_operations.draw_graph(
                graph_id=graph_id,
                output_file=output_file,
            )

        if data:
            cli.console.print("[green]✓ Graph drawing completed[/green]")

        return True

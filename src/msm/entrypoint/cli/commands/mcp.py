"""MCP server management CLI commands."""

from typing import TYPE_CHECKING, Any, Dict, List

from rich.panel import Panel
from rich.table import Table

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class MCPCommand(BaseCommand):
    """MCP server management command with subcommands."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="mcp",
            description="Manage MCP (Model Context Protocol) servers",
            arguments=[
                CommandArgument(
                    "subcommand",
                    ArgumentType.STRING,
                    choices=["add", "list", "remove"],
                    description="MCP operation",
                )
            ],
            examples=[
                "mcp list",
                'mcp add myserver stdio --command python --args server.py --description "My server"',
                'mcp add webserver streamable_http --url http://localhost:8000/mcp --description "Web server"',
                'mcp add sseserver sse --url http://localhost:8001/sse --description "SSE server"',
                'mcp add wsserver websocket --url ws://localhost:8002/ws --description "WebSocket server"',
                "mcp remove myserver",
            ],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if not args:
            self._print_usage_error(cli)
            return True

        subcommand = args[0].lower()
        subargs = args[1:]

        if subcommand == "add":
            return await self._handle_add(subargs, cli)
        elif subcommand == "list":
            return await self._handle_list(subargs, cli)
        elif subcommand == "remove":
            return await self._handle_remove(subargs, cli)
        else:
            self._print_error(cli, f"Unknown mcp subcommand: {subcommand}")
            cli.console.print("Available subcommands: add, list, remove")
            return True

    def _print_usage_error(self, cli: "FenixaosCLI") -> None:
        """Print usage information."""
        cli.console.print("[red]Usage: mcp <subcommand> [options][/red]")
        cli.console.print("Available subcommands:")
        cli.console.print("  add     - Add a new MCP server")
        cli.console.print("  list    - List all configured MCP servers")
        cli.console.print("  remove  - Remove an MCP server")

    def _print_error(self, cli: "FenixaosCLI", message: str) -> None:
        """Print an error message."""
        cli.console.print(f"[red]Error: {message}[/red]")

    async def _handle_add(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle mcp add subcommand."""
        if len(args) < 2:
            self._print_error(cli, "Insufficient arguments for add command")
            self._print_add_usage(cli)
            return True

        name = args[0]
        transport = args[1]

        # Parse additional arguments
        options = self._parse_options(args[2:])

        # Validate transport type
        valid_transports = ["stdio", "streamable_http", "sse", "websocket"]
        if transport not in valid_transports:
            self._print_error(cli, f"Invalid transport type: {transport}")
            cli.console.print(f"Valid transports: {', '.join(valid_transports)}")
            return True

        # Validate required parameters for each transport type
        if transport == "stdio":
            if "command" not in options:
                self._print_error(cli, "stdio transport requires --command parameter")
                return True
            if "args" not in options:
                self._print_error(cli, "stdio transport requires --args parameter")
                self._print_error(
                    cli,
                    "Usage: mcp add <name> stdio --command <cmd> --args <arg1> <arg2> ...",
                )
                return True
        elif transport in ["streamable_http", "sse", "websocket"]:
            if "url" not in options:
                self._print_error(
                    cli, f"{transport} transport requires --url parameter"
                )
                return True

        try:
            cli.console.print(
                f"Adding MCP server '{name}' with transport '{transport}'..."
            )

            # Prepare request parameters
            request_params = {
                "name": name,
                "transport": transport,
                "description": options.get("description"),
            }

            if transport == "stdio":
                request_params["command"] = options["command"]
                request_params["args"] = options["args"]
                if "env" in options:
                    request_params["env"] = options["env"]
                if "cwd" in options:
                    request_params["cwd"] = options["cwd"]
            else:
                request_params["url"] = options["url"]
                if "headers" in options:
                    request_params["headers"] = options["headers"]

            data = await cli.backend_operations.add_mcp_server(**request_params)  # type: ignore

            if data:
                # Display server details
                self._display_server_details(cli, data)
            else:
                self._print_error(cli, "Failed to add MCP server")

        except Exception as e:
            self._print_error(cli, f"Failed to add MCP server: {str(e)}")

        return True

    async def _handle_list(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle mcp list subcommand."""
        try:
            cli.console.print("Listing MCP servers...")
            data = await cli.backend_operations.list_mcp_servers()

            if data:
                servers = data.get("servers", [])
                count = data.get("count", 0)

                if count == 0:
                    cli.console.print("[yellow]No MCP servers configured[/yellow]")
                    return True

                # Create table for servers
                table = Table(title=f"Configured MCP Servers ({count})")
                table.add_column("Name", style="cyan", no_wrap=True)
                table.add_column("Transport", style="magenta")
                table.add_column("Configuration", style="white")
                table.add_column("Description", style="dim")

                for server in servers:
                    name = server.get("name", "Unknown")
                    transport = server.get("transport", "Unknown")
                    config = server.get("config", {})
                    description = server.get("description") or "No description"

                    # Format configuration based on transport type
                    config_text = self._format_config_for_display(transport, config)

                    table.add_row(name, transport, config_text, description)

                cli.console.print(table)
            else:
                self._print_error(cli, "Failed to list MCP servers")

        except Exception as e:
            self._print_error(cli, f"Failed to list MCP servers: {str(e)}")

        return True

    async def _handle_remove(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle mcp remove subcommand."""
        if not args:
            self._print_error(cli, "Server name is required for remove command")
            cli.console.print("[red]Usage: mcp remove <server_name>[/red]")
            return True

        server_name = args[0]

        try:
            cli.console.print(f"Removing MCP server '{server_name}'...")
            data = await cli.backend_operations.remove_mcp_server(server_name)

            if data:
                pass  # Success message already printed by backend_operations
            else:
                self._print_error(cli, "Failed to remove MCP server")

        except Exception as e:
            self._print_error(cli, f"Failed to remove MCP server: {str(e)}")

        return True

    def _parse_options(self, args: List[str]) -> Dict[str, Any]:
        """Parse command line options and arguments."""
        options: Dict[str, Any] = {}
        i = 0

        while i < len(args):
            arg = args[i]

            if arg == "--description":
                if i + 1 < len(args):
                    # Handle descriptions - could be single word or quoted multi-word
                    desc_parts = []
                    j = i + 1

                    # If next arg starts with quote, collect until closing quote
                    if j < len(args) and (
                        args[j].startswith('"') or args[j].startswith("'")
                    ):
                        quote_char = args[j][0]
                        # Remove opening quote
                        first_part = args[j][1:]

                        if first_part.endswith(quote_char):
                            # Single argument with quotes: "word" or 'word'
                            options["description"] = first_part[:-1]
                            i = j + 1
                        else:
                            # Multi-word quoted string: "word1 word2"
                            desc_parts.append(first_part)
                            j += 1
                            while j < len(args):
                                if args[j].endswith(quote_char):
                                    # Found closing quote
                                    desc_parts.append(args[j][:-1])
                                    break
                                else:
                                    desc_parts.append(args[j])
                                j += 1
                            options["description"] = " ".join(desc_parts)
                            i = j + 1
                    else:
                        # Single word without quotes
                        options["description"] = args[j]
                        i = j + 1
                else:
                    i += 1
            elif arg == "--command":
                if i + 1 < len(args):
                    options["command"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif arg == "--args":
                # Collect all arguments until next -- parameter or end
                cmd_args = []
                j = i + 1
                while j < len(args) and not args[j].startswith("--"):
                    cmd_args.append(args[j])
                    j += 1
                options["args"] = cmd_args
                i = j
            elif arg == "--url":
                if i + 1 < len(args):
                    options["url"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif arg == "--cwd":
                if i + 1 < len(args):
                    options["cwd"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif arg == "--env":
                # Parse environment variables (format: KEY=VALUE KEY2=VALUE2 ...)
                env_vars = {}
                j = i + 1
                while j < len(args) and not args[j].startswith("--"):
                    if "=" in args[j]:
                        key, value = args[j].split("=", 1)
                        env_vars[key] = value
                    j += 1
                options["env"] = env_vars
                i = j
            elif arg == "--headers":
                # Parse HTTP headers (format: KEY=VALUE KEY2=VALUE2 ...)
                headers = {}
                j = i + 1
                while j < len(args) and not args[j].startswith("--"):
                    if "=" in args[j]:
                        key, value = args[j].split("=", 1)
                        headers[key] = value
                    j += 1
                options["headers"] = headers
                i = j
            else:
                # Skip unknown arguments
                i += 1

        return options

    def _print_add_usage(self, cli: "FenixaosCLI") -> None:
        """Print usage information for add command."""
        usage_panel = Panel.fit(
            "[bold]MCP Add Command Usage[/bold]\n\n"
            "[cyan]stdio transport:[/cyan]\n"
            '  mcp add <name> stdio --command <command> --args <arg1> <arg2> ... [--description "<desc>"] [--cwd <path>] [--env KEY=VALUE ...]\n\n'
            "[cyan]streamable_http transport:[/cyan]\n"
            '  mcp add <name> streamable_http --url <url> [--description "<desc>"] [--headers KEY=VALUE ...]\n\n'
            "[cyan]sse transport:[/cyan]\n"
            '  mcp add <name> sse --url <url> [--description "<desc>"] [--headers KEY=VALUE ...]\n\n'
            "[cyan]websocket transport:[/cyan]\n"
            '  mcp add <name> websocket --url <url> [--description "<desc>"]\n\n'
            "[bold]Examples:[/bold]\n"
            '  mcp add myserver stdio --command python --args server.py --description "My MCP server"\n'
            '  mcp add webserver streamable_http --url http://localhost:8000/mcp --description "Web server"\n'
            '  mcp add sseserver sse --url http://localhost:8001/sse --headers Authorization="Bearer token"\n'
            "  mcp add wsserver websocket --url ws://localhost:8002/ws\n\n"
            "[bold]Notes:[/bold]\n"
            "  • All parameters must be specified with -- prefix\n"
            "  • Use quotes around multi-word descriptions\n"
            "  • Multiple args can be specified after --args\n"
            "  • Environment variables: --env KEY1=VALUE1 KEY2=VALUE2\n"
            "  • HTTP headers: --headers KEY1=VALUE1 KEY2=VALUE2"
        )
        cli.console.print(usage_panel)

    def _format_config_for_display(self, transport: str, config: Dict[str, Any]) -> str:
        """Format configuration for table display."""
        if transport == "stdio":
            command = str(config.get("command", ""))
            args = config.get("args", [])
            if isinstance(args, list):
                return f"{command} {' '.join(str(arg) for arg in args)}"
            else:
                return f"{command} {str(args)}"
        elif transport in ["streamable_http", "sse", "websocket"]:
            return str(config.get("url", ""))
        else:
            return str(config)

    def _display_server_details(
        self, cli: "FenixaosCLI", server_data: Dict[str, Any]
    ) -> None:
        """Display server configuration details."""
        if not server_data:
            return

        table = Table(title="Server Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Name", server_data.get("name", "Unknown"))
        table.add_row("Transport", server_data.get("transport", "Unknown"))
        table.add_row("Description", server_data.get("description") or "No description")

        config = server_data.get("config", {})
        for key, value in config.items():
            if key not in ["transport", "description"]:
                if isinstance(value, list):
                    value = " ".join(str(v) for v in value)
                elif isinstance(value, dict):
                    value = ", ".join(f"{k}={v}" for k, v in value.items())
                table.add_row(key.capitalize(), str(value))

        cli.console.print(table)

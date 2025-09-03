import argparse
import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .backend import BackendOperations
from .commands import CommandRegistry
from .completer import SystematicCompleter

# Set up logger
logger = logging.getLogger(__name__)


class YamlBackendClient:
    """Client for communicating with the YAML backend server."""

    def __init__(self, base_url: str = "http://127.0.0.1:9997"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)

    async def health_check(self) -> bool:
        """Check if the backend server is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def load_graph(self, file_path: str, graph_id: str) -> Dict[str, Any]:
        """Load a graph from a YAML file."""
        response = await self.client.post(
            f"{self.base_url}/api/graph/load",
            json={"file_path": file_path, "graph_id": graph_id},
        )
        result: Dict[str, Any] = response.json()
        return result

    async def execute_task(self, task: str, graph_id: str) -> Dict[str, Any]:
        """Execute a task using a loaded graph."""
        response = await self.client.post(
            f"{self.base_url}/api/task/execute",
            json={"task": task, "graph_id": graph_id},
        )
        result: Dict[str, Any] = response.json()
        return result

    async def list_graphs(self) -> Dict[str, Any]:
        """List all loaded graphs."""
        response = await self.client.get(f"{self.base_url}/api/graphs")
        result: Dict[str, Any] = response.json()
        return result

    async def get_graph_info(self, graph_id: str) -> Dict[str, Any]:
        """Get detailed information about a graph."""
        response = await self.client.get(f"{self.base_url}/api/graph/{graph_id}/info")
        result: Dict[str, Any] = response.json()
        return result

    async def unload_graph(self, graph_id: str) -> Dict[str, Any]:
        """Unload a graph from memory."""
        response = await self.client.delete(f"{self.base_url}/api/graph/{graph_id}")
        result: Dict[str, Any] = response.json()
        return result

    async def reload_graph(self, graph_id: str) -> Dict[str, Any]:
        """Reload a graph from its original file."""
        response = await self.client.post(
            f"{self.base_url}/api/graph/reload/{graph_id}"
        )
        result: Dict[str, Any] = response.json()
        return result

    async def reload_tools(self) -> Dict[str, Any]:
        """Reload tools."""
        response = await self.client.post(f"{self.base_url}/api/tools/reload")
        result: Dict[str, Any] = response.json()
        return result

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        response = await self.client.get(f"{self.base_url}/api/tools")
        result: Dict[str, Any] = response.json()
        return result

    async def register_model(
        self,
        model_id: str,
        model_type: str,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Register a new model."""
        response = await self.client.post(
            f"{self.base_url}/api/models/register",
            json={
                "model_id": model_id,
                "model_type": model_type,
                "model_name": model_name,
                "api_key": api_key,
                "base_url": base_url,
                "temperature": temperature,
            },
        )
        result: Dict[str, Any] = response.json()
        return result

    async def list_models(self) -> Dict[str, Any]:
        """List all registered models."""
        response = await self.client.get(f"{self.base_url}/api/models")
        result: Dict[str, Any] = response.json()
        return result

    async def delete_model(self, model_id: str) -> Dict[str, Any]:
        """Delete a registered model."""
        response = await self.client.delete(f"{self.base_url}/api/models/{model_id}")
        result: Dict[str, Any] = response.json()
        return result

    async def test_models(self, model_ids: list[str] = []) -> Dict[str, Any]:
        """Test model(s) for usability."""
        request_data = {}
        request_data["model_ids"] = model_ids

        response = await self.client.post(
            f"{self.base_url}/api/models/test",
            json=request_data,
        )
        result: Dict[str, Any] = response.json()
        return result

    async def add_mcp_server(
        self,
        name: str,
        transport: str,
        description: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        url: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a new MCP server configuration."""
        request_data: Dict[str, Any] = {
            "name": name,
            "transport": transport,
        }
        if description is not None:
            request_data["description"] = description
        if command is not None:
            request_data["command"] = command
        if args is not None:
            request_data["args"] = args
        if url is not None:
            request_data["url"] = url
        if env is not None:
            request_data["env"] = env
        if cwd is not None:
            request_data["cwd"] = cwd
        if headers is not None:
            request_data["headers"] = headers

        response = await self.client.post(
            f"{self.base_url}/api/mcp/servers",
            json=request_data,
        )
        result: Dict[str, Any] = response.json()
        return result

    async def list_mcp_servers(self) -> Dict[str, Any]:
        """List all configured MCP servers."""
        response = await self.client.get(f"{self.base_url}/api/mcp/servers")
        result: Dict[str, Any] = response.json()
        return result

    async def remove_mcp_server(self, server_name: str) -> Dict[str, Any]:
        """Remove an MCP server configuration."""
        response = await self.client.delete(
            f"{self.base_url}/api/mcp/servers/{server_name}"
        )
        result: Dict[str, Any] = response.json()
        return result

    async def draw_graph(
        self,
        graph_id: str,
        with_styles: bool = True,
        curve_style: str = "linear",
        wrap_label_n_words: int = 9,
    ) -> bytes:
        """Draw a graph as PNG image."""
        response = await self.client.post(
            f"{self.base_url}/api/graph/draw",
            json={
                "graph_id": graph_id,
                "with_styles": with_styles,
                "curve_style": curve_style,
                "wrap_label_n_words": wrap_label_n_words,
            },
        )

        return response.content

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


class FenixaosCLI:
    """Interactive CLI for FenixAOS with systematic command architecture."""

    def __init__(self, base_url: str = "http://127.0.0.1:9997") -> None:
        self.console = Console()
        self.client = YamlBackendClient(base_url=base_url)
        self.current_graph_id: Optional[str] = None
        self.loaded_graphs: Dict[str, Dict[str, Any]] = {}

        # Initialize new command system
        self.command_registry = CommandRegistry()
        self.backend_operations = BackendOperations(self.client, self.console)

        self.session: "PromptSession[str]" = PromptSession(
            completer=SystematicCompleter(self), complete_while_typing=True
        )

    def print_banner(self) -> None:
        """Print the CLI banner."""
        banner = Text("FenixAOS CLI", style="bold blue")
        self.console.print(Panel(banner, title="Welcome", expand=False))
        self.console.print("Type 'help' for available commands or 'exit' to quit.\n")

    async def check_backend(self) -> bool:
        """Check if backend is available."""
        if not await self.client.health_check():
            self.console.print(
                f"[red]Error: Backend server is not available at {self.client.base_url}[/red]"
            )
            self.console.print("Please start the YAML server first.")
            return False
        return True

    async def process_command(self, command_line: str) -> Optional[bool]:
        """Process a command using the systematic command registry."""
        parts = command_line.strip().split()
        if not parts:
            return None

        command_name = parts[0].lower()
        args = parts[1:]

        command = self.command_registry.get_command(command_name)
        if not command:
            self.console.print(f"[red]Unknown command: {command_name}[/red]")
            self.console.print("Type 'help' for available commands.")
            return True

        try:
            return await command.execute(args, self)
        except Exception as e:
            self.console.print(f"[red]Error executing command: {e}[/red]")
            logger.exception(f"Error in command {command_name}")
            return True

    async def run(self) -> None:
        """Run the CLI REPL."""
        self.print_banner()

        if not await self.check_backend():
            return

        self.console.print("[green]✓ Backend server is available[/green]\n")

        try:
            while True:
                try:
                    prompt_text = "fenixaos"
                    if self.current_graph_id:
                        prompt_text += f" ({self.current_graph_id})"
                    prompt_text += "> "

                    command_line = await self.session.prompt_async(prompt_text)
                    command_line = command_line.strip()

                    if not command_line:
                        continue

                    should_continue = await self.process_command(command_line)
                    if should_continue is False:
                        break

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                    continue
                except EOFError:
                    break
        finally:
            await self.client.close()
            self.console.print("[blue]Goodbye![/blue]")


async def run_cli(base_url: str) -> None:
    """Run the CLI."""
    cli = FenixaosCLI(base_url=base_url)
    await cli.run()


def main() -> None:
    """Main entry point for the CLI."""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="FenixAOS CLI - Interactive client for YAML entrypoint"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host of the YAML entrypoint server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9997,
        help="Port of the YAML entrypoint server (default: 9997)",
    )
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    asyncio.run(run_cli(base_url))


if __name__ == "__main__":
    main()

"""Backend operations abstraction layer."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from rich.console import Console

    from .repl import YamlBackendClient


class BackendOperations:
    """Abstraction layer for backend operations with consistent error handling."""

    def __init__(self, client: "YamlBackendClient", console: "Console"):
        self.client = client
        self.console = console

    def _print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[green]✓ {message}[/green]")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[red]Error: {message}[/red]")

    def _print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[blue]{message}[/blue]")

    async def handle_response(
        self, result: Dict[str, Any], success_key: str = "message"
    ) -> Optional[Dict[str, Any]]:
        """Handle backend response with consistent error handling."""
        if result.get("status") == "success":
            message = result.get(success_key, "Operation completed successfully")
            self._print_success(message)
            # Return the data if it exists, otherwise return a truthy dict to indicate success
            data = result.get("data")
            return data if data is not None else {"success": True}
        else:
            error = result.get("detail", "Unknown error occurred")
            self._print_error(error)
            return None

    async def load_graph(
        self, file_path: str, graph_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Load a graph with validation and error handling."""
        # Validate file exists
        if not Path(file_path).exists():
            self._print_error(f"File '{file_path}' not found")
            return None

        # Use filename stem as default graph_id
        if not graph_id:
            graph_id = Path(file_path).stem

        try:
            self.console.print(f"Loading graph from '{file_path}' as '{graph_id}'...")
            result = await self.client.load_graph(file_path, graph_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def list_graphs(self) -> Optional[Dict[str, Any]]:
        """List all loaded graphs."""
        try:
            result = await self.client.list_graphs()
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def get_graph_info(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific graph."""
        try:
            result = await self.client.get_graph_info(graph_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def unload_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Unload a graph from memory."""
        try:
            result = await self.client.unload_graph(graph_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def reload_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Reload a graph from its original file."""
        try:
            result = await self.client.reload_graph(graph_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def execute_task(self, task: str, graph_id: str) -> Optional[Dict[str, Any]]:
        """Execute a task using a loaded graph."""
        try:
            result = await self.client.execute_task(task, graph_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def register_model(
        self,
        model_id: str,
        model_type: str,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Register a new model."""
        try:
            result = await self.client.register_model(
                model_id=model_id,
                model_type=model_type,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
            )
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def list_models(self) -> Optional[Dict[str, Any]]:
        """List all registered models."""
        try:
            result = await self.client.list_models()
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def delete_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Delete a registered model."""
        try:
            result = await self.client.delete_model(model_id)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def test_models(self, model_ids: list[str] = []) -> Optional[Dict[str, Any]]:
        """Test model(s) for usability."""
        try:
            result = await self.client.test_models(model_ids)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def list_tools(self) -> Optional[Dict[str, Any]]:
        """List available tools."""
        try:
            result = await self.client.list_tools()
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def reload_tools(self) -> Optional[Dict[str, Any]]:
        """Reload all tools."""
        try:
            result = await self.client.reload_tools()
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

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
    ) -> Optional[Dict[str, Any]]:
        """Add a new MCP server configuration."""
        try:
            result = await self.client.add_mcp_server(
                name=name,
                transport=transport,
                description=description,
                command=command,
                args=args,
                url=url,
                env=env,
                cwd=cwd,
                headers=headers,
            )
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def list_mcp_servers(self) -> Optional[Dict[str, Any]]:
        """List all configured MCP servers."""
        try:
            result = await self.client.list_mcp_servers()
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def remove_mcp_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Remove an MCP server configuration."""
        try:
            result = await self.client.remove_mcp_server(server_name)
            return await self.handle_response(result)
        except Exception as e:
            self._print_error(str(e))
            return None

    async def draw_graph(
        self,
        graph_id: str,
        output_file: str,
        with_styles: bool = True,
        curve_style: str = "linear",
        wrap_label_n_words: int = 9,
    ) -> Optional[Dict[str, Any]]:
        """Draw a graph as PNG image."""
        try:
            result = await self.client.draw_graph(
                graph_id=graph_id,
                with_styles=with_styles,
                curve_style=curve_style,
                wrap_label_n_words=wrap_label_n_words,
            )

            # Save PNG bytes to file
            with open(output_file, "wb") as f:
                f.write(result)
            self._print_success(f"PNG image saved to '{output_file}'")
            return {"success": True}

        except Exception as e:
            self._print_error(str(e))
            return None

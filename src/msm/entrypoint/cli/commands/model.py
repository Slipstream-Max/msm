"""Model management CLI commands."""

from typing import TYPE_CHECKING, List

from rich.table import Table

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition

if TYPE_CHECKING:
    from ..repl import FenixaosCLI


class ModelCommand(BaseCommand):
    """Model management command with subcommands."""

    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(
            name="model",
            description="Manage AI models",
            arguments=[
                CommandArgument(
                    "subcommand",
                    ArgumentType.STRING,
                    choices=["register", "list", "delete", "test"],
                    description="Model operation",
                )
            ],
            examples=[
                "model list",
                "model register my_model openai gpt-4 api_key",
                "model delete my_model",
                "model test",
                "model test my_model",
                "model test my_model1 my_model2 my_model3",
            ],
        )

    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        if not args:
            self._print_usage_error(cli)
            return True

        subcommand = args[0].lower()
        subargs = args[1:]

        if subcommand == "register":
            return await self._handle_register(subargs, cli)
        elif subcommand == "list":
            return await self._handle_list(subargs, cli)
        elif subcommand == "delete":
            return await self._handle_delete(subargs, cli)
        elif subcommand == "test":
            return await self._handle_test(subargs, cli)
        else:
            self._print_error(cli, f"Unknown model subcommand: {subcommand}")
            cli.console.print("Available subcommands: register, list, delete, test")
            return True

    async def _handle_register(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle model register subcommand."""
        if len(args) < 4:
            cli.console.print(
                "[red]Usage: model register <id> <type> <name> <api_key> [base_url] [temperature][/red]"
            )
            return True

        model_id = args[0]
        model_type = args[1]
        model_name = args[2]
        api_key = args[3]
        base_url = args[4] if len(args) > 4 else None

        # Parse temperature
        try:
            temperature = float(args[5]) if len(args) > 5 else 0.0
        except ValueError:
            self._print_error(cli, "Invalid temperature value. Must be a float.")
            return True

        cli.console.print(f"Registering model '{model_id}'...")
        data = await cli.backend_operations.register_model(
            model_id=model_id,
            model_type=model_type,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

        if data:
            # Display registration details
            table = Table(title="Model Registration Details")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Model ID", data.get("model_id", model_id))
            table.add_row("Type", data.get("model_type", model_type))
            table.add_row("Model Name", data.get("model_name", model_name))
            table.add_row("Base URL", data.get("base_url") or "Default")
            table.add_row("Temperature", str(data.get("temperature", temperature)))
            table.add_row("Registered At", data.get("registered_at", "N/A"))

            cli.console.print(table)

        return True

    async def _handle_list(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle model list subcommand."""
        data = await cli.backend_operations.list_models()
        if data:
            models = data.get("models", [])
            if not models:
                cli.console.print("[yellow]No models registered[/yellow]")
                return True

            table = Table(title="Registered Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Model Name", style="green")
            table.add_column("Base URL", style="blue")
            table.add_column("Temperature", style="yellow")

            for model in models:
                table.add_row(
                    model.get("model_id", "N/A"),
                    model.get("model_type", "N/A"),
                    model.get("model_name", "N/A"),
                    model.get("base_url") or "Default",
                    str(model.get("temperature", 0.0)),
                )

            cli.console.print(table)

        return True

    async def _handle_delete(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle model delete subcommand."""
        if not args:
            cli.console.print("[red]Usage: model delete <id>[/red]")
            return True

        model_id = args[0]
        cli.console.print(f"Deleting model '{model_id}'...")
        await cli.backend_operations.delete_model(model_id)

        return True

    async def _handle_test(self, args: List[str], cli: "FenixaosCLI") -> bool:
        """Handle model test subcommand."""
        if len(args) == 0:
            # Test all models
            cli.console.print("Testing all models...")
            data = await cli.backend_operations.test_models()
        else:
            # Test multiple specific models
            model_ids = args
            cli.console.print(f"Testing models: {', '.join(model_ids)}...")
            data = await cli.backend_operations.test_models(model_ids=model_ids)

        with cli.console.status("[bold green]Testing models..."):
            pass  # Status is shown during the actual call above

        if data:
            test_results = data.get("test_results", [])
            total_tested = data.get("total_tested", 0)
            passed = data.get("passed", 0)
            failed = data.get("failed", 0)

            if not test_results:
                cli.console.print("[yellow]No models to test[/yellow]")
                return True

            # Create summary table
            summary_table = Table(title="Model Test Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")

            summary_table.add_row("Total Tested", str(total_tested))
            summary_table.add_row("Passed", f"[green]{passed}[/green]")
            summary_table.add_row("Failed", f"[red]{failed}[/red]")

            cli.console.print(summary_table)

            # Create detailed results table
            results_table = Table(title="Detailed Test Results")
            results_table.add_column("Model ID", style="cyan")
            results_table.add_column("Status", style="white")
            results_table.add_column("Response Time", style="blue")
            results_table.add_column("Message/Error", style="yellow")

            for result in test_results:
                status = result.get("status", "unknown")
                status_color = (
                    "[green]✓ PASSED[/green]"
                    if status == "passed"
                    else "[red]✗ FAILED[/red]"
                )

                response_time = result.get("response_time")
                response_time_str = (
                    f"{response_time}s" if response_time is not None else "N/A"
                )

                message = result.get("test_message") or result.get(
                    "error", "No details"
                )
                # Truncate long messages
                if len(message) > 50:
                    message = message[:47] + "..."

                results_table.add_row(
                    result.get("model_id", "Unknown"),
                    status_color,
                    response_time_str,
                    message,
                )

            cli.console.print(results_table)

        return True

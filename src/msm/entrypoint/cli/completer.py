"""Systematic completer for the new command framework."""

from typing import TYPE_CHECKING, Iterable

from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.completion.base import CompleteEvent
from prompt_toolkit.document import Document

from .commands.base import ArgumentType

if TYPE_CHECKING:
    from .commands.base import BaseCommand
    from .repl import FenixaosCLI


class FilePathCompleter(Completer):
    """Completer for file paths."""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        from pathlib import Path

        text = document.text_before_cursor
        try:
            p = Path(text).expanduser()
            if p.is_dir():
                for item in p.iterdir():
                    yield Completion(str(item), start_position=-len(text))
            else:
                for item in p.parent.iterdir():
                    if item.name.startswith(p.name):
                        yield Completion(str(item), start_position=-len(text))
        except Exception:
            # Log completion error but don't break autocomplete
            pass


class SystematicCompleter(Completer):
    """Systematic completer that works with the command framework."""

    def __init__(self, cli: "FenixaosCLI"):
        self.cli = cli
        self.file_path_completer = FilePathCompleter()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        parts = text.split()

        if not parts:
            yield from self._complete_commands(document, complete_event)
            return

        if len(parts) == 1 and not text.endswith(" "):
            yield from self._complete_commands(document, complete_event)
            return

        command_name = parts[0].lower()
        command = self.cli.command_registry.get_command(command_name)

        if command:
            yield from self._complete_command_args(
                command, parts[1:], text, document, complete_event
            )

    def _complete_commands(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Complete command names."""
        command_completer = WordCompleter(
            self.cli.command_registry.get_command_names(), ignore_case=True
        )
        yield from command_completer.get_completions(document, complete_event)

    def _complete_command_args(
        self,
        command: "BaseCommand",
        args: list,
        full_text: str,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        """Complete command arguments based on their types."""
        # Handle subcommands for model and tools
        if (
            command.definition.name in ["model", "tools"]
            and not full_text.endswith(" ")
            and args
        ):
            # We're still completing the subcommand
            if len(args) == 1 and not full_text.endswith(" "):
                choices = None
                for arg in command.definition.arguments:
                    if arg.name == "subcommand" and arg.choices:
                        choices = arg.choices
                        break

                if choices:
                    completer = WordCompleter(choices, ignore_case=True)
                    yield from completer.get_completions(document, complete_event)
                return

        # Determine which argument we're completing
        arg_index = len(args) - (0 if full_text.endswith(" ") else 1)

        if arg_index >= len(command.definition.arguments):
            return

        arg_def = command.definition.arguments[arg_index]

        # Complete based on argument type
        if arg_def.type == ArgumentType.FILE_PATH:
            partial = args[-1] if args and not full_text.endswith(" ") else ""
            doc = Document(partial, cursor_position=len(partial))
            yield from self.file_path_completer.get_completions(doc, complete_event)

        elif arg_def.type == ArgumentType.GRAPH_ID:
            graph_completer = WordCompleter(
                list(self.cli.loaded_graphs.keys()), ignore_case=True
            )
            yield from graph_completer.get_completions(document, complete_event)

        elif arg_def.choices:
            choice_completer = WordCompleter(arg_def.choices, ignore_case=True)
            yield from choice_completer.get_completions(document, complete_event)

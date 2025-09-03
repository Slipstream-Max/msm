"""CLI command framework for FenixAOS."""

from .base import ArgumentType, BaseCommand, CommandArgument, CommandDefinition
from .registry import CommandRegistry

__all__ = [
    "BaseCommand",
    "CommandDefinition",
    "CommandArgument",
    "ArgumentType",
    "CommandRegistry",
]

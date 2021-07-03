from typing import List, Optional
from .module import DashedCommand, DashedModule
from .interaction import InteractionContext, DeferredInteractionContext
from .discord import Channel, User, Role, Mentionable

__all__ = {
    "command",
    "DashedCommand",
    "DashedModule",
    "InteractionContext",
    "DeferredInteractionContext",
    "Channel",
    "User",
    "Role",
    "Mentionable",
}

_registered_command_functions_buffer = []


def _flush_registered_command_functions_buffer() -> List:
    global _registered_command_functions_buffer
    result = _registered_command_functions_buffer
    _registered_command_functions_buffer = []
    return result


def command(*, description: str, name: Optional[str] = None):
    global _registered_command_functions_buffer

    def command_decorator(fn):
        fn.__command_metadata__ = {
            "name": name or fn.__name__,
            "description": description,
        }
        _registered_command_functions_buffer.append(fn)
        return fn

    return command_decorator

import dataclasses
from typing import Any, List, Optional


_registered_command_functions_buffer = []


def _flush_registered_command_functions_buffer() -> List:
    global _registered_command_functions_buffer
    result = _registered_command_functions_buffer
    _registered_command_functions_buffer = []
    return result


class InteractionContext:
    pass


class Channel:
    pass


class User:
    pass


class Role:
    pass


class Mentionable:
    pass


def command(*, name: Optional[str] = None):
    global _registered_command_functions_buffer

    def command_decorator(fn):
        fn.__command_metadata__ = {"name": name or fn.__name__}
        _registered_command_functions_buffer.append(fn)
        return fn

    return command_decorator


@dataclasses.dataclass
class DashedCommand:
    name: str
    fn: Any


@dataclasses.dataclass
class DashedModule:
    name: str
    commands: List[DashedCommand]

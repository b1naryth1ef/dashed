from dashed.module import DashedCommand, DashedModule
from typing import List
from dashed import _flush_registered_command_functions_buffer

import pathlib
from importlib import util


def _load_commands() -> List[DashedCommand]:
    commands = []
    for command_function in _flush_registered_command_functions_buffer():
        commands.append(
            DashedCommand(fn=command_function, **command_function.__command_metadata__)
        )
    return commands


def load_from_file(path: pathlib.Path) -> DashedModule:
    import importlib.machinery

    module = importlib.machinery.SourceFileLoader(
        f"dashed.runtime.module.{path.stem}", str(path)
    ).load_module()

    return DashedModule(name=path.stem, commands=_load_commands())

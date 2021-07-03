import inspect
from dashed.discord import (
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    Channel,
    Mentionable,
    Role,
    User,
)
import dataclasses
from typing import Any, Dict, List
import typing


@dataclasses.dataclass
class DashedCommand:
    name: str
    description: str
    fn: Any

    def get_args(self) -> Dict[str, ApplicationCommandOption]:
        signature = inspect.signature(self.fn)
        type_hint = typing.get_type_hints(self.fn)

        assert list(signature.parameters.keys())[0] == "ctx"
        args = {k for k in list(signature.parameters.keys())[1:]}
        arg_types = {k: type_hint[k] for k in args}

        opts = {}
        for arg in args:
            required = signature.parameters[arg].default is inspect.Parameter.empty

            option_type = None
            if arg_types[arg] is str:
                option_type = ApplicationCommandOptionType.STRING
            elif arg_types[arg] is int:
                option_type = ApplicationCommandOptionType.INTEGER
            elif arg_types[arg] is bool:
                option_type = ApplicationCommandOptionType.BOOLEAN
            elif arg_types[arg] is User:
                option_type = ApplicationCommandOptionType.USER
            elif arg_types[arg] is Channel:
                option_type = ApplicationCommandOptionType.CHANNEL
            elif arg_types[arg] is Role:
                option_type = ApplicationCommandOptionType.ROLE
            elif arg_types[arg] is Mentionable:
                option_type = ApplicationCommandOptionType.MENTIONABLE
            else:
                raise Exception(
                    f"Could not determine application command option type for {arg_types[arg]}"
                )
            opts[arg] = ApplicationCommandOption(
                type=option_type, name=arg, description=arg, required=required
            )
        return opts


@dataclasses.dataclass
class DashedModule:
    name: str
    commands: List[DashedCommand]

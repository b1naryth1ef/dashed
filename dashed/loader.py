import inspect
import typing

from dashed.discord import (
    ApplicationCommandDescription,
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    Channel,
    DiscordAPIClient,
    Mentionable,
    Role,
    User,
)
import dataclasses
from typing import Any, Dict, List, Optional, Tuple, Union

import pathlib

_registered_groups_buffer = []
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


def _flush_registered_groups_buffer() -> List:
    global _registered_groups_buffer
    result = _registered_groups_buffer
    _registered_groups_buffer = []
    return result


class TypeWithChoices:
    def __init__(self, inner_type: type, choices: Dict[str, Union[str, int]]):
        self.inner_type = inner_type
        self.choices = choices


@dataclasses.dataclass
class Group:
    name: str
    description: str
    commands: Dict[str, "DashedCommand"] = dataclasses.field(default_factory=dict)
    children: Dict[str, "Group"] = dataclasses.field(default_factory=dict)

    def lookup(self, options):
        assert len(options) == 1
        target_name = options[0]["name"]

        if target_name in self.commands:
            return self.commands[target_name], options[0]["options"]

        return self.children[target_name].lookup(options[0]["options"])

    def __post_init__(self):
        global _registered_groups_buffer
        _registered_groups_buffer.append(self)

    def subgroup(self, name: str, description: str):
        group = Group(name=name, description=description)
        self.children[name] = group
        return group

    def command(self, *, description: str, name: Optional[str] = None):
        def command_decorator(fn):
            self.commands[name or fn.__name__] = DashedCommand(
                name=name or fn.__name__, description=description, fn=fn
            )
            return fn

        return command_decorator


@dataclasses.dataclass
class DashedCommand:
    name: str
    description: str
    fn: Any
    deferred: bool = False

    def __post_init__(self):
        from dashed.interaction import DeferredInteractionContext

        hints = typing.get_type_hints(self.fn)
        self.deferred = hints["ctx"] == DeferredInteractionContext


@dataclasses.dataclass
class DashedModule:
    name: str
    commands: List[DashedCommand]
    groups: List[Group]


@dataclasses.dataclass
class DashedContext:
    client: DiscordAPIClient
    application_id: str
    application_key: str
    commands: Dict[str, DashedCommand]
    groups: Dict[str, Group]

    async def register_commands(self, commands: List[DashedCommand]):
        for command in commands:
            await self.client.create_global_command_application(
                self.application_id,
                dataclasses.asdict(_get_application_command_description(command)),
            )
            self.commands[command.name] = command

    async def register_groups(self, groups: List[Group]):
        for group in groups:
            await self.client.create_global_command_application(
                self.application_id,
                dataclasses.asdict(_get_application_group_description(group)),
            )
            self.groups[group.name] = group


def _load_commands() -> List[DashedCommand]:
    commands = []
    for command_function in _flush_registered_command_functions_buffer():
        commands.append(
            DashedCommand(fn=command_function, **command_function.__command_metadata__)
        )
    return commands


def _load_groups() -> List["Group"]:
    return _flush_registered_groups_buffer()


def load_from_file(path: pathlib.Path) -> DashedModule:
    import importlib.machinery

    importlib.machinery.SourceFileLoader(
        f"dashed.runtime.module.{path.stem}", str(path)
    ).load_module()

    return DashedModule(
        name=path.stem, commands=_load_commands(), groups=_load_groups()
    )


def _get_options_for_group(group: Group) -> List[ApplicationCommandOption]:
    options = []

    for command in group.commands.values():
        options.append(
            ApplicationCommandOption(
                type=ApplicationCommandOptionType.SUB_COMMAND,
                name=command.name,
                description=command.description,
                options=list(_get_command_args(command).values()),
            )
        )

    for subgroup in group.children.values():
        options.append(
            ApplicationCommandOption(
                type=ApplicationCommandOptionType.SUB_COMMAND_GROUP,
                name=subgroup.name,
                description=subgroup.description,
                options=_get_options_for_group(subgroup),
            )
        )

    return options


def _get_application_group_description(group: Group) -> ApplicationCommandDescription:
    return ApplicationCommandDescription(
        name=group.name,
        description=group.description,
        options=_get_options_for_group(group),
    )


def _get_application_command_description(
    command: "DashedCommand",
) -> ApplicationCommandDescription:
    return ApplicationCommandDescription(
        name=command.name,
        description=command.description,
        options=list(_get_command_args(command).values()),
    )


def _get_option_type_and_choices(
    type_: type,
) -> Tuple[ApplicationCommandOptionType, Optional[List[Dict[str, Any]]]]:
    if type_ is str:
        return ApplicationCommandOptionType.STRING, None
    elif type_ is int:
        return ApplicationCommandOptionType.INTEGER, None
    elif type_ is bool:
        return ApplicationCommandOptionType.BOOLEAN, None
    elif type_ is User:
        return ApplicationCommandOptionType.USER, None
    elif type_ is Channel:
        return ApplicationCommandOptionType.CHANNEL, None
    elif type_ is Role:
        return ApplicationCommandOptionType.ROLE, None
    elif type_ is Mentionable:
        return ApplicationCommandOptionType.MENTIONABLE, None
    elif isinstance(type_, TypeWithChoices):
        inner, choices = _get_option_type_and_choices(type_.inner_type)
        assert choices is None, "cannot have nested TypeWithOptions"
        return inner, [{"name": k, "value": v} for k, v in type_.choices.items()]
    else:
        raise Exception(
            f"Could not determine application command option type for {type_}"
        )


def _get_command_args(command: DashedCommand) -> Dict[str, ApplicationCommandOption]:
    signature = inspect.signature(command.fn)
    type_hint = typing.get_type_hints(command.fn)

    assert list(signature.parameters.keys())[0] == "ctx"
    args = {k for k in list(signature.parameters.keys())[1:]}
    arg_types = {k: type_hint[k] for k in args}

    opts = {}
    for arg in args:
        required = signature.parameters[arg].default is inspect.Parameter.empty

        option_type, choices = _get_option_type_and_choices(arg_types[arg])
        opts[arg] = ApplicationCommandOption(
            type=option_type,
            name=arg,
            description=arg,
            required=required,
            choices=choices,
        )
    return opts

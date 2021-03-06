import dataclasses
import inspect
import pathlib
import typing
from typing import Any, Dict, List, Optional, OrderedDict, Tuple, Union

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

_registered_groups_buffer = []
_registered_commands_buffer = []


def _flush_registered_commands_buffer() -> List:
    global _registered_commands_buffer
    result = _registered_commands_buffer
    _registered_commands_buffer = []
    return result


def command(*, description: str, name: Optional[str] = None):
    global _registered_commands_buffer

    def command_decorator(fn):
        _registered_commands_buffer.append(
            DashedCommand(name=name or fn.__name__, description=description, fn=fn)
        )
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
    application_key: str
    commands: Dict[str, DashedCommand]
    groups: Dict[str, Group]

    async def register_commands(self, application_id):
        for command in self.commands.values():
            await self.client.create_global_application_command(
                application_id,
                dataclasses.asdict(_get_application_command_description(command)),
            )

    async def register_groups(self, application_id):
        for group in self.groups.values():
            await self.client.create_global_application_command(
                application_id,
                dataclasses.asdict(_get_application_group_description(group)),
            )


async def load_from_file(path: pathlib.Path) -> DashedModule:
    import importlib.machinery

    module = importlib.machinery.SourceFileLoader(
        f"dashed.runtime.module.{path.stem}", str(path)
    ).load_module()

    if hasattr(module, "initialize"):
        await module.initialize()

    return DashedModule(
        name=path.stem,
        commands=_flush_registered_commands_buffer(),
        groups=_flush_registered_groups_buffer(),
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

    assert list(type_hint.keys())[0] == "ctx"
    args = {k for k in list(type_hint.keys())[1:]}
    arg_types = {k: type_hint[k] for k in args}

    opts = OrderedDict()
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

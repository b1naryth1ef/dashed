import dataclasses
import json
from typing import List, Literal, Optional, Union
import typing
from dashed.module import DashedCommand, DashedModule
from email.policy import default
import httpx
from enum import IntEnum


class InteractionRequestType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3


class InteractionResponseType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7


class ApplicationCommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9


@dataclasses.dataclass
class AllowedMentions:
    parse: List[Literal["roles", "users", "everyone"]]
    roles: List[int] = dataclasses.field(default_factory=list)
    users: List[int] = dataclasses.field(default_factory=list)
    replied_user: bool = False


@dataclasses.dataclass
class ApplicationCommandCallbackData:
    tts: Optional[bool] = None
    content: Optional[str] = None
    embeds: Optional[List] = None
    allowed_mentions: Optional[AllowedMentions] = None
    flags: Optional[int] = None
    components: Optional[List] = None


@dataclasses.dataclass
class ApplicationCommandOptionChoice:
    name: str
    value: Union[int, str]


@dataclasses.dataclass
class ApplicationCommandOption:
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool = False
    choices: List[ApplicationCommandOptionChoice] = dataclasses.field(
        default_factory=list
    )
    options: List["ApplicationCommandOption"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ApplicationCommandDescription:
    name: str
    description: str
    options: List[ApplicationCommandOption]
    default_permission: bool = True


class DiscordAPIClient:
    def __init__(self, token):
        self._http = httpx.AsyncClient(
            headers={
                "Authorization": f"Bot {token}",
                "User-Agent": "DiscordBot (https://github.com/b1naryth1ef/dashed dev)",
            }
        )

    def _url(self, path):
        return f"https://discord.com/api/v8{path}"

    async def _post(self, path, **kwargs):
        r = await self._http.post(self._url(path), **kwargs)
        r.raise_for_status()
        return r.json()

    async def create_global_command_application(self, application_id, body):
        await self._post(f"/applications/{application_id}/commands", json=body)


def _get_application_command_description(
    command: DashedCommand,
) -> ApplicationCommandDescription:
    options = []

    for arg, arg_type in command.get_args().items():
        option_type = None
        if arg_type is str:
            option_type = ApplicationCommandOptionType.STRING
        else:
            raise Exception(
                f"Could not determine application command option type for {arg_type}"
            )

        options.append(
            ApplicationCommandOption(type=option_type, name=arg, description=arg)
        )

    return ApplicationCommandDescription(
        name=command.name, description=command.description, options=options
    )


async def register_slash_commands(
    client: DiscordAPIClient, application_id: int, commands: List[DashedCommand]
):
    for command in commands:
        await client.create_global_command_application(
            application_id,
            dataclasses.asdict(_get_application_command_description(command)),
        )
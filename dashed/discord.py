import asyncio
import dataclasses
from enum import IntEnum
from typing import List, Literal, Optional, Union

import httpx

from dashed.embeds import Embed


class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_STORE = 6
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_THREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13


@dataclasses.dataclass
class Channel:
    id: str
    name: str
    permissions: str
    type: ChannelType


@dataclasses.dataclass
class User:
    id: str
    username: str
    discriminator: str
    public_flags: int
    bot: bool
    avatar: str

    def mention(self):
        return f"<@{self.id}>"


@dataclasses.dataclass
class Role:
    pass


@dataclasses.dataclass
class Mentionable:
    pass


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
    embeds: Optional[List[Embed]] = None
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


@dataclasses.dataclass
class WebhookEditBody:
    content: Optional[str] = None
    allowed_mentions: Optional[AllowedMentions] = None
    embeds: Optional[List[Embed]] = None


class DiscordAPIClient:
    def __init__(self, token):
        self._http = httpx.AsyncClient(
            headers={
                "Authorization": f"Bot {token}",
                "User-Agent": "DiscordBot (https://github.com/b1naryth1ef/dashed dev)",
            }
        )

    async def close(self):
        await self._http.aclose()

    def _url(self, path):
        return f"https://discord.com/api/v8{path}"

    async def _check(self, response):
        if "X-RateLimit-Reset-After" in response.headers:
            if int(response.headers["X-RateLimit-Remaining"]) == 0:
                await asyncio.sleep(float(response.headers["X-RateLimit-Reset-After"]))

        try:
            response.raise_for_status()
        except Exception:
            print("Response: ", response.json())
            raise

    async def _get(self, path):
        r = await self._http.get(self._url(path))
        await self._check(r)
        return r.json()

    async def _patch(self, path, **kwargs):
        r = await self._http.patch(self._url(path), **kwargs)
        await self._check(r)
        return r.json()

    async def _post(self, path, **kwargs):
        r = await self._http.post(self._url(path), **kwargs)
        await self._check(r)
        return r.json()

    async def _delete(self, path):
        r = await self._http.delete(self._url(path))
        await self._check(r)

    async def get_global_application_commands(self, application_id):
        return await self._get(f"/applications/{application_id}/commands")

    async def create_global_application_command(self, application_id, body):
        return await self._post(f"/applications/{application_id}/commands", json=body)

    async def delete_global_application_command(self, application_id, command_id):
        await self._delete(f"/applications/{application_id}/commands/{command_id}")

    async def edit_original_interaction_response(
        self, application_id, interaction_token, body
    ):
        return await self._patch(
            f"/webhooks/{application_id}/{interaction_token}/messages/@original",
            json=body,
        )

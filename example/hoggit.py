from datetime import timedelta
from dashed.embeds import Embed, EmbedField
import dataclasses
import time
from typing import Any, List
import dashed
import httpx


@dataclasses.dataclass
class HoggitServerData:
    players: int
    maxPlayers: int
    metar: str
    missionName: str
    realtime: float
    serverName: str
    start_time: int
    theater: str
    updateTime: str
    uptime: float
    wx: Any
    airports: List[Any]
    objects: List[Any]


group = dashed.Group(
    name="hoggit", description="Commands relating to the hoggit community"
)


servers = {"saw": "coldwar", "gaw": "dcs", "pgaw": "pgaw", "tnn": "tnn"}
ServerType = dashed.TypeWithChoices(str, choices=servers)

GREEN_COLOR = 0x77DD77
RED_COLOR = 0xFF6961


@group.command(description="Lookup the current status of a DCS server")
async def status(ctx: dashed.DeferredInteractionContext, server: ServerType):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://{server}.hoggitworld.com/?_={int(time.time())}"
        )

        server_data = HoggitServerData(**res.json())

    is_full = server_data.players == server_data.maxPlayers

    await ctx.update(
        embeds=[
            Embed(
                title=server_data.serverName,
                color=RED_COLOR if is_full else GREEN_COLOR,
                fields=[
                    EmbedField(
                        name="Players",
                        value=f"{server_data.players}/{server_data.maxPlayers}",
                        inline=True,
                    ),
                    EmbedField(
                        name="Mission",
                        value=server_data.missionName,
                        inline=True,
                    ),
                    EmbedField(
                        name="Uptime",
                        value=str(timedelta(seconds=int(server_data.uptime))),
                    ),
                ],
                description=server_data.metar,
            )
        ]
    )

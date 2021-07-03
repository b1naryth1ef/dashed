from dashed.interaction import InteractionContext
from typing import Dict
from dashed.module import DashedCommand
from dashed.discord import (
    DiscordAPIClient,
    InteractionRequestType,
    InteractionResponseType,
)
import json
from aiohttp import web
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def respond_json(data) -> web.Response:
    return web.Response(
        body=json.dumps(data).encode("utf-8"), content_type="application/json"
    )


async def handle_interactions_request(request):
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    body = await request.read()

    try:
        request.app["application_key"].verify(
            timestamp.encode("utf-8") + body, bytes.fromhex(signature)
        )
    except BadSignatureError:
        return web.Response(text="bad signature", status=400)

    data = json.loads(body)

    if data["type"] == InteractionRequestType.PING:
        return respond_json({"type": InteractionResponseType.PONG})
    elif data["type"] == InteractionRequestType.APPLICATION_COMMAND:
        command_data = data["data"]

        target_command = request.app["commands"].get(command_data["name"])
        if not target_command:
            return web.Response(text="unknown command", status=400)

        options = {i["name"]: i["value"] for i in command_data.get("options", [])}
        args = {k: options[k] for k in target_command.get_args().keys()}
        result = await target_command.fn(
            InteractionContext(request.app["api"], data), **args
        )
        return respond_json(result)

    return respond_json({})


async def run(
    host: str,
    port: int,
    api: DiscordAPIClient,
    application_key: bytes,
    commands: Dict[str, DashedCommand],
):
    app = web.Application()
    app["api"] = api
    app["application_key"] = VerifyKey(application_key)
    app["commands"] = commands
    app.add_routes([web.post("/interactions", handle_interactions_request)])
    await web._run_app(app, host=host, port=port)

import asyncio
import json
from typing import Any, Dict, List

from aiohttp import web
from nacl.exceptions import BadSignatureError

from dashed.discord import (
    ApplicationCommandOptionType,
    Channel,
    InteractionRequestType,
    InteractionResponseType,
    User,
)
from dashed.interaction import DeferredInteractionContext, InteractionContext
from dashed.loader import DashedContext, _get_command_args


def respond_json(data) -> web.Response:
    return web.Response(
        body=json.dumps(data).encode("utf-8"), content_type="application/json"
    )


def _get_options_data(
    command_data: Dict[str, Any], options: List[Any]
) -> Dict[str, Any]:
    result = {}

    for option in options:
        if option["type"] == ApplicationCommandOptionType.CHANNEL:
            result[option["name"]] = Channel(
                **command_data["resolved"]["channels"][option["value"]]
            )
        elif option["type"] == ApplicationCommandOptionType.USER:
            result[option["name"]] = User(
                **command_data["resolved"]["users"][option["value"]]
            )
        else:
            result[option["name"]] = option["value"]
    return result


async def handle_interactions_request(request):
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    body = await request.read()

    try:
        request.app["ctx"].application_key.verify(
            timestamp.encode("utf-8") + body, bytes.fromhex(signature)
        )
    except BadSignatureError:
        return web.Response(text="bad signature", status=400)

    data = json.loads(body)

    if data["type"] == InteractionRequestType.PING:
        return respond_json({"type": InteractionResponseType.PONG})
    elif data["type"] == InteractionRequestType.APPLICATION_COMMAND:
        command_data = data["data"]

        target_command = None
        options_data = None
        if command_data["name"] in request.app["ctx"].commands:
            target_command = request.app["ctx"].commands[command_data["name"]]
            options_data = command_data.get("options", [])
        elif command_data["name"] in request.app["ctx"].groups:
            target_command, options_data = (
                request.app["ctx"]
                .groups[command_data["name"]]
                .lookup(command_data["options"])
            )
        else:
            print("No target command", data)
            return web.Response(text="unknown command", status=400)

        options = _get_options_data(command_data, options_data)
        args = {k: options[k] for k in _get_command_args(target_command).keys()}

        interaction_context = InteractionContext(request.app["ctx"], data)

        if target_command.deferred:
            asyncio.ensure_future(
                target_command.fn(
                    DeferredInteractionContext(interaction_context), **args
                )
            )
            return respond_json(
                {"type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE}
            )

        result = await target_command.fn(interaction_context, **args)
        return respond_json(result)

    return respond_json({})


async def run(host: str, port: int, ctx: DashedContext):
    app = web.Application()
    app["ctx"] = ctx
    app.add_routes([web.post("/interactions", handle_interactions_request)])
    await web._run_app(app, host=host, port=port)

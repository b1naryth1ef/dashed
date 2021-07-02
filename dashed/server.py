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
    print(data)

    if data["type"] == 1:
        return respond_json({"type": 1})

    return respond_json({})


def run(host: str, port: int, application_key: bytes):
    app = web.Application()
    app["application_key"] = VerifyKey(application_key)
    app.add_routes([web.post("/interactions", handle_interactions_request)])
    web.run_app(app, host=host, port=port)

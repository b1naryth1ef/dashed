import argparse
import asyncio
from dashed.discord import DiscordAPIClient
from dashed import server
import os
import pathlib
from dashed.loader import DashedContext, load_from_file
from nacl.signing import VerifyKey

ENV_ARGS = {
    "token": "DASHED_DISCORD_TOKEN",
    "application_key": "DASHED_DISCORD_APPLICATION_KEY",
    "application_id": "DASHED_DISCORD_APPLICATION_ID",
}


parser = argparse.ArgumentParser("dashed")
parser.add_argument(
    "--load-from-file",
    action="append",
    help="Load interactions and slash commands from a Python file",
)
parser.add_argument(
    "--host",
    default="localhost",
    help="The host string to bind on",
)
parser.add_argument("--port", default=8689, type=int, help="The port to bind on")
parser.add_argument("--token", help="Discord Bot Token")
parser.add_argument("--application-key", help="Discord Application Key")
parser.add_argument("--application-id", help="Discord Application ID")


def _run_in_loop(fn):
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(fn)
    finally:
        event_loop.close()


async def main():
    args = parser.parse_args()

    env_opts = {}
    for k, v in ENV_ARGS.items():
        env_opts[k] = getattr(args, k)
        if env_opts[k] is None:
            value = os.environ.get(v)
            if value is None:
                print(
                    f"Error: {k.replace('_', '-')} was not passed and {v} env variable was not set"
                )
                return

            env_opts[k] = value

    application_key = bytes.fromhex(env_opts["application_key"])

    api = DiscordAPIClient(token=env_opts["token"])

    modules = []
    for file_path in args.load_from_file:
        modules.append(load_from_file(pathlib.Path(file_path)))

    commands = {}
    for module in modules:
        for command in module.commands:
            commands[command.name] = command

    groups = {}
    for module in modules:
        for group in module.groups:
            groups[group.name] = group

    ctx = DashedContext(
        client=api,
        application_id=env_opts["application_id"],
        application_key=VerifyKey(bytes.fromhex(env_opts["application_key"])),
        commands=commands,
        groups=groups,
    )

    await ctx.register_commands(commands.values())
    await ctx.register_groups(groups.values())

    await server.run(args.host, args.port, ctx)


_run_in_loop(main())

import argparse
import asyncio
import sys
from dashed.discord import DiscordAPIClient
from dashed import server
import os
import pathlib
from dashed.loader import DashedContext, load_from_file
from nacl.signing import VerifyKey

ENV_ARGS = {
    "token": "DASHED_DISCORD_TOKEN",
    "application_key": "DASHED_DISCORD_APPLICATION_KEY",
}


def _get_context(args, not_required=None) -> DashedContext:
    for k, v in ENV_ARGS.items():
        if getattr(args, k, None) is None:
            value = os.environ.get(v)
            if value is None:
                if not_required is not None and k in not_required:
                    continue

                print(
                    f"Error: {k.replace('_', '-')} was not passed and {v} env variable was not set"
                )
                return sys.exit(1)

            setattr(args, k, value)

    api = DiscordAPIClient(token=args.token)

    modules = []
    for file_path in args.load_from_file or []:
        modules.append(load_from_file(pathlib.Path(file_path)))

    commands = {}
    for module in modules:
        for command in module.commands:
            commands[command.name] = command

    groups = {}
    for module in modules:
        for group in module.groups:
            groups[group.name] = group

    return DashedContext(
        client=api,
        application_key=VerifyKey(bytes.fromhex(args.application_key))
        if hasattr(args, "application_key")
        else None,
        commands=commands,
        groups=groups,
    )


async def _register_commands(args):
    ctx = _get_context(args, not_required={"application_key"})

    if args.delete_unknown:
        existing_commands = await ctx.client.get_global_application_commands(
            args.application_id
        )
        for command in existing_commands:
            await ctx.client.delete_global_application_command(
                args.application_id, command["id"]
            )

    await ctx.register_commands(args.application_id)
    await ctx.register_groups(args.application_id)
    await ctx.client.close()


async def _serve(args):
    ctx = _get_context(args)
    await server.run(args.host, args.port, ctx)
    await ctx.client.close()


parser = argparse.ArgumentParser("dashed")
subparsers = parser.add_subparsers()

register_commands_parser = subparsers.add_parser("register-commands")
register_commands_parser.set_defaults(fn=_register_commands)
register_commands_parser.add_argument(
    "--application-id", help="Discord Application ID", required=True
)
register_commands_parser.add_argument(
    "-d",
    "--delete-unknown",
    help="Delete unknown (global) slash commands",
    action="store_true",
)
register_commands_parser.add_argument(
    "--load-from-file",
    action="append",
    help="Load interactions and slash commands from a Python file",
)

serve_parser = subparsers.add_parser("serve")
serve_parser.set_defaults(fn=_serve)
serve_parser.add_argument(
    "--load-from-file",
    action="append",
    help="Load interactions and slash commands from a Python file",
)
serve_parser.add_argument(
    "--host",
    default="localhost",
    help="The host string to bind on",
)
serve_parser.add_argument("--port", default=8689, type=int, help="The port to bind on")
serve_parser.add_argument("--token", help="Discord Bot Token")
serve_parser.add_argument("--application-key", help="Discord Application Key")


def _run_in_loop(fn):
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(fn)
    finally:
        event_loop.close()


async def main():
    args = parser.parse_args()
    if not hasattr(args, "fn"):
        parser.print_help()
        return

    await args.fn(args)


_run_in_loop(main())

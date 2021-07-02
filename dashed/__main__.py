import argparse
from dashed import server
import os
import pathlib
from dashed.loader import load_from_file

ENV_ARGS = {
    "token": "DASHED_DISCORD_TOKEN",
    "application_key": "DASHED_DISCORD_APPLICATION_KEY",
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


def main():
    args = parser.parse_args()
    print(args)

    modules = []
    for file_path in args.load_from_file:
        modules.append(load_from_file(pathlib.Path(file_path)))

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

    print(modules)
    server.run(args.host, args.port, application_key)


main()

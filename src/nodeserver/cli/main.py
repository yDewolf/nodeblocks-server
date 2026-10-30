import argparse
import sys

from nodeserver.cli.commands.base_command import CLICommand
from nodeserver.cli.commands.create_plugin import CreatePluginCMD

COMMANDS: list[type[CLICommand]] = [
    CreatePluginCMD,
]

def main():
    parser = argparse.ArgumentParser(
        prog="nodeserver",
        description="CLI for NodeBlocks Engine",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    for command_module in COMMANDS:
        command_module.register_command(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

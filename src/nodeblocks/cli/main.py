import argparse
import multiprocessing
import sys

from nodeblocks.cli.commands.base_command import CLICommand
from nodeblocks.cli.commands.build_protos import BuildProtosCMD
from nodeblocks.cli.commands.create_plugin import CreatePluginCMD
from nodeblocks.cli.commands.pack_plugin import PackPluginCMD
from nodeblocks.cli.commands.run_server import RunServerCMD

COMMANDS: list[type[CLICommand]] = [
    CreatePluginCMD,
    PackPluginCMD,
    RunServerCMD,
    BuildProtosCMD
]

def main():
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(
        prog="nodeblocks",
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

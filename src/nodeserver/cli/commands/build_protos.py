from argparse import _SubParsersAction, ArgumentParser, Namespace

from nodeserver.cli.commands.base_command import CLICommand
from nodeserver.scripts.compile_protos import compile_protos

class BuildProtosCMD(CLICommand):
    @classmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = subparsers.add_parser(
            "build:protos",
            description="Compiles .proto files."
        )
        return parser

    @classmethod
    def run(cls, args: Namespace):
        compile_protos()

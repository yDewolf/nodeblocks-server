from argparse import _SubParsersAction, ArgumentParser, Namespace
import logging
from pathlib import Path

from nodeserver.cli.commands.base_command import CLICommand
from nodeserver.engine.logging_config import setup_logging
from nodeserver.server.web.server import NodeServer


class RunServerCMD(CLICommand):
    @classmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = subparsers.add_parser(
            "run",
            description="Runs base Nodeblocks server."
        )
        parser.add_argument(
            "--plugins",
            type=Path,
            default=Path("./plugins"),
            help="Path to plugins folder.",
        )
        parser.add_argument(
            "--extraction",
            type=Path,
            default=Path("./plugins"),
            help="Path to extracted plugins folder.",
        )
        parser.add_argument(
            "--scenes",
            type=Path,
            default=Path("./scenes"),
            help="Path to scenes storage folder.",
        )
        return parser

    @classmethod
    def run(cls, args: Namespace):
        setup_logging(default_level=logging.DEBUG)

        plugins_folder: Path = args.plugins.resolve()
        extraction_folder: Path = args.extraction.resolve()
        scenes_folder: Path = args.scenes.resolve()

        scenes_folder.mkdir(parents=True, exist_ok=True)
        plugins_folder.mkdir(parents=True, exist_ok=True)

        print(f"Starting NodeServer...")
        print(f"- Plugins folder: {plugins_folder}")
        print(f"- Plugin Extraction folder: {extraction_folder}")
        print(f"- Scenes folder:  {scenes_folder}\n")

        server = NodeServer(
            plugins_folder=plugins_folder,
            scenes_folder=scenes_folder,
            extraction_folder=extraction_folder
        )
        server.run()

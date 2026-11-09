import importlib
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from nodeserver.cli.commands.base_command import CLICommand
from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.api import Plugin

from nodeserver.engine.plugins.helpers.plugin_packer import PluginPacker
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_EXTENSION, PluginArchive
from nodeserver.engine.plugins.protocols.plugin_manifest import EnginePluginManifest
from nodeserver.engine.utils.context_managers import scoped_sys_path


class PackPluginCMD(CLICommand):
    @classmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = subparsers.add_parser(
            "pack:plugin",
            description=f"Packs a plugin folder into a {ARCHIVE_EXTENSION} archive.",
        )
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=Path("."),
            help="Plugin folder (the one that contains plugin.py). Defaults to current folder.",
        )
        parser.add_argument(
            "-o", "--output",
            dest="output",
            type=Path,
            default=Path("dist"),
            help="Where the archive will be written. Defaults to ./dist",
        )
        return parser

    @classmethod
    def run(cls, args: Namespace):
        plugin_dir = Path(args.path).resolve()
        output_dir = Path(args.output).resolve()

        plugin_file = plugin_dir / "plugin.py"
        if not (plugin_file).is_file():
            cls._fail(f"Couldn't find plugin.py directly inside {plugin_dir}")

        if output_dir == plugin_dir or plugin_dir in output_dir.parents:
            cls._fail("Output folder must be outside of plugin folder")

        try:
            manifest = PluginScanner.get_plugin_manifest(plugin_file)
            if not manifest:
                raise Exception()
        
        except Exception as e:
            cls._fail(f"Could not load plugin manifest from plugin.py: {e}")

        if manifest.package_id != plugin_dir.name:
            cls._fail(
                f"Folder name {plugin_dir.name} must match the manifest package_id (which is {manifest.package_id})"
            )

        info = PluginArchive(**manifest.__dict__)

        try:
            archive_path, file_count = PluginPacker.pack(plugin_dir, info, output_dir)
        
        except Exception as e:
            cls._fail(str(e))

        size_kb = archive_path.stat().st_size / 1024
        print(f"\nPacked {manifest.package_id} {manifest.plugin_version}")
        print(f"    files:   {file_count}")
        print(f"    size:    {size_kb:,.1f} KiB")
        print(f"    archive: {archive_path}\n")

    @staticmethod
    def _fail(message: str):
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)
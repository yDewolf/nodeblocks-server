import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from nodeblocks.cli.commands.base_command import CLICommand
from nodeblocks.engine.plugins.helpers.archive.plugin_packer import PluginPacker
from nodeblocks.engine.plugins.helpers.archive.plugin_unpacker import PluginUnpacker
from nodeblocks.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeblocks.engine.plugins.protocols.plugin_archive import DEFAULT_ARCHIVE_EXTENSION, PluginArchive


class PackPluginCMD(CLICommand):
    @classmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = subparsers.add_parser(
            "pack:plugin",
            description=f"Packs a plugin folder into a {DEFAULT_ARCHIVE_EXTENSION} archive.",
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
        parser.add_argument(
            "--zip",
            dest="zip_suffix",
            type=bool,
            default=False,
            help="If True -> file will have .nbplugin.zip suffix instead of only .nbplugin",
        )
        return parser

    @classmethod
    def run(cls, args: Namespace):
        plugin_dir = Path(args.path).resolve()
        output_dir = Path(args.output).resolve()
        zip_suffix = bool(args.zip_suffix)

        plugin_file = plugin_dir / "plugin.py"
        if not (plugin_file).is_file():
            cls._fail(f"Couldn't find plugin.py directly inside {plugin_dir}")

        if output_dir == plugin_dir or plugin_dir in output_dir.parents:
            cls._fail("Output folder must be outside of plugin folder")

        try:
            manifest = PluginScanner.get_plugin_manifest(plugin_file)
            if not manifest: raise Exception()
        
        except Exception as e:
            cls._fail(f"Could not load plugin manifest from plugin.py: {e}")

        if manifest.package_id != plugin_dir.name:
            cls._fail(
                f"Folder name {plugin_dir.name} must match the manifest package_id (which is {manifest.package_id})"
            )

        info = PluginArchive(**manifest.__dict__)

        try:
            archive_path, file_count = PluginPacker.pack(plugin_dir, info, output_dir, zip_suffix)
            sha256 = PluginUnpacker._sha256(archive_path)
            archive_path.with_suffix(archive_path.suffix + ".sha256").write_text(f"{sha256} {archive_path.name}", encoding="utf-8")
        
        except Exception as e:
            cls._fail(str(e))

        size_kb = archive_path.stat().st_size / 1024
        print(f"\nPacked {manifest.package_id} {manifest.plugin_version}")
        print(f"    files:   {file_count}")
        print(f"    size:    {size_kb:,.1f} KiB")
        print(f"    archive: {archive_path}\n")
        print(f"    sha256: {sha256}\n")

    @staticmethod
    def _fail(message: str):
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)

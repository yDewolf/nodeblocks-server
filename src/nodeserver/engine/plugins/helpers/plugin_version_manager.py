from typing import Optional
from packaging.version import Version, parse as parse_version

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.exceptions.plugin.plugin_exceptions import IncompatibleApiVersionPluginError, IncompatibleEngineVersionPluginError
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import IncompatibleVersionPluginError, PluginMissingDependency
from nodeserver.engine.helpers.version_helper import VersionHelper
from nodeserver.engine.plugins.api.plugin_api_version import CURRENT_PLUGIN_API_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

import logging
logger = logging.getLogger("nds.plugins")

class PluginVersionManager:
    engine_version: Version
    plugin_api_version: Version
    
    def __init__(
        self, 
        current_engine_version: str = CURRENT_ENGINE_VERSION,
        current_api_version: str = CURRENT_PLUGIN_API_VERSION
    ):
        self.engine_version = parse_version(current_engine_version)
        self.plugin_api_version = parse_version(current_api_version)

    def validate_plugin_requirements(
        self, 
        plugin_manifest: PluginManifest,
        installed_plugins: dict[str, PluginManifest]
    ):
        self.validate_api_compatibility(
            plugin_manifest.plugin_api_version, plugin_manifest.package_id
        )
        self.validate_engine_compatibility(
            plugin_manifest.engine_version, plugin_manifest.package_id
        )
        self.validate_plugin_dependencies(
            plugin_manifest, installed_plugins
        )

    def validate_engine_compatibility(
        self, engine_version_req: Optional[str], package_id: str
    ) -> None:
        if not engine_version_req:
            logger.warning("Plugin %s is missing engine version requirement. Plugin will be used anyway.", package_id)
            return

        specifier = VersionHelper._parse_semver_specifier(engine_version_req)
        if self.engine_version not in specifier:
            raise IncompatibleEngineVersionPluginError(
                package_id,
                engine_version_req,
                str(self.engine_version),
            )

    def validate_api_compatibility(
        self, api_version_req: Optional[str], package_id: str
    ) -> None:
        if not api_version_req:
            logger.warning("Plugin %s is missing plugin api version requirement. Plugin will be used anyway.", package_id)
            return

        specifier = VersionHelper._parse_semver_specifier(api_version_req)

        if self.plugin_api_version not in specifier:
            raise IncompatibleApiVersionPluginError(
                package_id,
                api_version_req,
                str(self.plugin_api_version),
            )

    def validate_plugin_dependencies(
        self, plugin_manifest: PluginManifest, installed_plugins: dict[str, PluginManifest]
    ) -> None:
        for dep_package_id, version_req in plugin_manifest.dependencies.items():
            if dep_package_id not in installed_plugins:
                raise PluginMissingDependency(
                    plugin_id=plugin_manifest.package_id,
                    loaded_plugins=list(installed_plugins.keys()),
                    plugin_dependencies=plugin_manifest.dependencies,
                )

            installed_manifest = installed_plugins[dep_package_id]
            installed_version = parse_version(installed_manifest.plugin_version)

            specifier = VersionHelper._parse_semver_specifier(version_req)

            if installed_version not in specifier:
                raise IncompatibleVersionPluginError(
                    plugin_id=plugin_manifest.package_id,
                    dependency_id=dep_package_id,
                    target_version=version_req,
                    current_version=installed_manifest.plugin_version,
                )

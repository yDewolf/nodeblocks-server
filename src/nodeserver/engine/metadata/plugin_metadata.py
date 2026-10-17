
from nodeserver.protocols.manifest.metadata.datatype_meta import DataTypeMeta
from nodeserver.protocols.manifest.metadata.metadata_header import MetadataManifest
from nodeserver.protocols.manifest.metadata.node_meta import DEFAULT_CATEGORY, DEFAULT_NODE_TAG, NodeTypeMeta, ParameterMeta, SlotMeta
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

# TODO: talvez implementar um metadata compiler que importa as classes
# e gera metadata a partir de DocString
class PluginMetadataGenerator:
    def generate_from_manifest(self, manifest: ManifestPackage) -> MetadataManifest:
        return MetadataManifest(
            package_id=manifest.package_id,
            package_version=manifest.version,
            meta_version=0,
            tags={"default": DEFAULT_NODE_TAG},
            categories={"default": DEFAULT_CATEGORY},
            data_types=self.generate_datatype_meta(manifest.data_types),
            node_types=self.generate_nodetype_meta(manifest.node_types)
        )


    def generate_datatype_meta(self, datatypes: dict[str, DataTypeSpec]) ->  dict[str, DataTypeMeta]:
        meta: dict[str, DataTypeMeta] = {}
        for id, datatype in datatypes.items():
            meta[datatype.id] = DataTypeMeta(
                capitalized_name=datatype.id,
                description=""
            )

        return meta

    def generate_nodetype_meta(self, nodetypes: dict[str, NodeTypeSpec]) -> dict[str, NodeTypeMeta]:
        meta: dict[str, NodeTypeMeta] = {}
        for id, nodetype in nodetypes.items():
            meta[nodetype.id] = NodeTypeMeta(
                capitalized_name=nodetype.id,
                category=DEFAULT_CATEGORY,
                parameter_meta={
                    param_id: ParameterMeta(capitalized_name=param_spec.label or param_id)
                    for param_id, param_spec in nodetype.parameters.items()
                },
                slot_meta={
                    slot_id: SlotMeta(capitalized_name=slot_id)
                    for slot_id, slot_spec in nodetype.slots.items()
                }
            )

        return meta

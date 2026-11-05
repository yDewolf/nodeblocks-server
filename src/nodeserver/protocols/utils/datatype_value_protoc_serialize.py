import json

from nodeserver.generated.protocols import datatype_value_pb2
from nodeserver.protocols.manifest.node.datatype_value_meta import ArrayMetadata, FileMetadata, SerializedDataTypeValue

def serialize_datatype_value(data_val: SerializedDataTypeValue) -> datatype_value_pb2.SerializedDataTypeValueMessage:
    proto_val = datatype_value_pb2.SerializedDataTypeValueMessage()
    
    val = data_val.value
    if isinstance(val, str):
        proto_val.value.string_value = val

    elif isinstance(val, bool):
        proto_val.value.bool_value = val

    elif isinstance(val, int):
        proto_val.value.int_value = val

    elif isinstance(val, float):
        proto_val.value.float_value = val

    elif val is None:
        proto_val.value.string_value = "null"
        
    else:
        proto_val.value.json_serialized_value = json.dumps(val)

    if data_val.metadata:
        meta = data_val.metadata
        if isinstance(meta, ArrayMetadata):
            proto_val.metadata.type = datatype_value_pb2.DATA_TYPE_ARRAY
            proto_val.metadata.array_metadata.shape.extend(meta.shape)
            if meta.min is not None:
                proto_val.metadata.array_metadata.min = meta.min
            
            if meta.max is not None:
                proto_val.metadata.array_metadata.max = meta.max
                
        elif isinstance(meta, FileMetadata):
            proto_val.metadata.type = datatype_value_pb2.DATA_TYPE_FILE
            proto_val.metadata.file_metadata.is_artifact = meta.is_artifact

    return proto_val
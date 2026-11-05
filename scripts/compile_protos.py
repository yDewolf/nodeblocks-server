from pathlib import Path
from grpc_tools import protoc

def compile_protos():
    root_dir = Path(__file__).resolve().parent.parent
    proto_root_dir = root_dir / "src/protos"
    out_dir = root_dir / "src/nodeserver/generated"

    if not proto_root_dir.exists():
        print(f"Couldn't find protos dir in: {proto_root_dir}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    proto_files = list(proto_root_dir.rglob("*.proto"))
    if not proto_files:
        print("Couldn't find any .proto file")
        return

    for proto_file in proto_files:
        print(f"Compiling: {proto_file.relative_to(proto_root_dir)}...")
        command = [
            'grpc_tools.protoc',
            f'-I{proto_root_dir}',
            f'--python_out={out_dir}',
            str(proto_file)
        ]
        
        result = protoc.main(command)
        if result != 0:
            raise RuntimeError(f"Failed to compile: {proto_file.name}")

    print("Compiled protobufs successfully")

if __name__ == "__main__":
    compile_protos()
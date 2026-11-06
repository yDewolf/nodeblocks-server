import importlib.util
import re
from pathlib import Path
from grpc_tools import protoc

def check_mypy_protobuf_installed() -> bool:
    return importlib.util.find_spec("mypy_protobuf") is not None

def compile_protos():
    src_dir = Path(__file__).resolve().parent.parent.parent
    proto_root_dir = src_dir / "protos"
    out_dir = src_dir / "nodeserver/generated"

    if not proto_root_dir.exists():
        print(f"Couldn't find protos dir in: {proto_root_dir}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    proto_files = list(proto_root_dir.rglob("*.proto"))
    if not proto_files:
        print("Couldn't find any .proto file")
        return

    has_mypy_protobuf = check_mypy_protobuf_installed()
    if has_mypy_protobuf:
        print("mypy-protobuf detected: type stubs (.pyi) will be generated.")
    else:
        print("mypy-protobuf not installed: skipping type stubs generation.")

    for proto_file in proto_files:
        print(f"Compiling: {proto_file.relative_to(proto_root_dir)}...")
        command = [
            'grpc_tools.protoc',
            f'-I{proto_root_dir}',
            f'--python_out={out_dir}',
        ]

        if has_mypy_protobuf:
            command.append(f'--mypy_out={out_dir}')

        command.append(str(proto_file))
        
        result = protoc.main(command)
        if result != 0:
            raise RuntimeError(f"Failed to compile: {proto_file.name}")

    for generated_file in out_dir.rglob("*_pb2.py"):
        content = generated_file.read_text(encoding="utf-8")
        
        relative_path = generated_file.relative_to(out_dir)
        depth = len(relative_path.parts) - 1
        
        if depth > 0:
            parent_dots = '.' * (depth + 1)
        
            def replace_relative_import(match: re.Match[str]):
                module_name = match.group(1)
                import_stuff = match.group(2)
                return f"from {parent_dots}{module_name} import {import_stuff}"

            pattern = r'^from ([a-zA-Z0-9_]+) import (.*_pb2)'
            updated_content = re.sub(pattern, replace_relative_import, content, flags=re.MULTILINE)
            
            if content != updated_content:
                generated_file.write_text(updated_content, encoding="utf-8")

    print("Compiled protobufs successfully")

if __name__ == "__main__":
    compile_protos()
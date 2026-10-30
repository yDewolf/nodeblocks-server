from pydantic import BaseModel, ConfigDict


class DataModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
    )

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class NamespaceModel(DataModel):
    namespace: str
    id: str

    @property
    def fqn(self) -> str:
        return make_namespace_fqn(self.namespace, self.id)

def make_namespace_fqn(namespace: str, id: str):
    return f"{namespace}:{id}"

def split_fqn(fqn: str) -> tuple[str, str]:
    split = fqn.split(":", 1)
    if len(split) != 2:
        raise Exception(f"Invalid Fully Qualified Name: {fqn}")
    
    return split[0], split[1]
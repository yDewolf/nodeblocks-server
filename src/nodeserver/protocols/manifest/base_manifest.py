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
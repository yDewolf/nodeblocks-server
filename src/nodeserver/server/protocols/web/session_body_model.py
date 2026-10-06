from pydantic import BaseModel


# TODO: depender de autenticação do usuário
class CreateSessionTokenModel(BaseModel):
    user_id: str


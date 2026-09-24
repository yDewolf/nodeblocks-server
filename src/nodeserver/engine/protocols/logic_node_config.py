from dataclasses import dataclass

@dataclass
class LogicNodeConfig:
    bypass_cache: bool = False
    order_independent: bool = True # TODO: implementar ordem de conexões para slots que recebem mais de uma entrada


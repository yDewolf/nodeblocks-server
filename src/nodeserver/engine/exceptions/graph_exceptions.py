# TODO: adicionar campos para popular essas exceções com 
# os slots, nodes que estão com problema para usar dps
# nas notificações do server

class ConnectionValidationError(ValueError):
    pass

class IncompatibleSlotsError(ConnectionValidationError):
    pass

class MaxConnectionReached(ConnectionValidationError):
    pass

class CyclicConnectionError(ConnectionValidationError):
    pass


class CyclicGraphError(ValueError):
    pass


class WorldError(Exception):
    pass


class EntityNotFound(WorldError):
    pass


class InvalidReference(WorldError):
    pass

class UnknownEntityType(WorldError):
    pass

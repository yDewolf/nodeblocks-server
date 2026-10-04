from enum import Flag, auto

class ScenePermission(Flag):
    NONE = 0
    READ = auto()
    EXECUTE = auto()
    EDIT = auto()
    ADMIN = auto()
    
    VIEWER = READ
    OPERATOR = READ | EXECUTE
    EDITOR = READ | EXECUTE | EDIT
    ALL = READ | EXECUTE | EDIT | ADMIN


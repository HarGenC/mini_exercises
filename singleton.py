from import_singleton import instance # С помощью импортов синглтон

class AddSingletonMeta(type): # С помощью метакласса
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    
class MetaSingleton(metaclass=AddSingletonMeta):
    pass

class Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs): # С помощью метода __new__
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_initialized'):
            self._initialized = True


first = Singleton()
second = Singleton()

assert first is second

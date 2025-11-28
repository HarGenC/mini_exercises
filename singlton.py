from import_singlton import instance # С помощью импортов синглтон

class AddSingltonMeta(type): # С помощью метакласса
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    
class MetaSinglton(metaclass=AddSingltonMeta):
    pass

class Singlton:
    _instance = None
    def __new__(cls, *args, **kwargs): # С помощью метода __new__
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    pass

first = Singlton()
second = Singlton()

if first is second:
    print("good")
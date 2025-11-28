#Напишите метакласс, который автоматически добавляет атрибут created_at с текущей датой и временем к любому классу, который его использует.

from datetime import datetime
import time

class AddAttrMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        
        original_init = getattr(cls, '__init__', None)
        
        def new_init(self, *args, **kwargs):
            self.created_at = datetime.now()
            if original_init:
                original_init(self, *args, **kwargs)
        
        # Заменяем __init__ класса
        cls.__init__ = new_init

    #def __init__(cls, name, bases, attrs):
    #    super().__init__(name, bases, attrs)
    #   cls.created_at = datetime.now()

class A(metaclass=AddAttrMeta):
    pass

a = A()

time.sleep(2)

b = A()

print(b.created_at)
print(a.created_at)
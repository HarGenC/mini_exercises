#Напишите метакласс, который автоматически добавляет атрибут created_at с текущей датой и временем к любому классу, который его использует.

from datetime import datetime
import time
from typing import Any, Dict, Tuple, Type

from click import pause

class AddAttrMeta(type):
    def __new__(
        mcs: Type['AddAttrMeta'], 
        name: str, 
        bases: Tuple[type, ...], 
        attrs: Dict[str, Any]
    ) -> 'AddAttrMeta':
        new_class = super().__new__(mcs, name, bases, attrs)
        new_class.created_at = datetime.now()
        
        return new_class

class A(metaclass=AddAttrMeta):
    pass

a = A()

time.sleep(2)

b = A()

print(b.created_at)
print(a.created_at)
assert a.created_at == b.created_at
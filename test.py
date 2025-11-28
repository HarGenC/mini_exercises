class N(): pass
class A(N): pass
class B(A): pass
class C(A): pass
class R(A): pass
class F(R): pass
class D(B, C, F): pass

print(D.__mro__)  # Выводит порядок разрешения методов для класса D
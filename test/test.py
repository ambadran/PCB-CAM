
class A:
    def __new__(cls, int_):

        cls.set_class_map()

        return cls.map_[int_]

    @classmethod
    def set_class_map(cls):
        cls.map_  = {0: 'a', 1: 'b'}

    def test(self):
        print('run test')

a = A(1)

print(a)

def test():
    return NotImplemented

test()

class B():
    def __init__(self):
        pass

class C():
    def __init__(self):
        pass



b = B()
c = C()


print(type(b))
print(type(c))
print(type(c) == type(b))

print(type(int))

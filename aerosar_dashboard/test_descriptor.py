class ReadOnly:
    def __get__(self, obj, objtype=None):
        return 1

    def __set__(self, obj, value):
        # Implement your setter logic here, e.g., storing the value in obj
        pass

class A:
    x = ReadOnly()

try:
    A().x = 2
except Exception as e:
    import sys
    print(repr(e), file=sys.stderr)

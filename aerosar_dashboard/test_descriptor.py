class ReadOnly:
    def __get__(self, obj, objtype=None):
        return 1

class A:
    x = ReadOnly()

try:
    A().x = 2
except Exception as e:
    import sys
    print(repr(e), file=sys.stderr)

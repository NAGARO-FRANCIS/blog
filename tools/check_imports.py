import sys

def show(name):
    try:
        m = __import__(name)
        print(f"{name} -> {getattr(m, '__file__', 'built-in')}")
    except Exception as e:
        print(f"{name} import failed: {type(e).__name__}: {e}")

show('accounts')
show('ivoire')
print('sys.path[0]=', sys.path[0])

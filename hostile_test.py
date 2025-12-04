"""
Hostile environment test for pycheck.
This script sabotages the Python environment before importing pycheck.
If pycheck crashes with a traceback, the attack wins.
If pycheck handles errors gracefully, pycheck wins.
"""
import sys
import builtins
import types
import pathlib

print("=== HOSTILE ENVIRONMENT TEST ===")
print("Setting up hostile environment...")

# 1. Corrupt sys.modules
sys.modules['_fake_none_module'] = None
sys.modules['_fake_int_module'] = 42
recursive = []
recursive.append(recursive)
sys.modules['_fake_recursive_module'] = recursive

# 2. Break builtins - save originals first so we can still import
_real_import = builtins.__import__
_real_open = builtins.open

def broken_import(name, *args, **kwargs):
    if name.startswith('_fake_'):
        raise ImportError("Hostile takeover: import is broken!")
    return _real_import(name, *args, **kwargs)

builtins.__import__ = broken_import

def broken_open(path, *args, **kwargs):
    if '_fake_' in str(path):
        raise OSError("Hostile takeover: open is broken!")
    return _real_open(path, *args, **kwargs)

builtins.open = broken_open

# 3. Simulate disk errors - patch pathlib for fake paths
_real_read_text = pathlib.Path.read_text

def broken_read_text(self, *args, **kwargs):
    if '_fake_' in str(self):
        raise OSError("Hostile takeover: disk read error!")
    return _real_read_text(self, *args, **kwargs)

pathlib.Path.read_text = broken_read_text

# 4. Circular import scenario
class Circular(types.ModuleType):
    _depth = 0
    def __getattr__(self, name):
        Circular._depth += 1
        if Circular._depth > 100:
            raise RecursionError("Hostile circular import!")
        return getattr(self, name)

sys.modules['_fake_circular'] = Circular('_fake_circular')

print("Hostile environment ready.")
print()

# Now, try to import pycheck and run it
print("=== IMPORTING PYCHECK ===")
try:
    import pycheck
    print(f"pycheck imported successfully. Version: {pycheck.__version__}")
except Exception as e:
    print(f"CRASH during import: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== TESTING get_failed_imports(OS) ===")
try:
    failed = pycheck.get_failed_imports(pycheck.OS)
    print(f"get_failed_imports(OS) returned: {failed}")
except Exception as e:
    print(f"CRASH during get_failed_imports(OS): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== TESTING get_failed_imports(ALL) ===")
try:
    failed = pycheck.get_failed_imports(pycheck.ALL)
    print(f"get_failed_imports(ALL) returned: {len(failed)} failures")
except Exception as e:
    print(f"CRASH during get_failed_imports(ALL): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== TESTING doSanityCheck(OS) ===")
try:
    result = pycheck.doSanityCheck(pycheck.OS)
    print(f"doSanityCheck(OS) returned: {result}")
except Exception as e:
    print(f"CRASH during doSanityCheck(OS): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== TESTING doSanityCheck(ALL) ===")
try:
    result = pycheck.doSanityCheck(pycheck.ALL)
    print(f"doSanityCheck(ALL) returned: {result}")
except Exception as e:
    print(f"CRASH during doSanityCheck(ALL): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== PYCHECK SURVIVED! IT WINS! ===")

"""
HOSTILE environment test v3 for pycheck.
This test is more realistic - it corrupts the environment AFTER pycheck imports
but BEFORE it runs checks. This simulates a truly broken Python environment.
"""
import sys
import types

print("=== HOSTILE ENVIRONMENT TEST v3 ===")

# First, import pycheck cleanly
print("[0] Importing pycheck cleanly...")
import pycheck
print(f"    pycheck {pycheck.__version__} imported successfully")

# ============================================================
# Now corrupt the environment
# ============================================================
print()
print("[1] Corrupting sys.modules with pathological objects...")

# A module that explodes on any attribute access
class ExplodingModule(types.ModuleType):
    def __getattr__(self, name):
        raise RuntimeError(f"BOOM! Tried to access {name} on exploding module")
    def __dir__(self):
        raise RuntimeError("BOOM! Tried to dir() exploding module")
    def __repr__(self):
        raise RuntimeError("BOOM! Tried to repr() exploding module")

# A module with infinite recursion
class RecursiveModule(types.ModuleType):
    def __getattr__(self, name):
        return getattr(self, name)  # Infinite recursion

# A module that's None
sys.modules['ssl'] = None
sys.modules['socket'] = None
sys.modules['_ssl'] = None

# Modules that explode
sys.modules['http'] = ExplodingModule('http')
sys.modules['urllib'] = ExplodingModule('urllib')
sys.modules['email'] = ExplodingModule('email')

# Modules with recursion
sys.modules['xml'] = RecursiveModule('xml')
sys.modules['html'] = RecursiveModule('html')

# Integer where module should be
sys.modules['json'] = 42
sys.modules['csv'] = []
sys.modules['re'] = {'not': 'a module'}

# Self-referential nightmare
circular = []
circular.append(circular)
sys.modules['pickle'] = circular

print("    Done corrupting sys.modules")

# ============================================================
# ATTACK 2: Corrupt importlib.metadata
# ============================================================
print()
print("[2] Corrupting importlib.metadata...")

import importlib.metadata

_real_distributions = importlib.metadata.distributions

def hostile_distributions():
    """Yield some broken distribution objects mixed with real ones."""
    count = 0
    for dist in _real_distributions():
        count += 1
        if count % 5 == 0:
            # Every 5th distribution, yield a broken one
            class BrokenDist:
                def read_text(self, name):
                    raise OSError("Disk read error!")
                @property
                def files(self):
                    raise RuntimeError("Files exploded!")
                @property
                def metadata(self):
                    raise ValueError("Metadata is corrupted!")
            yield BrokenDist()
        else:
            yield dist

importlib.metadata.distributions = hostile_distributions

print("    Done corrupting importlib.metadata")

# ============================================================
# ATTACK 3: Corrupt tempfile
# ============================================================
print()
print("[3] Corrupting tempfile...")

import tempfile

_real_tempdir = tempfile.TemporaryDirectory

class BrokenTempDir:
    def __init__(self, *args, **kwargs):
        raise PermissionError("Cannot create temp directory!")
    def __enter__(self):
        raise PermissionError("Cannot enter temp directory!")
    def __exit__(self, *args):
        pass

tempfile.TemporaryDirectory = BrokenTempDir

print("    Done corrupting tempfile")

# ============================================================
# Run the tests
# ============================================================
print()
print("=" * 60)
print("RUNNING PYCHECK IN HOSTILE ENVIRONMENT")
print("=" * 60)

crashed = False

# Test 1: doSanityCheck(OS)
print()
print(">>> pycheck.doSanityCheck(pycheck.OS)")
try:
    result = pycheck.doSanityCheck(pycheck.OS)
    print(f"    Result: {result}")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    crashed = True

# Test 2: doSanityCheck(ALL)
print()
print(">>> pycheck.doSanityCheck(pycheck.ALL)")
try:
    result = pycheck.doSanityCheck(pycheck.ALL)
    print(f"    Result: {result}")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    crashed = True

# Test 3: get_failed_imports(OS)
print()
print(">>> pycheck.get_failed_imports(pycheck.OS)")
try:
    result = pycheck.get_failed_imports(pycheck.OS)
    print(f"    Result: {len(result)} failures: {result[:5]}...")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    crashed = True

# Test 4: get_failed_imports(ALL)
print()
print(">>> pycheck.get_failed_imports(pycheck.ALL)")
try:
    result = pycheck.get_failed_imports(pycheck.ALL)
    print(f"    Result: {len(result)} failures")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    crashed = True

# Test 5: check_ssl_support
print()
print(">>> pycheck.check_ssl_support()")
try:
    result = pycheck.check_ssl_support()
    print(f"    Result: {result}")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    crashed = True

# Test 6: check_filesystem_access
print()
print(">>> pycheck.check_filesystem_access()")
try:
    result = pycheck.check_filesystem_access()
    print(f"    Result: {result}")
except Exception as e:
    print(f"    CRASH: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    crashed = True

# Final verdict
print()
print("=" * 60)
if crashed:
    print("ATTACK WINS! PYCHECK CRASHED!")
    sys.exit(1)
else:
    print("PYCHECK SURVIVED! IT WINS!")
    sys.exit(0)

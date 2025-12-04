"""
ULTRA-HOSTILE environment test for pycheck.
This is the nuclear option - we break things BEFORE pycheck can even load.
"""
import sys
import builtins
import types

print("=== ULTRA-HOSTILE ENVIRONMENT TEST ===")
print("Breaking Python before pycheck can even import...")

# Save originals so we can still do SOME things
_real_import = builtins.__import__
_real_getattr = builtins.getattr
_real_hasattr = builtins.hasattr

# ============================================================
# ATTACK 1: Corrupt sys.modules with pathological objects
# ============================================================
print("[1] Corrupting sys.modules...")

# None module - this can crash code that does `import x; x.something`
sys.modules['importlib'] = None  # This is evil - pycheck uses importlib!

# Integer where module should be
sys.modules['pathlib'] = 42

# A module that raises on any attribute access
class ExplodingModule(types.ModuleType):
    def __getattr__(self, name):
        raise RuntimeError(f"BOOM! Tried to access {name}")
    def __dir__(self):
        raise RuntimeError("BOOM! Tried to dir()")

sys.modules['tempfile'] = ExplodingModule('tempfile')

# A module with recursive __getattr__
class RecursiveModule(types.ModuleType):
    def __getattr__(self, name):
        return getattr(self, name + "_")  # Infinite recursion

sys.modules['typing'] = RecursiveModule('typing')

# ============================================================
# ATTACK 2: Break builtins
# ============================================================
print("[2] Breaking builtins...")

import_call_count = 0
def hostile_import(name, globals=None, locals=None, fromlist=(), level=0):
    global import_call_count
    import_call_count += 1
    
    # Randomly fail some imports
    if import_call_count % 3 == 0:
        raise ImportError(f"Random import failure for {name}!")
    
    # Let some imports through so Python doesn't totally die
    return _real_import(name, globals, locals, fromlist, level)

builtins.__import__ = hostile_import

# ============================================================
# ATTACK 3: Corrupt sys itself
# ============================================================
print("[3] Corrupting sys...")

# Remove stdlib_module_names if it exists (forces fallback path)
if hasattr(sys, 'stdlib_module_names'):
    delattr(sys, 'stdlib_module_names')

# ============================================================
# Now try to import pycheck
# ============================================================
print()
print("=== ATTEMPTING TO IMPORT PYCHECK ===")

try:
    # We need to restore importlib first or nothing works
    del sys.modules['importlib']
    del sys.modules['pathlib'] 
    del sys.modules['tempfile']
    del sys.modules['typing']
    
    import pycheck
    print(f"pycheck imported! Version: {pycheck.__version__}")
except Exception as e:
    print(f"CRASH during import: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("=== ATTACK WINS! PYCHECK CRASHED! ===")
    sys.exit(1)

# ============================================================
# Test the API
# ============================================================
print()
print("=== TESTING API ===")

# Re-corrupt things now that pycheck is loaded
sys.modules['ssl'] = None
sys.modules['socket'] = ExplodingModule('socket')

try:
    result = pycheck.doSanityCheck(pycheck.OS)
    print(f"doSanityCheck(OS): {result}")
except Exception as e:
    print(f"CRASH in doSanityCheck(OS): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    failed = pycheck.get_failed_imports(pycheck.OS)
    print(f"get_failed_imports(OS): {len(failed)} failures")
except Exception as e:
    print(f"CRASH in get_failed_imports(OS): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    result = pycheck.check_ssl_support()
    print(f"check_ssl_support(): {result}")
except Exception as e:
    print(f"CRASH in check_ssl_support(): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    result = pycheck.check_filesystem_access()
    print(f"check_filesystem_access(): {result}")
except Exception as e:
    print(f"CRASH in check_filesystem_access(): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=== PYCHECK SURVIVED! IT WINS! ===")

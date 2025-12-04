"""
HOSTILE environment test v4 - The Final Boss
This test attacks pycheck with every dirty trick possible.
"""
import sys
import types
import builtins

print("=== HOSTILE ENVIRONMENT TEST v4 - THE FINAL BOSS ===")

# First, import pycheck cleanly
print("[0] Importing pycheck cleanly...")
import pycheck
print(f"    pycheck {pycheck.__version__} imported successfully")

# ============================================================
# ATTACK 1: Replace sys.modules with a hostile dict-like object
# ============================================================
print()
print("[1] Creating hostile sys.modules proxy...")

class HostileModulesDict(dict):
    """A dict that sometimes raises exceptions."""
    _access_count = 0
    
    def __getitem__(self, key):
        HostileModulesDict._access_count += 1
        if HostileModulesDict._access_count % 7 == 0:
            raise KeyError(f"Random failure accessing {key}")
        return super().__getitem__(key)
    
    def __contains__(self, key):
        if 'hostile' in str(key):
            raise RuntimeError("Checking for hostile module!")
        return super().__contains__(key)

# We can't actually replace sys.modules entirely (Python would crash),
# but we can corrupt individual entries
print("    Done (partial - full replacement would crash Python)")

# ============================================================
# ATTACK 2: Create modules that raise during import checks
# ============================================================
print()
print("[2] Creating explosive modules...")

class ModuleRaisesOnBool(types.ModuleType):
    def __bool__(self):
        raise ValueError("Cannot convert module to bool!")

class ModuleRaisesOnStr(types.ModuleType):
    def __str__(self):
        raise TypeError("Cannot convert module to string!")
    def __repr__(self):
        raise TypeError("Cannot repr module!")

class ModuleRaisesOnIter(types.ModuleType):
    def __iter__(self):
        raise StopIteration("Immediate stop!")
    def __getattr__(self, name):
        if name == '__iter__':
            raise AttributeError("No iteration!")
        return super().__getattribute__(name)

sys.modules['_hostile_bool'] = ModuleRaisesOnBool('_hostile_bool')
sys.modules['_hostile_str'] = ModuleRaisesOnStr('_hostile_str')
sys.modules['_hostile_iter'] = ModuleRaisesOnIter('_hostile_iter')

print("    Done")

# ============================================================
# ATTACK 3: Corrupt stdlib module detection
# ============================================================
print()
print("[3] Corrupting stdlib module detection...")

# If Python has stdlib_module_names, corrupt it
if hasattr(sys, 'stdlib_module_names'):
    # We can't modify the frozenset directly, but let's try replacing it
    try:
        # This will likely fail but let's try
        sys.stdlib_module_names = frozenset(['nonexistent_module_abc123'])
    except (TypeError, AttributeError):
        print("    (Cannot replace stdlib_module_names - it's read-only)")
        
print("    Done")

# ============================================================
# ATTACK 4: Corrupt specific modules that pycheck might use
# ============================================================
print()
print("[4] Corrupting modules pycheck might use internally...")

# Replace pathlib with a hostile version
_real_pathlib = sys.modules.get('pathlib')
class HostilePath:
    def __init__(self, *args, **kwargs):
        raise OSError("Cannot create path!")
    def __truediv__(self, other):
        raise OSError("Cannot divide path!")

# Don't actually replace pathlib - it would break too much
# But let's corrupt pkgutil for the fallback path
sys.modules['pkgutil'] = None

print("    Done")

# ============================================================
# ATTACK 5: Create recursive/circular module structures
# ============================================================
print()
print("[5] Creating recursive module structures...")

class RecursiveGetattr(types.ModuleType):
    _depth = 0
    def __getattr__(self, name):
        RecursiveGetattr._depth += 1
        if RecursiveGetattr._depth > 100:
            raise RecursionError("Too deep!")
        return getattr(self, name)

sys.modules['_recursive_module'] = RecursiveGetattr('_recursive')

# A module whose attributes are themselves
class SelfRef(types.ModuleType):
    @property
    def self(self):
        return self
    @property
    def nested(self):
        return {'self': self, 'nested': self.nested}  # Infinite!

sys.modules['_selfref'] = SelfRef('_selfref')

print("    Done")

# ============================================================
# ATTACK 6: Corrupt importlib.metadata more aggressively
# ============================================================
print()
print("[6] Aggressively corrupting importlib.metadata...")

import importlib.metadata

_real_distributions = importlib.metadata.distributions

def ultra_hostile_distributions():
    """Yield broken distributions that crash in various ways."""
    class CrashOnRead:
        def read_text(self, name):
            raise OSError("Disk on fire!")
        @property
        def files(self):
            raise MemoryError("Out of memory!")
        @property
        def metadata(self):
            raise SystemError("System error!")
    
    class CrashOnIter:
        def read_text(self, name):
            return None
        @property
        def files(self):
            # Return something that crashes when iterated
            class CrashIter:
                def __iter__(self):
                    raise RuntimeError("Cannot iterate!")
            return CrashIter()
        @property
        def metadata(self):
            return {}
    
    class InfiniteFiles:
        def read_text(self, name):
            return None
        @property
        def files(self):
            # Return an infinite iterator
            def infinite():
                i = 0
                while True:
                    yield f"file_{i}.py"
                    i += 1
                    if i > 1000:  # Safety limit
                        break
            return infinite()
        @property
        def metadata(self):
            return {'Name': 'infinite'}
    
    # Yield some broken ones first
    yield CrashOnRead()
    yield CrashOnIter()
    
    # Then yield real ones
    try:
        for dist in _real_distributions():
            yield dist
    except Exception:
        pass
    
    # And some more broken ones
    yield InfiniteFiles()

importlib.metadata.distributions = ultra_hostile_distributions

print("    Done")

# ============================================================
# Run the tests
# ============================================================
print()
print("=" * 60)
print("RUNNING PYCHECK IN ULTRA-HOSTILE ENVIRONMENT")
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
    import traceback
    traceback.print_exc()
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
    print(f"    Result: {len(result)} failures")
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

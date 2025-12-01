"""Demo of pycheck-tool usage — exactly as you requested."""
import pycheck_tool as pycheck

# Check OS (stdlib) libraries
pycheck_result = pycheck.doSanityCheck(pycheck.OS)

# Check ALL installed libraries (resource-heavy)
py_all = pycheck.doSanityCheck(pycheck.ALL)

if pycheck_result:
    # if pycheck_result returns True then the following appears:
    print("OS Library is good")

if py_all:
    # Resource heavy way. Checks ALL Libraries
    # Returns a Str object with every library checked
    print(py_all + " Libraries are fine!")

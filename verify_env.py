import os, sys
print("Python:", sys.executable)
print("CWD   :", os.getcwd())
try:
    import pytest; print("pytest:", pytest.__version__)
    import core; print("core OK:", core.__file__)
except Exception as e:
    print("ERROR:", e)

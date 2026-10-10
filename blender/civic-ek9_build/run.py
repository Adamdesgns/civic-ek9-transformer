"""Entry point. Execute inside Blender:

    exec(open('/.../blender/civic-ek9_build/run.py').read())

Reloads the ek9 package so edits on disk take effect."""
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.path.join(os.getcwd(), 'blender', 'civic-ek9_build')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
for name in [m for m in sys.modules if m == 'ek9' or m.startswith('ek9.')]:
    del sys.modules[name]
ek9 = importlib.import_module('ek9')

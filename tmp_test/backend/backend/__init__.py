import sys, os
parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, parent)
import importlib.util

spec = importlib.util.spec_from_file_location("backend", os.path.join(parent, "backend/__init__.py"))
real = importlib.util.module_from_spec(spec)
sys.modules["backend"] = real
spec.loader.exec_module(real)

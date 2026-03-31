import sys
import os
import importlib.util

# This is a fallback proxy package to allow `uvicorn backend.main:app` to work
# even if the current working directory is already `/backend` (which occurs
# if the Render "Root Directory" is incorrectly set to "backend").
# It dynamically adds the repository root to sys.path and proxies the import
# to the real `backend` module.

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if parent_dir not in sys.path:
    # Add the repository root to sys.path
    sys.path.insert(0, parent_dir)
    
real_backend_init = os.path.join(parent_dir, "backend", "__init__.py")

if os.path.exists(real_backend_init):
    spec = importlib.util.spec_from_file_location("backend", real_backend_init)
    real_backend = importlib.util.module_from_spec(spec)
    
    # Replace ourselves in sys.modules so subsequent imports like `backend.main`
    # correctly resolve to the parent `backend` directory.
    sys.modules["backend"] = real_backend
    spec.loader.exec_module(real_backend)

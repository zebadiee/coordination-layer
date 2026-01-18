import os

# Make 'model_layer.tools' a package that forwards to the real 'model-layer/tools' directory.
# This keeps tests working without moving the existing implementation files.
real_tools = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
if real_tools not in __path__:
    __path__.insert(0, real_tools)

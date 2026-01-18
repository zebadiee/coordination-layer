import os

# Expose the 'tools' directory as submodules under the 'model_layer' package.
# This shim keeps repository structure flat while allowing tests to import
# `model_layer.tools.*` as expected.
here = os.path.dirname(__file__)
tools_path = os.path.normpath(os.path.join(here, '..', 'tools'))
if tools_path not in __path__:
    __path__.append(tools_path)

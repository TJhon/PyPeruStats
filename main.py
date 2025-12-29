from pyperustats import print_tree

print_tree(
    ".",
    exclude_extensions=[".egg-info"],
    exclude_dirs=[".venv", "datos_inei", "__pycache__", ".git"],
)

# steps

# root: python -m pip install -e .
# probar local:  python -c "import pyperustats; print(pyperustats.__version__)"
# pip build: python -m pip install build
# build: python -m build
# twine: python -m pip install twine
# upload twine: twine upload dist/*

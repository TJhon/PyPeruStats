import os
from pathlib import Path
from typing import List, Optional


def print_tree(
    directory: str,
    exclude_extensions: Optional[List[str]] = None,
    indent: str = "",
    is_last: bool = True,
    icons: bool = True,
) -> None:
    """
    Imprime un árbol de directorios con formato personalizado.

    Args:
        directory (str): Ruta del directorio a mostrar
        exclude_extensions (List[str], opcional): Lista de extensiones a excluir (ej: ['.pyc', '.git'])
        indent (str): Sangría actual (usado recursivamente)
        is_last (bool): Indica si es el último elemento del nivel actual
        icons (bool): Indica si se deben mostrar iconos
    """
    # Iconos para diferentes tipos de elementos
    ICON_FOLDER = "📁" if icons else ""
    ICON_FILE = "📄" if icons else ""
    PIPE = "│   "
    ELBOW = "└── "
    TEE = "├── "
    PIPE_PREFIX = "│   "
    SPACE_PREFIX = "    "

    # Obtener el nombre base del directorio
    directory_path = Path(directory)
    if indent == "":  # Primer nivel
        print(f"{ICON_FOLDER} {directory_path.name}")

    # Filtrar y ordenar el contenido del directorio
    items = list(directory_path.iterdir())
    items.sort(
        key=lambda x: (not x.is_dir(), x.name.lower())
    )  # Ordenar directorios primero

    # Filtrar extensiones excluidas
    if exclude_extensions:
        items = [
            item
            for item in items
            if not any(item.name.endswith(ext) for ext in exclude_extensions)
        ]

    # Procesar cada elemento
    for index, item in enumerate(items):
        is_last_item = index == len(items) - 1
        item_prefix = ELBOW if is_last_item else TEE
        item_indent = indent + (SPACE_PREFIX if is_last else PIPE_PREFIX)

        if item.is_dir():
            print(f"{indent}{item_prefix}{ICON_FOLDER} {item.name}")
            print_tree(str(item), exclude_extensions, item_indent, is_last_item, icons)
        else:
            print(f"{indent}{item_prefix}{ICON_FILE} {item.name}")

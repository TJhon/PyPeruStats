import os
from pathlib import Path
from typing import List, Optional



def print_tree(
    directory: str,
    exclude_extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    indent: str = "",
    is_last: bool = True,
    icons: bool = True,
) -> None:
    """
    Imprime un árbol de directorios con formato personalizado.

    Args:
        directory (str): Ruta del directorio a mostrar
        exclude_extensions (List[str], opcional): Extensiones a excluir (ej: ['.pyc'])
        exclude_dirs (List[str], opcional): Nombres de carpetas a excluir (ej: ['.venv'])
        indent (str): Sangría actual
        is_last (bool): Indica si es el último elemento del nivel actual
        icons (bool): Indica si se deben mostrar iconos
    """

    ICON_FOLDER = "📁" if icons else ""
    ICON_FILE = "📄" if icons else ""
    ELBOW = "└── "
    TEE = "├── "
    PIPE_PREFIX = "│   "
    SPACE_PREFIX = "    "

    directory_path = Path(directory)

    # Primera línea: nombre del directorio raíz
    if indent == "":
        print(f"{ICON_FOLDER} {directory_path.name}")

    # Leer contenido
    items = list(directory_path.iterdir())

    # 🔎 EXCLUSIÓN POR NOMBRE DE CARPETA
    if exclude_dirs:
        items = [
            item
            for item in items
            if not (item.is_dir() and item.name in exclude_dirs)
        ]

    # 🔎 EXCLUSIÓN POR EXTENSIÓN
    if exclude_extensions:
        items = [
            item
            for item in items
            if not any(item.name.endswith(ext) for ext in exclude_extensions)
        ]

    # Ordenar: primero directorios
    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

    # Recorrer
    for index, item in enumerate(items):
        is_last_item = index == len(items) - 1
        item_prefix = ELBOW if is_last_item else TEE
        item_indent = indent + (SPACE_PREFIX if is_last else PIPE_PREFIX)

        if item.is_dir():
            print(f"{indent}{item_prefix}{ICON_FOLDER} {item.name}")
            print_tree(
                str(item),
                exclude_extensions=exclude_extensions,
                exclude_dirs=exclude_dirs,
                indent=item_indent,
                is_last=is_last_item,
                icons=icons,
            )
        else:
            print(f"{indent}{item_prefix}{ICON_FILE} {item.name}")
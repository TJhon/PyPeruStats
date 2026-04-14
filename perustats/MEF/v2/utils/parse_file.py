from pathlib import Path

import pandas as pd


def sanitize_filename(text: str) -> str:
    """
    Limpia texto para usar en nombre de archivo

    Args:
        text: Texto a limpiar

    Returns:
        Texto sanitizado
    """

    return "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text
    ).strip()


def filename_save(name: str, value: str, save_dir: Path) -> Path:
    """
    Genera la ruta completa para guardar un archivo

    Args:
        name: Nombre del grupo/categoría
        value: Valor específico
        save_dir: Directorio base

    Returns:
        Path completo del archivo
    """
    filename = f"{name}_{sanitize_filename(value)}.csv"
    filepath = save_dir / filename
    return filepath


def save_dataframe(df: pd.DataFrame, save_dir: Path, name: str, value: str) -> Path:
    """
    Guarda un dataframe en la ubicación especificada

    Args:
        df: DataFrame a guardar
        save_dir: Directorio base
        name: Nombre del grupo/categoría
        value: Valor específico

    Returns:
        Path del archivo guardado
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = filename_save(name, value, save_dir)
    df.to_csv(filepath, index=False)
    return filepath

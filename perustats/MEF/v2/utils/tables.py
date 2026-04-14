import re

import pandas as pd
from bs4 import BeautifulSoup


def filter_content(df: pd.DataFrame, rows=[]) -> pd.DataFrame:
    if len(rows) == 0:
        return df
        # Filtrar si se especifica búsqueda
    if rows and rows is not None:
        pattern = "|".join(map(re.escape, rows))
        df = df[df["concepto_region"].str.contains(pattern, case=False, na=False)]
    return df


def html_table_to_dataframe(
    soup: BeautifulSoup, columns: list, convert: bool = True
) -> pd.DataFrame:
    """
    Convierte la tabla HTML 'Data' en un DataFrame de pandas

    Args:
        soup: BeautifulSoup object con el HTML
        columns: Lista de nombres de columnas
        buscar: Texto a buscar en la columna 'concepto_region' (opcional)
        convert: Si True, convierte números a float

    Returns:
        DataFrame con los datos de la tabla
    """
    table = soup.find("table", class_="Data")

    if table is None:
        raise ValueError("No se encontró la tabla 'Data' en el HTML")

    rows = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")

        if not tds:
            continue

        row = []

        for i, td in enumerate(tds):
            text = td.get_text(strip=True)

            # En la primera columna, extraer el valor del input (código grp)
            if i == 0:
                input_tag = td.find("input")
                if input_tag:
                    text = input_tag.get("value", text)

            # Limpiar y convertir números (formato: 3,400,841.50 → 3400841.50)
            if convert and re.match(r"^[\d,]+\.?\d*$", text):
                text = text.replace(",", "")
                try:
                    text = float(text)
                except ValueError:
                    pass

            row.append(text)

        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    return df


def get_grp_from_row(df: pd.DataFrame, row_index: int = 0) -> str:
    """
    Extrae el código grp de una fila específica del DataFrame

    Args:
        df: DataFrame con los datos
        row_index: Índice de la fila (por defecto 0)

    Returns:
        Código grp como string
    """
    if len(df) == 0:
        raise ValueError("DataFrame vacío")

    if row_index >= len(df):
        raise ValueError(
            f"Índice {row_index} fuera de rango. DataFrame tiene {len(df)} filas"
        )

    return df.iloc[row_index]["codigo_grp"]


def find_row_by_text(df: pd.DataFrame, search_text: str) -> int:
    """
    Encuentra el índice de la primera fila que contiene el texto buscado

    Args:
        df: DataFrame con los datos
        search_text: Texto a buscar en la columna 'concepto_region'

    Returns:
        Índice de la fila encontrada

    Raises:
        ValueError: Si no se encuentra el texto
    """
    mask = df["concepto_region"].str.contains(search_text, case=False, na=False)

    if not mask.any():
        raise ValueError(f"No se encontró ninguna fila con el texto: '{search_text}'")

    return mask.idxmax()


if __name__ == "__main__":
    html = """
    <table class="Data">
        <tr>
            <td><input value="001"/></td>
            <td>Transferencias de capital al Gobierno Regional de Lima</td>
            <td>1,200,000.50</td>
        </tr>
        <tr>
            <td><input value="002"/></td>
            <td>Gasto corriente en educación básica en Cusco</td>
            <td>850,300.00</td>
        </tr>
        <tr>
            <td><input value="003"/></td>
            <td>Inversión en infraestructura vial en Arequipa</td>
            <td>2,500,100.75</td>
        </tr>
        <tr>
            <td><input value="004"/></td>
            <td>Programa social en la región Puno</td>
            <td>430,000.00</td>
        </tr>
    </table>
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    columns = ["codigo", "concepto_region", "monto"]

    df = html_table_to_dataframe(
        soup,
        columns=columns,
    )
    # df = filter_content(
    #     df,
    #     rows=["lima", "cusco"],
    # )

    print(df)

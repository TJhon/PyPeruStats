"""
Constantes unificadas para scraping de SIAF MEF (Ingresos y Gastos)
"""

# ============================================
# CONFIGURACIÓN DE BOTONES COMPARTIDA
# ============================================

BUTTONS_BASE = {
    "nivel_gobierno": "ctl00$CPH1$BtnTipoGobierno",
    "generica": "ctl00$CPH1$BtnGenerica",
    "sub_generica": "ctl00$CPH1$BtnSubGenerica",
    "detalle_sub_generica": "ctl00$CPH1$BtnSubGenericaDetalle",
    "especifica": "ctl00$CPH1$BtnEspecifica",
    "detalle_especifica": "ctl00$CPH1$BtnEspecificaDetalle",
    "mes": "ctl00$CPH1$BtnMes",
    "departamento": "ctl00$CPH1$BtnDepartamento",
    "municipalidad": "ctl00$CPH1$BtnMunicipalidad",
    "funcion": "ctl00$CPH1$BtnFuncion",
    "fuente": "ctl00$CPH1$BtnFuenteAgregada",
    "rubro": "ctl00$CPH1$BtnRubro",
}

BUTTONS_V5_EXTENDED = {
    **BUTTONS_BASE,
    "sub_tipo_gobierno": "ctl00$CPH1$BtnSubTipoGobierno",
    "programa": "ctl00$CPH1$BtnPrograma",
    "sub_programa": "ctl00$CPH1$BtnSubPrograma",
    "categoria_presupuestal": "ctl00$CPH1$BtnProgramaPpto",
    "producto_proyecto": "ctl00$CPH1$BtnProdProy",
    "actividad_accion": "ctl00$CPH1$BtnAAO",
}

# ============================================
# LABELS DE BOTONES
# ============================================

LABELS_BASE = {
    "sub_generica": "Sub-Genéricas",
    "detalle_sub_generica": "Detalle Sub-Genéricas",
    "especifica": "Específicas",
    "detalle_especifica": "Detalle Específicas",
}

# Labels para Gastos V4 (2009-2011)
LABELS_GASTO_V4 = {
    **LABELS_BASE,
    "nivel_gobierno": "Niveles de Gobierno",
    "funcion": "Funciones",
    "fuente": "Fuentes",
    "mes": "Meses",
    "departamento": "Departamentos",
    "municipalidad": "Municipalidades",
}

# Labels para Gastos V5+ (2012+)
LABELS_GASTO_V5 = {
    **LABELS_BASE,
    "nivel_gobierno": "Nivel de Gobierno",
    "sub_tipo_gobierno": "Gob.Loc./Mancom.",
    "generica": "Genérica",
    "mes": "Mes",
    "fuentes": "Fuente",
    "programa": "Programa",
    "sub_programa": "Sub-Programa",
    "departamento": "Departamento",
    "municipalidad": "Municipalidad",
    "funcion": "Función",
    "rubro": "Rubros",
}

# Labels para Ingresos V4 (2009-2011)
LABELS_INGRESO_V4 = {
    "nivel_gobierno": "Nivel de Gobierno",
    "generica": "Genérica",
    "sub_generica": "Sub-Genérica",
    "fuente": "Fuente",
    "departamento": "Departamento",
    "municipalidad": "Municipalidad",
}

# Labels para Ingresos V5+ (2012+)
LABELS_INGRESO_V5 = {
    **LABELS_INGRESO_V4,
    "sub_tipo_gobierno": "Gob.Loc./Mancom.",
}

# ============================================
# COLUMNAS POR TIPO Y VERSIÓN
# ============================================

# Gastos
COLUMNS_GASTO_V4 = [
    "codigo_grp",
    "concepto_region",
    "pia",
    "pim",
    "compromiso",
    "devengado",
    "girado",
    "avance_p",
]

COLUMNS_GASTO_V5 = [
    "codigo_grp",
    "concepto_region",
    "pia",
    "pim",
    "certificacion",
    "compromiso_anual",
    "atencion_de_compromiso_mensual",
    "devengado",
    "girado",
    "avance_p",
]

# Ingresos (igual para todas las versiones)
COLUMNS_INGRESO = [
    "codigo_grp",
    "concepto_region",
    "pia",
    "pim",
    "recaudado",
]

# ============================================
# URLS POR TIPO Y VERSIÓN
# ============================================

# Gastos
GASTO_URL_V4 = (
    "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_4.aspx?y={year}&ap={ap}"
)
GASTO_URL_V5 = (
    "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_5.aspx?y={year}&ap={ap}"
)
GASTO_URL_V6 = (
    "https://apps5.mineco.gob.pe/transparencia/mensual/Navegar_6.aspx?y={year}&ap={ap}"
)
GASTO_URL_V7 = "https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_7.aspx?y={year}&ap={ap}"

# Ingresos
INGRESO_URL_V4 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_4.aspx?y={year}"
INGRESO_URL_V5 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_5.aspx?y={year}"
INGRESO_URL_V6 = "https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_6.aspx?y={year}"

# ============================================
# CONFIGURACIÓN COMPLETA POR TIPO
# ============================================

CONFIG_GASTO = {
    "v4": {
        "years": range(2009, 2012),
        "url": GASTO_URL_V4,
        "buttons": BUTTONS_BASE,
        "button_labels": LABELS_GASTO_V4,
        "columns": COLUMNS_GASTO_V4,
    },
    "v5": {
        "years": range(2012, 2016),
        "url": GASTO_URL_V5,
        "buttons": BUTTONS_V5_EXTENDED,
        "button_labels": LABELS_GASTO_V5,
        "columns": COLUMNS_GASTO_V5,
    },
    "v6": {
        "years": range(2016, 2024),
        "url": GASTO_URL_V6,
        "buttons": BUTTONS_V5_EXTENDED,
        "button_labels": LABELS_GASTO_V5,
        "columns": COLUMNS_GASTO_V5,
    },
    "v7": {
        "years": range(2024, 2027),
        "url": GASTO_URL_V7,
        "buttons": BUTTONS_V5_EXTENDED,
        "button_labels": LABELS_GASTO_V5,
        "columns": COLUMNS_GASTO_V5,
    },
}

CONFIG_INGRESO = {
    "v4": {
        "years": range(2009, 2012),
        "url": INGRESO_URL_V4,
        "buttons": BUTTONS_BASE,
        "button_labels": LABELS_INGRESO_V4,
        "columns": COLUMNS_INGRESO,
    },
    "v5": {
        "years": range(2012, 2016),
        "url": INGRESO_URL_V5,
        "buttons": BUTTONS_V5_EXTENDED,
        "button_labels": LABELS_INGRESO_V5,
        "columns": COLUMNS_INGRESO,
    },
    "v6": {
        "years": range(2016, 2027),
        "url": INGRESO_URL_V6,
        "buttons": BUTTONS_V5_EXTENDED,
        "button_labels": LABELS_INGRESO_V5,
        "columns": COLUMNS_INGRESO,
    },
}

# ============================================
# HEADERS HTTP
# ============================================

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

# ============================================
# COLORES PARA PROGRESO
# ============================================

COLORS_PROGRESS = ["bold white", "bold cyan", "yellow", "cyan", "blue"]


# ============================================
# FUNCIONES DE DETECCIÓN DE VERSIÓN
# ============================================


def detect_version(year: int, tipo: str = "gasto") -> str:
    """
    Detecta qué versión de API usar según el año y tipo

    Args:
        year: Año a procesar
        tipo: "gasto" o "ingreso"

    Returns:
        String con la versión: "v4", "v5", "v6" o "v7"
    """
    if tipo == "gasto":
        if 2009 <= year <= 2011:
            return "v4"
        elif 2012 <= year <= 2015:
            return "v5"
        elif 2016 <= year <= 2023:
            return "v6"
        elif 2024 <= year <= 2026:
            return "v7"
    elif tipo == "ingreso":
        if 2009 <= year <= 2011:
            return "v4"
        elif 2012 <= year <= 2015:
            return "v5"
        elif 2016 <= year <= 2026:
            return "v6"
    else:
        raise ValueError(f"Tipo '{tipo}' no válido. Use 'gasto' o 'ingreso'")

    raise ValueError(f"Año {year} no soportado para tipo '{tipo}'")


def get_config(year: int, tipo: str = "gasto") -> dict:
    """
    Obtiene la configuración completa para un año y tipo específico

    Args:
        year: Año a procesar
        tipo: "gasto" o "ingreso"

    Returns:
        Diccionario con configuración (url, buttons, labels, columns)
    """
    version = detect_version(year, tipo)

    if tipo == "gasto":
        return CONFIG_GASTO[version]
    elif tipo == "ingreso":
        return CONFIG_INGRESO[version]
    else:
        raise ValueError(f"Tipo '{tipo}' no válido. Use 'gasto' o 'ingreso'")

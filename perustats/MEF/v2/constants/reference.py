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

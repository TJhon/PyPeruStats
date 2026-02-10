import requests
from bs4 import BeautifulSoup
from rich import print

print()


# constants

distrital = dict(prev_istr=4001)
provincial = dict()


session = requests.Session()
# session.headers = headers
response = session.get(URL_ELECCIONES)
soup = BeautifulSoup(response.content, "html.parser")


# id tipo proceso

options_procesos_electorales = soup.select_one("#IdTipoProceso").find_all("option")
procesos_electorales = [
    dict(eleccion_name=option.get_text(strip=True), id=option.get("value"))
    for option in options_procesos_electorales[1:]
]

# seleccionar: proceso electoral municipal distrital

proceso_electoral = [
    eleccion
    for eleccion in procesos_electorales
    if "distrital" in eleccion.get("eleccion_name").lower()
][0]

TOKEN = get_token(soup)


elecciones = listar_elecciones(proceso_electoral, TOKEN)

### ejemplo: Seleccionar el anio 2022, en la practica sera todos los o rango

YEAR = 2022

distrital_2022 = [e for e in elecciones if str(YEAR) in e.get("name_eleccion").lower()][
    0
]


def get_redirected_eleccion(eleccion: dict, prev_istr=4001):
    id_eleccion = eleccion.get("id_eleccion")
    r = session.post(
        URL_FICHA_ELECCION,
        data={"parameter1": id_eleccion},
        allow_redirects=False,
    )
    redirect_url = r.headers["Location"]

    # candidatos_resultados
    url_resultados = BASE_URL + redirect_url.replace(
        "_normativa_", "_candidatos-y-resultados_"
    )
    resultados = BeautifulSoup(session.get(url_resultados).content, "html.parser")

    id_group_eleccion = resultados.find("input", {"id": "IdGrupoEleccion"}).get("value")
    istr = f"{prev_istr}{id_eleccion}@{id_group_eleccion}"
    eleccion["id_group_eleccion"] = id_group_eleccion
    # se obtiene los lugares de resultados
    params = {"istrParameters": istr}
    payload = {"token": TOKEN}
    r_lugares = session.post(URL_RESULTADOS_ELECCION, params=params, json=payload)
    return BeautifulSoup(r_lugares.content)


soup_search_location = get_redirected_eleccion(distrital_2022)

regiones_opt = soup_search_location.select_one("#IdRegion").find_all("option")[1:]
regiones = [
    dict(id_region=opt.get("value"), region=opt.get_text(strip=True))
    for opt in regiones_opt
]

region_n = regiones[4]


provincias_n_m = listar_sub_loc(distrital_2022, region_n)

distritos_n_m_o = listar_sub_loc(distrital_2022, provincias_n_m[1], "distrito")

# Asumiendo que ya se tienen a todos los departamentos provincias y distritos


proceso_electoral_prov = [
    eleccion
    for eleccion in procesos_electorales
    if "provincial" in eleccion.get("eleccion_name").lower()
][0]


# https://infogob.jne.gob.pe/Eleccion/ListarElecciones
# https://infogob.jne.gob.pe/Eleccion/ListarElecciones
elecciones_prov = listar_elecciones(proceso_electoral_prov, TOKEN)

### ejemplo: Seleccionar el anio 2022, en la practica sera todos los o rango

YEAR = 2022

provincial_2022 = [
    e for e in elecciones if str(YEAR) in e.get("name_eleccion").lower()
][0]

provincial_location = get_redirected_eleccion(provincial_2022, 3001)

regiones_opt_distritla = provincial_location.select_one("#IdRegion").find_all("option")[
    1:
]
regiones_provincial = [
    dict(id_region=opt.get("value"), region=opt.get_text(strip=True))
    for opt in regiones_opt
]

region_n = regiones[4]

regiones


# si es a nivel provincial, entonces esta en vez de {distritos_n_m_o[0].get('id_distrito')} esta el del id_provincia
data_distrito = {
    "istrParameters": f"{distrital_2022.get('id_eleccion')}@{distritos_n_m_o[0].get('id_distrito')}@{distrital_2022.get('id_group_eleccion')}",
    "token": TOKEN,
}

resultados_en_distrito = requests.post(URL_LISTAR_RESULTADOS, data=data_distrito).json()

listar_elecciones()

print(resultados_en_distrito)
print(data_distrito)

from pyPeruStats import clean_names
import pandas as pd
enaho_metadata = 'https://raw.githubusercontent.com/TJhon/PyPeruStats/refs/heads/inei/MetadataSources/INEI/enaho_actualizado.csv'

endes_metadata = 'https://raw.githubusercontent.com/TJhon/PyPeruStats/refs/heads/inei/MetadataSources/INEI/endes_actualizado.csv'

enapres_metadata = 'https://raw.githubusercontent.com/TJhon/PyPeruStats/refs/heads/inei/MetadataSources/INEI/enapres_actualizado.csv'

metadata_enaho = pd.read_csv(enaho_metadata).assign(encuesta_ref = "enaho")
metadata_endes = pd.read_csv(endes_metadata).assign(encuesta_ref = "endes")
metada_enapres = pd.read_csv(enapres_metadata).assign(encuesta_ref = "enapres")

all_microdatos = pd.concat([metadata_enaho, metada_enapres, metadata_endes])
clean_names(all_microdatos)
all_microdatos.drop(columns=['nro', 'ficha', 'descargar', 'descargar_1',
       'descargar_2'], inplace=True)

def modules_microdatos(datos = all_microdatos):
    # endes = datos.query("encuesta_ref == @encuesta")
    endes_modules = datos.groupby(
        ['encuesta_ref', 'modulo']
    ).agg({
        "anio": lambda x: "_".join(sorted(set(map(str, x)))),
        'codigo_modulo': 'min'
        }).sort_values('codigo_modulo').reset_index()
    endes_modules['anio'] = endes_modules['anio'].str.split('_')
    endes_modules = endes_modules.explode('anio', ignore_index=True)#.assign(encuesta_ref = encuesta)
    endes_modules['anio'] = endes_modules['anio'].astype(int)
    return endes_modules
unique_microdatos = modules_microdatos()
all_microdatos.drop(columns=['codigo_modulo'], inplace=True)

microdatos_con_modulos_unicos = all_microdatos.merge(unique_microdatos, validate=None)
microdatos_con_modulos_unicos.to_csv("./MetadataSources/inei/microdatos_recolectados.csv", index=False)
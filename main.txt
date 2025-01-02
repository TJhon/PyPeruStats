# Ejemplo de uso
from pyPeruStats import MICRODATOS_INEI

enapres = MICRODATOS_INEI(survey="enaho")
modules = enapres.modules
print(modules)

descargados = enapres.search(
    [2021, 2023, 2004, 2006, 2007, 2008], [1, 2, 3, 8]
).download_default(force=False, remove_zip=False, workers=4)


result_files = descargados.organize_files(order_by="modules", delete_master_dir=True)
print(result_files)

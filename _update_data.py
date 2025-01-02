import json
from pyPeruStats.MTC.homologacion import TelMTC

## MTC

homologados_f = "./requests/MTC/homologacion.json"
with open(homologados_f, 'r') as hf:
    brands = json.load(hf).get("marcas")

for brand in brands:
    data = TelMTC(brand).fetch_data()
    print(data)

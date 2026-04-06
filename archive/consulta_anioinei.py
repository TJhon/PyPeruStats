import subprocess
from urllib.parse import quote

endes = "Encuesta Demográfica y de Salud Familiar - ENDES"

name = quote(endes, encoding="iso-8859-1")
print(name)
# Encuesta%20Demogr%E1fica%20y%20de%20Salud%20Familiar%20-%20ENDES
# Definir la URL y los datos
url = "https://proyectos.inei.gob.pe/microdatos/CambiaAnio.asp"
data = f"bandera=1&_cmbEncuesta={name}&_cmbAnno={str(2019)}&_cmbEncuesta0={name}"

# Ejecutar el comando curl mediante subprocess
try:
    result = subprocess.run(
        ["curl", url, "--data-raw", data],
        capture_output=True,  # Captura la salida (stdout) y errores (stderr)
        text=True,  # Devuelve la salida como string en lugar de bytes
        check=True,  # Lanza una excepción si el comando falla (código de salida != 0)
    )

    # Imprimir la respuesta del servidor
    print("Respuesta del servidor:")
    print(result.stdout)

except subprocess.CalledProcessError as e:
    print(f"Ocurrió un error al ejecutar curl: {e}")
    print(f"Error output: {e.stderr}")
except FileNotFoundError:
    print(
        "Error: 'curl' no está instalado o no está en las variables de entorno del sistema."
    )

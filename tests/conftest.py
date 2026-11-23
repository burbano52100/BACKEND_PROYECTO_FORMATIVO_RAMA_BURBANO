# Este archivo lo lee pytest antes de correr las pruebas

# os sirve para cambiar las variables de entorno
import os

# En las pruebas dejo reservar a cualquier hora (si no, las pruebas fallarían de noche)
os.environ["hora_apertura"] = "0"
# Pongo el cierre en 24 para que siempre esté abierto
os.environ["hora_cierre"] = "24"

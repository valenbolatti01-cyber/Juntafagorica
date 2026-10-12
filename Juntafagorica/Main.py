from shell import *
from pathlib import Path
memoria = inicializar_memoria()

ruta_csv = Path(__file__).with_name("procesos.csv")
procesos = cargar_procesos(ruta_csv)

for proceso in procesos:
    asignar_memoria(memoria, proceso)

mostrar_memoria(memoria)

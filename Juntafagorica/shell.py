import csv


class Proceso:
    def __init__(self, id_proceso, tamanio, tiempo_arribo, tiempo_irrupcion):
        self.id_proceso = id_proceso
        self.tamanio = tamanio
        self.tiempo_arribo = tiempo_arribo
        self.tiempo_irrupcion = tiempo_irrupcion

        self.tiempo_restante = tiempo_irrupcion
        self.estado = "Nuevo"

        self.tiempo_finalizacion = None
        self.tiempo_espera = 0
        self.tiempo_retorno = 0


def cargar_procesos(ruta_archivo):
    procesos = []
    ids = set()

    with open(ruta_archivo, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)

        columnas = {"id", "tamanio", "arribo", "irrupcion"}
        if lector.fieldnames is None or not columnas.issubset(lector.fieldnames):
            raise ValueError("El CSV debe tener: id,tamanio,arribo,irrupcion")

        for numero_fila, fila in enumerate(lector, start=2):
            try:
                id_proceso = fila["id"].strip()
                tamanio = int(fila["tamanio"])
                arribo = int(fila["arribo"])
                irrupcion = int(fila["irrupcion"])
            except (ValueError, TypeError, AttributeError) as error:
                raise ValueError(
                    f"Datos invalidos en la fila {numero_fila}"
                ) from error

            if not id_proceso or id_proceso in ids:
                raise ValueError(f"ID vacio o repetido en la fila {numero_fila}")
            if not 0 < tamanio <= 450 or arribo < 0 or irrupcion <= 0:
                raise ValueError(f"Valores fuera de rango en la fila {numero_fila}")

            ids.add(id_proceso)
            procesos.append(Proceso(id_proceso, tamanio, arribo, irrupcion))

            if len(procesos) > 10:
                raise ValueError("El archivo no puede contener mas de 10 procesos")

    return procesos


class ParticionMemoria:
    def __init__(self, id_particion, direccion_inicio, tamanio, id_proceso=None):
        self.id_particion = id_particion
        self.direccion_inicio = direccion_inicio
        self.tamanio = tamanio
        self.id_proceso = id_proceso

    def esta_libre(self):
        return self.id_proceso is None

    def asignar(self, id_proceso):
        self.id_proceso = id_proceso

    def liberar(self):
        self.id_proceso = None


def inicializar_memoria():
    memoria = [
        ParticionMemoria(1, 100, 450)
    ]
    return memoria


def renumerar_particiones(memoria):
    for numero, particion in enumerate(memoria, start=1):
        particion.id_particion = numero


def mostrar_memoria(memoria):
    columnas = ["ID", "Inicio", "Tamano", "Proceso", "Frag. Externa"]

    filas = []
    for particion in memoria:
        proceso = particion.id_proceso if particion.id_proceso is not None else "Libre"
        filas.append([particion.id_particion, particion.direccion_inicio,
                      particion.tamanio, proceso, 0])

    # Ancho de cada columna = lo más largo entre el título y sus valores
    anchos = []
    for i, titulo in enumerate(columnas):
        anchos.append(max([len(titulo)] + [len(str(fila[i])) for fila in filas]))

    separador = "+" + "+".join("-" * (ancho + 2) for ancho in anchos) + "+"

    def armar_fila(valores):
        celdas = [str(valor).center(ancho) for valor, ancho in zip(valores, anchos)]
        return "| " + " | ".join(celdas) + " |"

    print("--- Tabla De Particiones ---")
    print(separador)
    print(armar_fila(columnas))
    print(separador)
    for fila in filas:
        print(armar_fila(fila))
    print(separador)


def asignar_memoria(memoria, proceso):
    # Best-Fit: la partición libre más chica en la que entra el proceso
    mejor = None
    for particion in memoria:
        if particion.esta_libre() and particion.tamanio >= proceso.tamanio:
            if mejor is None or particion.tamanio < mejor.tamanio:
                mejor = particion

    if mejor is None:
        return False  # no hay lugar: el proceso queda Listo y Suspendido

    indice = memoria.index(mejor)
    sobrante = mejor.tamanio - proceso.tamanio

    mejor.tamanio = proceso.tamanio
    mejor.asignar(proceso.id_proceso)

    if sobrante > 0:
        nueva_particion = ParticionMemoria(
            0,
            mejor.direccion_inicio + proceso.tamanio,
            sobrante
        )
        memoria.insert(indice + 1, nueva_particion)

    renumerar_particiones(memoria)
    return True


def liberar_memoria(memoria, id_proceso):
    for particion in memoria:
        if particion.id_proceso == id_proceso:
            particion.liberar()
            break
    else:
        return False

    # Unir particiones libres contiguas
    i = 0
    while i < len(memoria) - 1:
        actual = memoria[i]
        siguiente = memoria[i + 1]
        if actual.esta_libre() and siguiente.esta_libre():
            actual.tamanio += siguiente.tamanio
            memoria.pop(i + 1)
        else:
            i += 1

    renumerar_particiones(memoria)
    return True

def seleccionar_srtf(procesos):
    candidatos = [
        proceso
        for proceso in procesos
        if proceso.estado in ("Listo", "Ejecucion")
    ]

    if not candidatos:
        return None

    return min(
        candidatos,
        key=lambda proceso: (
            proceso.tiempo_restante,
            proceso.tiempo_arribo,
            proceso.id_proceso
        )
    )

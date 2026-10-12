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
    columnas = ["ID", "Inicio", "Tamaño", "Proceso", "Frag. interna"]

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

    print("--- TABLA DE PARTICIONES ---")
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
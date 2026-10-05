class Proceso:
    def __init__(self, id_proceso, tamaño, tiempo_arribo, tiempo_irrupcion):
        self.id_proceso = id_proceso
        self.tamaño = tamaño
        self.tiempo_arribo = tiempo_arribo
        self.tiempo_irrupcion = tiempo_irrupcion

        self.tiempo_restante = tiempo_irrupcion
        self.estado = "Nuevo"

        self.tiempo_finalizacion = None
        self.tiempo_espera = 0
        self.tiempo_retorno = 0


class ParticionMemoria:
    def __init__(self, id_particion, direccion_inicio, tamaño, id_proceso=None):
        self.id_particion = id_particion
        self.direccion_inicio = direccion_inicio
        self.tamaño = tamaño
        self.id_proceso = id_proceso

    def esta_libre(self):
        return self.id_proceso is None

    def asignar(self):
        self.id_proceso = self.id_proceso

    def liberar(self):
        self.id_proceso = None


def inicializar_memoria():
    memoria = [
        ParticionMemoria(1, 100, 450)
    ]
    return memoria


def mostrar_memoria(memoria):
    print("TABLAS DE PARTICIONES")
    print("" \
    "==================================\n"
    "||ID | Inicio | Tamaño | Proceso||\n"
    "==================================\n"
    "")

    for particiones in memoria:
        proceso = particion.id_proceso

        if proceso is None:
            proceso = "Libre"

        print(particion.id_particion, particion.direccion_inicio, particion.tamaño, proceso)

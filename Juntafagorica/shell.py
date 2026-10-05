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
    print(""
    "==================================\n"
    "||ID | Inicio | Tamanio | Proceso||\n"
    "==================================\n"
    "")

    for particion in memoria:
        proceso = particion.id_proceso

        if proceso is None:
            proceso = "Libre"

        print(particion.id_particion, particion.direccion_inicio, particion.tamanio, proceso)


def asignar_memoria(memoria, proceso):
    for i, particion in enumerate(memoria):
        for particion in memoria:
            if particion.esta_libre() and particion.tamanio >= proceso.tamanio:

                sobrante = particion.tamanio - proceso.tamanio

                particion.tamanio = proceso.tamanio
                particion.id_proceso = proceso.id_proceso     # Si hay una particion libre suficientemente grande, asignar ahi el proceso

                if sobrante > 0:
                    nueva_particion = ParticionMemoria(
                        particion.id_particion + 1,
                        particion.direccion_inicio + proceso.tamanio,
                        sobrante
                    )

                    memoria.insert(i + 1, nueva_particion)

                return True

        return False

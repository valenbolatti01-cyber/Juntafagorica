import copy
import csv
import webbrowser
from visualizador import generar_html
from pathlib import Path
from shell import (
    cargar_procesos,
    inicializar_memoria,
    asignar_memoria,
    liberar_memoria,
    seleccionar_srtf,
)

MAX_PROCESOS_ACTIVOS = 5

def contar_activos(procesos):
    estados_activos = ("Listo", "Ejecucion", "Listo y Suspendido")
    return sum(
        1 for proceso in procesos
        if proceso.estado in estados_activos
    )


def admitir_procesos(memoria, procesos, tiempo):
    # Los suspendidos ya tienen un cupo lógico.
    # Se intenta asignarles memoria primero.
    for proceso in procesos:
        if proceso.estado == "Listo y Suspendido":
            if asignar_memoria(memoria, proceso):
                proceso.estado = "Listo"

    # Admitir procesos que ya arribaron, sin superar el límite de cinco.
    for proceso in procesos:
        if proceso.estado != "Nuevo" or proceso.tiempo_arribo > tiempo:
            continue

        if contar_activos(procesos) >= MAX_PROCESOS_ACTIVOS:
            break

        if asignar_memoria(memoria, proceso):
            proceso.estado = "Listo"
        else:
            proceso.estado = "Listo y Suspendido"


def calcular_estado_fragmentacion(memoria, procesos):
    huecos_libres = [
        particion.tamanio
        for particion in memoria
        if particion.esta_libre()
    ]

    libre_total = sum(huecos_libres)
    hueco_mayor = max(huecos_libres, default=0)
    frag_externa = libre_total - hueco_mayor

    suspendidos = [
        proceso
        for proceso in procesos
        if proceso.estado == "Listo y Suspendido"
    ]

    bloqueados_por_fragmentacion = [
        proceso.id_proceso
        for proceso in suspendidos
        if hueco_mayor < proceso.tamanio <= libre_total
    ]

    bloqueados_por_falta_total = [
        proceso.id_proceso
        for proceso in suspendidos
        if proceso.tamanio > libre_total
    ]

    return {
        "libre_total": libre_total,
        "hueco_mayor": hueco_mayor,
        "frag_externa": frag_externa,
        "bloqueados_por_fragmentacion": bloqueados_por_fragmentacion,
        "bloqueados_por_falta_total": bloqueados_por_falta_total,
    }


def mostrar_evento_consola(evento):
    print(f"\nTiempo {evento['tiempo']} - {evento['descripcion']}")
    print(f"Ejecucion: {evento['cpu']}")
    print(f"Nuevos: {', '.join(evento['nuevos']) or '-'}")
    print(f"Listos: {', '.join(evento['listos']) or '-'}")
    print(f"Listos y suspendidos: {', '.join(evento['suspendidos']) or '-'}")
    print(f"Terminados: {', '.join(evento['terminados']) or '-'}")

    filas_memoria = [
        [
            particion["id"],
            particion["inicio"],
            particion["tamano"],
            particion["proceso"] or "Libre",
            particion["fragmentacion"],
        ]
        for particion in evento["memoria"]
    ]

    imprimir_tabla(
        "Particiones de memoria",
        ["ID", "Inicio", "Tamano", "Proceso", "Frag. Interna"],
        filas_memoria,
    )

    print(
        f"Memoria libre total: {evento['libre_total']}K | "
        f"Hueco mayor: {evento['hueco_mayor']}K | "
        f"Fragmentacion externa: {evento['frag_externa']}K"
    )

    if evento["bloqueados_por_fragmentacion"]:
        ids = ", ".join(evento["bloqueados_por_fragmentacion"])
        print(
            f"No entran por fragmentacion externa: {ids}. "
            "El espacio libre total alcanza, pero esta separado."
        )

    if evento["bloqueados_por_falta_total"]:
        ids = ", ".join(evento["bloqueados_por_falta_total"])
        print(f"No hay memoria libre total suficiente para: {ids}.")


def registrar_evento(
    memoria, procesos, tiempo, motivo, ejecutando, eventos, paso_a_paso=False
):
    evento = {
        "tiempo": tiempo,
        "descripcion": motivo,
        "cpu": ejecutando.id_proceso if ejecutando else "Libre",

        "memoria": [
            {
                "id": p.id_particion,
                "inicio": p.direccion_inicio,
                "tamano": p.tamanio,
                "proceso": p.id_proceso,
                "fragmentacion": 0
            }
            for p in memoria
        ],

        "nuevos": [
            p.id_proceso for p in procesos if p.estado == "Nuevo"
        ],

        "listos": [
            p.id_proceso for p in procesos if p.estado == "Listo"
        ],

        "suspendidos": [
            p.id_proceso for p in procesos
            if p.estado == "Listo y Suspendido"
        ],

        "terminados": [
            p.id_proceso for p in procesos if p.estado == "Terminado"
        ]
    }

    evento.update(calcular_estado_fragmentacion(memoria, procesos))
    eventos.append(evento)

    if paso_a_paso:
        if len(eventos) > 1:
            input(
                f"\nPresiona Enter para avanzar al siguiente cambio "
                f"(tiempo {evento['tiempo']})..."
            )

        mostrar_evento_consola(evento)



def simular(procesos, paso_a_paso=False):
    memoria = inicializar_memoria()
    eventos = []
    procesos.sort(key=lambda p: (p.tiempo_arribo, p.id_proceso))

    tiempo = 0
    ejecutando = None
    llegadas_mostradas = set()

    while any(proceso.estado != "Terminado" for proceso in procesos):
        # 1) Arribos de este instante (todavía no mostrados).
        llegadas = [
            proceso
            for proceso in procesos
            if proceso.tiempo_arribo <= tiempo
            and proceso.id_proceso not in llegadas_mostradas
        ]

        for proceso in llegadas:
            llegadas_mostradas.add(proceso.id_proceso)

        # 2) Admisión (suspendidos primero, luego nuevos).
        admitir_procesos(memoria, procesos, tiempo)

        # 3) Evento de arribo: la CPU todavía no cambió de proceso.
        if llegadas:
            ids = ", ".join(p.id_proceso for p in llegadas)
            registrar_evento(
                memoria,
                procesos,
                tiempo,
                f"Arribo de proceso(s): {ids}",
                ejecutando,
                eventos,
                paso_a_paso,
            )

        # 4) Selección SRTF.
        elegido = seleccionar_srtf(procesos)

        # Si no hay procesos listos, avanzar hasta el próximo arribo.
        if elegido is None:
            proximos_arribos = [
                proceso.tiempo_arribo
                for proceso in procesos
                if proceso.estado == "Nuevo"
                and proceso.tiempo_arribo > tiempo
            ]

            if not proximos_arribos:
                raise RuntimeError(
                    "No hay procesos ejecutables ni próximos arribos."
                )

            tiempo = min(proximos_arribos)
            continue

        # 5) Si la CPU cambia de proceso, se registra el comienzo de ejecución.
        if elegido is not ejecutando:
            if ejecutando is not None:
                ejecutando.estado = "Listo"

            elegido.estado = "Ejecucion"
            ejecutando = elegido

            registrar_evento(
                memoria,
                procesos,
                tiempo,
                f"Comienzo de ejecución de: {ejecutando.id_proceso}",
                ejecutando,
                eventos,
                paso_a_paso,
            )

        # 6) Ejecutar una unidad de tiempo y volver a evaluar SRTF.
        ejecutando.tiempo_restante -= 1
        tiempo += 1

        if ejecutando.tiempo_restante == 0:
            finalizado = ejecutando
            finalizado.estado = "Terminado"
            finalizado.tiempo_finalizacion = tiempo
            finalizado.tiempo_retorno = (
                tiempo - finalizado.tiempo_arribo
            )
            finalizado.tiempo_espera = (
                finalizado.tiempo_retorno
                - finalizado.tiempo_irrupcion
            )

            liberar_memoria(memoria, finalizado.id_proceso)
            ejecutando = None

            registrar_evento(
                memoria,
                procesos,
                tiempo,
                f"Finalización de {finalizado.id_proceso}",
                None,
                eventos,
                paso_a_paso,
            )

    return procesos, tiempo, eventos


# VERIFICAR PORQUE SOLUCIONA PROBLEMAS QUE NO SABIAMOS QUE TENIAMOS

def seleccionar_archivo():
    """Abre el explorador y devuelve la ruta elegida, o None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as error:
        print(
            "\nNo esta disponible tkinter "
            f"({error}). Puedes cargar el CSV por ruta con la opcion 2."
        )
        return None

    ventana = None

    try:
        ventana = tk.Tk()
        ventana.withdraw()
        ventana.attributes("-topmost", True)

        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de procesos",
            initialdir=str(Path(__file__).parent),
            filetypes=[
                ("Archivos CSV", "*.csv"),
                ("Todos los archivos", "*.*"),
            ],
        )

        return Path(ruta) if ruta else None

    except tk.TclError as error:
        print(
            "\nNo se pudo abrir el explorador "
            f"({error}). Puedes cargar el CSV por ruta con la opcion 2."
        )
        return None

    finally:
        if ventana is not None:
            try:
                ventana.destroy()
            except tk.TclError:
                pass


def cargar_archivo():
    """Opcion 1. Devuelve (ruta, procesos) o None si no se pudo cargar."""
    ruta = seleccionar_archivo()

    if ruta is None:
        print("\nNo se selecciono ningun archivo.")
        return None

    try:
        procesos = cargar_procesos(ruta)
    except (OSError, ValueError, csv.Error) as error:
        print(f"\nArchivo invalido ({ruta.name}): {error}")
        return None

    if not procesos:
        print(
            f"\nArchivo invalido ({ruta.name}): "
            "el CSV debe incluir al menos un proceso."
        )
        return None

    print(f"\nArchivo cargado: {ruta.name} ({len(procesos)} procesos)")
    return ruta, procesos


def cargar_archivo_por_ruta():
    """Opcion 2. Pide la ruta por teclado. Devuelve (ruta, procesos) o None."""
    entrada = input("\nIngrese la ruta del archivo CSV: ").strip().strip('"').strip("'")

    if not entrada:
        print("\nNo se ingreso ninguna ruta.")
        return None

    ruta = Path(entrada)

    if not ruta.is_file():
        print(f"\nNo se encontro el archivo: {ruta}")
        return None

    try:
        procesos = cargar_procesos(ruta)
    except (OSError, ValueError, csv.Error) as error:
        print(f"\nArchivo invalido ({ruta.name}): {error}")
        return None

    if not procesos:
        print(
            f"\nArchivo invalido ({ruta.name}): "
            "el CSV debe incluir al menos un proceso."
        )
        return None

    print(f"\nArchivo cargado: {ruta.name} ({len(procesos)} procesos)")
    return ruta, procesos


def imprimir_tabla(titulo, columnas, filas):
    anchos = []

    for indice, columna in enumerate(columnas):
        ancho = max(
            len(str(columna)),
            *(len(str(fila[indice])) for fila in filas)
        )
        anchos.append(ancho)

    separador = "+" + "+".join(
        "-" * (ancho + 2) for ancho in anchos
    ) + "+"

    def formar_fila(valores):
        celdas = [
            str(valor).center(ancho)
            for valor, ancho in zip(valores, anchos)
        ]
        return "| " + " | ".join(celdas) + " |"

    print(f"\n{titulo}")
    print(separador)
    print(formar_fila(columnas))
    print(separador)

    for fila in filas:
        print(formar_fila(fila))

    print(separador)


def ejecutar_por_consola(procesos):
    """Ejecuta la simulacion y muestra eventos, memoria y estadisticas."""
    try:
        procesos, tiempo_total, eventos = simular(
            procesos,
            paso_a_paso=True,
        )
    except RuntimeError as error:
        print(f"\nNo se pudo completar la simulacion: {error}")
        return

    if not procesos:
        print("\nNo hay procesos para simular.")
        return

    cantidad = len(procesos)
    promedio_retorno = sum(
        proceso.tiempo_retorno for proceso in procesos
    ) / cantidad
    promedio_espera = sum(
        proceso.tiempo_espera for proceso in procesos
    ) / cantidad
    rendimiento = cantidad / tiempo_total if tiempo_total else 0

    filas_procesos = []

    for proceso in sorted(procesos, key=lambda p: p.id_proceso):
        filas_procesos.append([
            proceso.id_proceso,
            proceso.tiempo_arribo,
            proceso.tiempo_irrupcion,
            proceso.tiempo_finalizacion,
            proceso.tiempo_retorno,
            proceso.tiempo_espera,
        ])

    imprimir_tabla(
        "Estadisticas por proceso",
        [
            "ID",
            "Arribo",
            "Irrupcion",
            "Finalizacion",
            "Retorno",
            "Espera",
        ],
        filas_procesos,
    )

    imprimir_tabla(
        "Resumen del sistema",
        ["Estadistica", "Valor"],
        [
            ["Promedio de retorno", f"{promedio_retorno:.2f}"],
            ["Promedio de espera", f"{promedio_espera:.2f}"],
            ["Rendimiento", f"{rendimiento:.4f} procesos/unidad"],
        ],
    )


def generar_visualizador(procesos):
    # La simulacion modifica los procesos, por eso se usa una copia.
    procesos, tiempo_total, eventos = simular(copy.deepcopy(procesos))
    ruta_html = generar_html(eventos, procesos, tiempo_total)
    webbrowser.open(ruta_html.as_uri())


def mostrar_menu(nombre_archivo):
    print("\n=== Simulador MVT + SRTF ===")
    print(f"Archivo cargado: {nombre_archivo or 'ninguno'}")
    print("1. Cargar archivo por explorador de windows")
    print("2. Cargar archivo por ruta")
    print("3. Ejecutar por consola")
    print("4. Generar el html")
    print("5. Salir")


def menu():
    procesos = None
    nombre_archivo = None

    while True:
        mostrar_menu(nombre_archivo)
        opcion = input("Elegi una opcion: ").strip()

        if opcion in ("1", "2"):
            if opcion == "1":
                resultado = cargar_archivo()
            else:
                resultado = cargar_archivo_por_ruta()

            if resultado is not None:
                ruta, procesos = resultado
                nombre_archivo = ruta.name

        elif opcion in ("3", "4"):
            if procesos is None:
                print(
                    "\nNo hay un archivo cargado. "
                    "Primero usa la opcion 1 (Cargar archivo)."
                )
                continue

            if opcion == "3":
                ejecutar_por_consola(copy.deepcopy(procesos))
            elif opcion == "4":
                try:
                    generar_visualizador(procesos)
                except (RuntimeError, OSError) as error:
                    print(f"\nNo se pudo generar el visualizador: {error}")

        elif opcion == "5":
            print("Hasta luego.")
            break

        else:
            print("Opcion invalida. Elegi un numero del 1 al 5.")


if __name__ == "__main__":
    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\nSimulacion interrumpida. Hasta luego.")

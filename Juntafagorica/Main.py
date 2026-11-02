import copy
import csv
import html
import webbrowser
from pathlib import Path
from shell import (
    cargar_procesos,
    inicializar_memoria,
    asignar_memoria,
    liberar_memoria,
    mostrar_memoria,
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
        ["ID", "Inicio", "Tamano", "Proceso", "Frag. Externa"],
        filas_memoria,
    )


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

    eventos.append(evento)

    if paso_a_paso:
        if len(eventos) > 1:
            input(
                f"\nPresiona Enter para avanzar al siguiente cambio "
                f"(tiempo {evento['tiempo']})..."
            )

        mostrar_evento_consola(evento)


def generar_memoria_html(memoria):
    contenido = ""

    for p in memoria:
        if p.id_proceso == "SO":
            clase = "bloque-so"
            nombre = "SO"
        elif p.esta_libre():
            clase = "bloque-libre"
            nombre = "Libre"
        else:
            clase = "bloque-proceso"
            nombre = p.id_proceso

        ancho = p.tamanio / 550 * 100

        contenido += f'''
            <div class="bloque-memoria {clase}"
                 style="width: {ancho:.2f}%;">
                <strong>{nombre}</strong>
                <span>{p.tamanio}K</span>
            </div>
        '''

    return contenido


def generar_colas_html(evento):
    colas = [
        ("NUEVOS", evento["nuevos"], "nuevo"),
        ("LISTOS", evento["listos"], ""),
        ("SUSPENDIDOS", evento["suspendidos"], "suspendido"),
        ("TERMINADOS", evento["terminados"], "terminado")
    ]

    contenido = ""

    for titulo, procesos, clase in colas:
        elementos = "".join(
            f'<span class="parte-proceso {clase}">{p}</span>'
            for p in procesos
        )

        if not procesos:
            elementos = '<span class="cola-vacia">Sin procesos</span>'

        contenido += f'''
            <div class="cola-indv">
                <h3>{titulo}</h3>
                <div class="procesos-cola">{elementos}</div>
            </div>
        '''

    return contenido


def generar_html(eventos, procesos, tiempo_total):
    carpeta = Path(__file__).parent

    with open(carpeta / "pagina.html", "r", encoding="utf-8") as archivo:
        plantilla = archivo.read()

    botones = ""
    estados = ""
    reglas_css = ""

    for i, evento in enumerate(eventos):
        seleccionado = "checked" if i == 0 else ""

        botones += f'''
            <input type="radio" name="evento" id="evento{i}" {seleccionado}>
            <label for="evento{i}">T{evento["tiempo"]}</label>
        '''

        reglas_css += f'''
            #timeline:has(#evento{i}:checked) ~ #estados #estado{i} {{
                display: block;
            }}
        '''

        memoria = ""
        for p in evento["memoria"]:
            if p["proceso"] == "SO":
                clase, nombre = "bloque-so", "SO"
            elif p["proceso"] is None:
                clase, nombre = "bloque-libre", "Libre"
            else:
                clase, nombre = "bloque-proceso", p["proceso"]

            ancho = p["tamano"] / 550 * 100

            memoria += f'''
                <div class="bloque-memoria {clase}" style="width:{ancho:.2f}%">
                    <strong>{nombre}</strong>
                    <span>{p["tamano"]}K</span>
                </div>
            '''

        colas = generar_colas_html(evento)

        estados += f'''
            <div class="estado-evento" id="estado{i}">
                <div class="cont-instante">
                    <div class="instante-tiempo">
                        <span>TIEMPO</span>
                        <strong>T{evento["tiempo"]}</strong>
                    </div>
                    <div class="instante-evento">
                        <span>EVENTO</span>
                        <strong>{evento["descripcion"]}</strong>
                    </div>
                </div>

                <div class="estado-principal">
                    <div class="panel">
                        <h2>Memoria</h2>
                        <div class="memoria">{memoria}</div>
                    </div>
                    <div class="panel">
                        <h2>CPU</h2>
                        <div class="bloque-cpu">
                            <div class="cpu-icon">⚙</div>
                            <div class="cpu-proceso">
                                <span>PROCESO EN EJECUCIÓN</span>
                                <strong>{evento["cpu"]}</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="colas">{colas}</div>
            </div>
        '''

    cantidad = len(procesos)
    promedio_retorno = sum(p.tiempo_retorno for p in procesos) / cantidad
    promedio_espera = sum(p.tiempo_espera for p in procesos) / cantidad
    rendimiento = cantidad / tiempo_total if tiempo_total else 0

    estadisticas = f'''
        <div class="resumen-estadisticas">
            <div class="bloque-estadistica">
                <span>PROMEDIO DE RETORNO</span>
                <strong>{promedio_retorno:.2f}</strong>
            </div>
            <div class="bloque-estadistica">
                <span>PROMEDIO DE ESPERA</span>
                <strong>{promedio_espera:.2f}</strong>
            </div>
            <div class="bloque-estadistica">
                <span>RENDIMIENTO</span>
                <strong>{rendimiento:.4f}</strong>
            </div>
        </div>

        <div class="tabla-estadisticas">
            <table>
                <thead>
                    <tr>
                        <th>Proceso</th>
                        <th>Arribo</th>
                        <th>Irrupción</th>
                        <th>Finalización</th>
                        <th>Retorno</th>
                        <th>Espera</th>
                    </tr>
                </thead>
                <tbody>
    '''

    for p in sorted(procesos, key=lambda p: p.id_proceso):
        estadisticas += f'''
            <tr>
                <td>{p.id_proceso}</td>
                <td>{p.tiempo_arribo}</td>
                <td>{p.tiempo_irrupcion}</td>
                <td>{p.tiempo_finalizacion}</td>
                <td>{p.tiempo_retorno}</td>
                <td>{p.tiempo_espera}</td>
            </tr>
        '''

    estadisticas += '</tbody></table></div>'

    plantilla = plantilla.replace("<!-- EVENTOS -->", botones)
    plantilla = plantilla.replace("<!-- ESTADOS -->", estados)
    plantilla = plantilla.replace("<!-- ESTADISTICAS -->", estadisticas)
    plantilla = plantilla.replace("/* CSS DINAMICO */", reglas_css)

    salida = carpeta / "visualizador.html"
    salida.write_text(plantilla, encoding="utf-8")

    print(f"Visualizador generado: {salida}")
    return salida


def simular(procesos, paso_a_paso=False):
    memoria = inicializar_memoria()
    eventos = []
    procesos.sort(key=lambda p: (p.tiempo_arribo, p.id_proceso))

    tiempo = 0
    ejecutando = None
    llegadas_mostradas = set()

    while any(proceso.estado != "Terminado" for proceso in procesos):
        # Detectar arribos que todavía no se mostraron.
        llegadas = [
            proceso
            for proceso in procesos
            if proceso.tiempo_arribo <= tiempo
            and proceso.id_proceso not in llegadas_mostradas
        ]

        for proceso in llegadas:
            llegadas_mostradas.add(proceso.id_proceso)

        admitir_procesos(memoria, procesos, tiempo)

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

        # Si SRTF cambia de proceso, el anterior vuelve a Listo.
        if ejecutando is not None and ejecutando is not elegido:
            ejecutando.estado = "Listo"

        elegido.estado = "Ejecucion"
        ejecutando = elegido

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

        # Ejecutar una unidad de tiempo y volver a evaluar SRTF.
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

            # Primer evento: finalización.
            registrar_evento(
                memoria,
                procesos,
                tiempo,
                f"Finalización de {finalizado.id_proceso}",
                None,
                eventos,
                paso_a_paso,
            )

            # Seleccionar al siguiente proceso.
            siguiente = seleccionar_srtf(procesos)

            if siguiente is not None:
                siguiente.estado = "Ejecucion"
                ejecutando = siguiente

                # Segundo evento: comienzo de ejecución.
                registrar_evento(
                    memoria,
                    procesos,
                    tiempo,
                    f"Arribo de proceso(s): {ids}",
                    ejecutando,
                    eventos,
                    paso_a_paso,
                )

    return procesos, tiempo, eventos


# VERIFICAR PORQUE SOLUCIONA PROBLEMAS QUE NO SABIAMOS QUE TENIAMOS

def seleccionar_archivo():
    """Abre el explorador de archivos y devuelve la ruta elegida (o None)."""
    import tkinter as tk
    from tkinter import filedialog

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

    ventana.destroy()
    return Path(ruta) if ruta else None


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
    print("1. Cargar archivo")
    print("2. Ejecutar por consola")
    print("3. Generar el html")
    print("4. Salir")


def menu():
    procesos = None
    nombre_archivo = None

    while True:
        mostrar_menu(nombre_archivo)
        opcion = input("Elegi una opcion: ").strip()

        if opcion == "1":
            resultado = cargar_archivo()

            if resultado is not None:
                ruta, procesos = resultado
                nombre_archivo = ruta.name

        elif opcion in ("2", "3"):
            if procesos is None:
                print(
                    "\nNo hay un archivo cargado. "
                    "Primero usa la opcion 1 (Cargar archivo)."
                )
                continue

            if opcion == "2":
                ejecutar_por_consola(copy.deepcopy(procesos))
            else:
                try:
                    generar_visualizador(procesos)
                except RuntimeError as error:
                    print(f"\nError: {error}")

        elif opcion == "4":
            print("Hasta luego.")
            break

        else:
            print("Opcion invalida. Elegi un numero del 1 al 4.")


if __name__ == "__main__":
    menu()

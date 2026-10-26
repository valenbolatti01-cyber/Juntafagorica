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


def mostrar_estado(memoria, procesos, tiempo, motivo, ejecutando):
    print(f"\nTiempo {tiempo} - {motivo}")
    print(f"CPU: {ejecutando.id_proceso if ejecutando else 'Libre'}")

    for estado in (
        "Nuevo",
        "Listo",
        "Listo y Suspendido",
        "Ejecucion",
        "Terminado",
    ):
        ids = [
            proceso.id_proceso
            for proceso in procesos
            if proceso.estado == estado
        ]
        print(f"{estado}: {', '.join(ids) if ids else '-'}")

    mostrar_memoria(memoria)


def simular(procesos):
    memoria = inicializar_memoria()
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
            mostrar_estado(
                memoria,
                procesos,
                tiempo,
                f"Arribo de proceso(s): {ids}",
                ejecutando,
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

            mostrar_estado(
                memoria,
                procesos,
                tiempo,
                f"Finalizacion de {finalizado.id_proceso}",
                ejecutando,
            )

    return procesos, tiempo


if __name__ == "__main__":
    ruta_csv = Path(__file__).with_name("procesos.csv")
    procesos = cargar_procesos(ruta_csv)

    if not procesos:
        raise ValueError("El CSV debe incluir al menos un proceso.")

    procesos, tiempo_total = simular(procesos)

    print("\nEstadisticas finales")
    print("ID | Arribo | Irrupcion | Finalizacion | Retorno | Espera")

    for proceso in sorted(procesos, key=lambda p: p.id_proceso):
        print(
            f"{proceso.id_proceso} | "
            f"{proceso.tiempo_arribo} | "
            f"{proceso.tiempo_irrupcion} | "
            f"{proceso.tiempo_finalizacion} | "
            f"{proceso.tiempo_retorno} | "
            f"{proceso.tiempo_espera}"
        )

    promedio_retorno = (
        sum(p.tiempo_retorno for p in procesos) / len(procesos)
    )
    promedio_espera = (
        sum(p.tiempo_espera for p in procesos) / len(procesos)
    )
    rendimiento = len(procesos) / tiempo_total if tiempo_total else 0

    print(f"Promedio de retorno: {promedio_retorno:.2f}")
    print(f"Promedio de espera: {promedio_espera:.2f}")
    print(f"Rendimiento: {rendimiento:.4f} procesos por unidad de tiempo")
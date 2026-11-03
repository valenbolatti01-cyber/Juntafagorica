from pathlib import Path
import html


def generar_memoria_html(memoria):
    contenido = ""

    for p in memoria:
        if p["proceso"] == "SO":
            clase, nombre = "bloque-so", "SO"
        elif p["proceso"] is None:
            clase, nombre = "bloque-libre", "Libre"
        else:
            clase, nombre = "bloque-proceso", p["proceso"]

        ancho = p["tamano"] / 550 * 100

        contenido += f'''
            <div class="bloque-memoria {clase}"
                 style="width: {ancho:.2f}%;">
                <strong>{html.escape(str(nombre))}</strong>
                <span>{p["tamano"]}K</span>
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
            f'<span class="parte-proceso {clase}">'
            f'{html.escape(str(p))}</span>'
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

        memoria = generar_memoria_html(evento["memoria"])

        # Botón "Siguiente"
        if i < len(eventos) - 1:
            boton = (f'<label class="btn-siguiente" for="evento{i + 1}">'
                     f'Siguiente &#9654;</label>')
        else:
            boton = '<span class="btn-siguiente deshabilitado">Fin &#9632;</span>'

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
                        <strong>{html.escape(str(evento["descripcion"]))}</strong>
                    </div>
                </div>

                <div class="estado-principal">
                    <div class="panel">
                        <h2>Memoria</h2>
                        <div class="memoria">{memoria}</div>
                        <div class="controles-memoria">{boton}</div>
                    </div>

                    <div class="panel">
                        <h2>CPU</h2>
                        <div class="bloque-cpu">
                            <div class="cpu-icon">⚙</div>
                            <div class="cpu-proceso">
                                <span>PROCESO EN EJECUCIÓN</span>
                                <strong>{html.escape(str(evento["cpu"]))}</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="colas">{colas}</div>
            </div>
        '''

    cantidad = len(procesos)

    if cantidad > 0:
        promedio_retorno = sum(
            p.tiempo_retorno for p in procesos
        ) / cantidad

        promedio_espera = sum(
            p.tiempo_espera for p in procesos
        ) / cantidad
    else:
        promedio_retorno = 0
        promedio_espera = 0

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
                <td>{html.escape(str(p.id_proceso))}</td>
                <td>{p.tiempo_arribo}</td>
                <td>{p.tiempo_irrupcion}</td>
                <td>{p.tiempo_finalizacion}</td>
                <td>{p.tiempo_retorno}</td>
                <td>{p.tiempo_espera}</td>
            </tr>
        '''

    estadisticas += '''
                </tbody>
            </table>
        </div>
    '''

    plantilla = plantilla.replace("<!-- EVENTOS -->", botones)
    plantilla = plantilla.replace("<!-- ESTADOS -->", estados)
    plantilla = plantilla.replace("<!-- ESTADISTICAS -->", estadisticas)
    plantilla = plantilla.replace("/* CSS DINAMICO */", reglas_css)

    salida = carpeta / "visualizador.html"
    salida.write_text(plantilla, encoding="utf-8")

    print(f"Visualizador generado: {salida}")

    return salida

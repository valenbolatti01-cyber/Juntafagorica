import csv
import io
import re
import unicodedata
from pathlib import Path


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


class ErrorCSV(ValueError):
    """Error de lectura o validacion del archivo de procesos."""
    pass

COLUMNAS_REQUERIDAS = ("id", "tamanio", "arribo", "irrupcion")
MAX_PROCESOS = 10


def _normalizar_columna(nombre):
    nombre = nombre.strip().casefold()
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(
        caracter
        for caracter in nombre
        if not unicodedata.combining(caracter)
    )    

    # Permite que "tamano" y "tamaño" correspondan a "tamanio"
    if nombre == "tamano":
        nombre = "tamanio"

    return nombre


def _leer_texto_csv(ruta_archivo):
    ruta = Path(ruta_archivo)

    if not ruta.exists():
        raise ErrorCSV(
            f"No se encontro el archivo '{ruta.name}' en '{ruta.parent}'."
        )

    if not ruta.is_file():
        raise ErrorCSV(f"'{ruta.name}' no es un archivo.")

    try:
        datos = ruta.read_bytes()
    except PermissionError as error:
        raise ErrorCSV(f"No hay permiso para leer '{ruta.name}'.") from error
    except OSError as error:
        raise ErrorCSV(f"No se pudo leer '{ruta.name}': {error}.") from error

    if not datos:
        raise ErrorCSV("El archivo esta vacio.")

    try:
        if datos.startswith((b"\xff\xfe", b"\xfe\xff")):
            texto = datos.decode("utf-16")
        else:
            try:
                texto = datos.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = datos.decode("cp1252")
    except UnicodeError as error:
        raise ErrorCSV(
            "No se pudo decodificar el archivo. "
            "Guardalo como CSV UTF-8."
        ) from error

    # Quita marcas BOM que puedan haber quedado dentro del contenido.
    texto = texto.replace("\ufeff", "")

    if "\x00" in texto:
        raise ErrorCSV(
            "El archivo contiene caracteres nulos y no parece ser un CSV de texto."
        )

    return texto


def _detectar_separador(texto):
    muestra = "\n".join(
        linea for linea in texto.splitlines() if linea.strip()
    )[:4096]

    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
        return dialecto.delimiter
    except csv.Error:
        primera_linea = next(
            (linea for linea in texto.splitlines() if linea.strip()),
            "",
        )
        cantidades = {
            separador: primera_linea.count(separador)
            for separador in (",", ";", "\t")
        }
        mejor = max(cantidades, key=cantidades.get)

        return mejor if cantidades[mejor] else ","


def _leer_entero(valor, nombre_campo, numero_linea, minimo, maximo=None):
    valor = valor.strip()

    # Se permiten solamente números ASCII con signo negativo opcional.
    # Así se rechazan decimales, notación científica, guiones bajos y
    # dígitos Unicode que int() aceptaría.
    if not re.fullmatch(r"-?[0-9]+", valor):
        raise ErrorCSV(
            f"Linea {numero_linea}: '{nombre_campo}' debe ser un entero "
            f"sin decimales (se leyo '{valor}')."
        )

    numero = int(valor)

    if numero < 0:
        raise ErrorCSV(
            f"Linea {numero_linea}: '{nombre_campo}' no puede ser negativo."
        )

    if numero < minimo:
        raise ErrorCSV(
            f"Linea {numero_linea}: '{nombre_campo}' debe ser como minimo "
            f"{minimo}."
        )

    if maximo is not None and numero > maximo:
        raise ErrorCSV(
            f"Linea {numero_linea}: '{nombre_campo}' debe ser como maximo "
            f"{maximo}."
        )

    return numero


def cargar_procesos(ruta_archivo):
    texto = _leer_texto_csv(ruta_archivo)
    separador = _detectar_separador(texto)
    lector = csv.reader(
        io.StringIO(texto),
        delimiter=separador,
        strict=True,
    )

    # Buscar el primer registro que no esté vacío para usarlo como encabezado.
    while True:
        linea_encabezado = lector.line_num + 1

        try:
            encabezado = next(lector)
        except StopIteration:
            raise ErrorCSV("El archivo no contiene un encabezado.")
        except csv.Error as error:
            raise ErrorCSV(
                f"Formato CSV invalido cerca de la linea "
                f"{linea_encabezado}: revisa las comillas."
            ) from error

        if encabezado and any(valor.strip() for valor in encabezado):
            break

    columnas = [_normalizar_columna(nombre) for nombre in encabezado]

    repetidas = sorted({
        nombre for nombre in columnas
        if columnas.count(nombre) > 1
    })
    if repetidas:
        raise ErrorCSV(
            "Columnas repetidas en el encabezado: "
            + ", ".join(repetidas)
            + "."
        )

    faltantes = [
        nombre
        for nombre in COLUMNAS_REQUERIDAS
        if nombre not in columnas
    ]
    if faltantes:
        raise ErrorCSV(
            "Faltan columnas en el encabezado: "
            + ", ".join(faltantes)
            + "."
        )

    sobrantes = [
        nombre
        for nombre in columnas
        if nombre not in COLUMNAS_REQUERIDAS
    ]
    if sobrantes:
        raise ErrorCSV(
            "Columnas que no corresponden: "
            + ", ".join(sobrantes)
            + "."
        )

    procesos = []
    ids = set()

    while True:
        linea_inicio = lector.line_num + 1

        try:
            fila = next(lector)
        except StopIteration:
            break
        except csv.Error as error:
            raise ErrorCSV(
                f"Formato CSV invalido desde la linea {linea_inicio}: "
                "revisa que las comillas esten cerradas."
            ) from error

        # Ignorar líneas realmente vacías, pero no filas como ",,,"
        if not fila or all(not valor.strip() for valor in fila):
            continue

        if len(procesos) >= MAX_PROCESOS:
            raise ErrorCSV(
                f"El archivo no puede contener mas de {MAX_PROCESOS} procesos."
            )

        if len(fila) != len(columnas):
            raise ErrorCSV(
                f"Linea {linea_inicio}: tiene {len(fila)} valores y "
                f"deberia tener {len(columnas)}."
            )

        datos = dict(zip(columnas, fila))

        id_proceso = datos["id"].strip()
        if not id_proceso:
            raise ErrorCSV(
                f"Linea {linea_inicio}: el campo 'id' esta vacio."
            )
        
        if not re.fullmatch(r"[A-Za-z0-9]{1,10}", id_proceso):
            raise ErrorCSV(
                f"Linea {linea_inicio}: el ID '{id_proceso}' "
                "debe tener entre 1 y 10 letras o numeros."
            )

        if id_proceso.casefold() == "so":
            raise ErrorCSV(
                f"Linea {linea_inicio}: 'SO' esta reservado "
                "para el sistema operativo."
            )

        id_normalizado = id_proceso.casefold()
        if id_normalizado in ids:
            raise ErrorCSV(
                f"Linea {linea_inicio}: el ID '{id_proceso}' "
                "ya fue utilizado, ignorando mayusculas y minusculas."
            )
        
        tamanio = _leer_entero(
            datos["tamanio"], "tamanio", linea_inicio, 1, 450
        )
        arribo = _leer_entero(
            datos["arribo"], "arribo", linea_inicio, 0
        )
        irrupcion = _leer_entero(
            datos["irrupcion"], "irrupcion", linea_inicio, 1
        )

        ids.add(id_normalizado)
        procesos.append(
            Proceso(id_proceso, tamanio, arribo, irrupcion)
        )

    if not procesos:
        raise ErrorCSV("El archivo no tiene procesos; solo tiene el encabezado.")

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
    columnas = ["ID", "Inicio", "Tamano", "Proceso", "Frag. Interna"]

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

# Introducción
  Este simulador de gestión de memoria (MVT) y planificación de procesos (SRTF) permite evaluar la carga y ejecución de procesos mediante asignación dinámica Best-Fit. A continuación, se detalla el procedimiento para configurar los datos, ejecutar el entorno y analizar las simulaciones.   

# Preparar el archivo de procesos (CSV)
  El programa requiere un archivo CSV con la lista de procesos a simular, el cual debe cumplir con las siguientes reglas de formato y validación:   
    Columnas obligatorias: El encabezado del archivo debe contener exactamente id, tamanio, arribo, y irrupcion. Si esto no se cumple, el simulador muestra un mensaje mencionando que el archivo csv no es válido.   

    Límites de procesos: Se permite un máximo de 10 procesos por archivo para la simulación. Si este se excede, el simulador avisa que el archivo sobrepasa la cantidad permitida y no carga el archivo para su ejecución.

    Reglas del identificador (ID): Debe tener entre 1 y 10 caracteres alfanuméricos. No debe llamarse "SO" (ni sus variantes en mayúsculas/minúsculas), ya que está reservado para el Sistema Operativo.   

    Restricciones numéricas: El tamanio debe ser un valor entero entre 1 y 450 (representando kilobytes), el tiempo de arribo debe ser mayor o igual a 0, y el tiempo de irrupcion mayor o igual a 1. En caso de superar el tamaño, el simulador avisa que un proceso excede el tamaño de memoria y no lo carga para su ejecución.

    Ejemplo de contenido válido para un archivo CSV:
      id,tamanio,arribo,irrupcion
      P1,30,0,5
      P2,20,5,4
      P3,250,6,3
      P4,15,4,1
      P5,45,7,4

# Iniciar el simulador
  Para iniciarlo, se puede hacer mediante el ejecutable "Simulador.exe" o abriendo el archivo "main.py" y ejecutarlo por la terminal.

# Operar el menú interactivo
  Al iniciar, el sistema presenta un menú de 5 opciones:   
    Opción 1 (Cargar archivo por explorador de windows): Abre el explorador de windows para seleccionar fácilmente el archivo CSV desde las carpetas.

    Opción 2 (Cargar archivo por ruta): Permite ingresar manualmente la ruta del archivo mediante la consola, útil si no se dispone de un entorno gráfico.   
    
    Opción 3 (Ejecutar por consola): Inicia la simulación paso a paso en la terminal. Se debe presionar la tecla "Enter" para avanzar a cada instante de tiempo donde ocurra un nuevo evento (arribo de procesos, inicio en CPU o finalización). En cada paso se imprimen las particiones de memoria ocupadas/libres, el grado de fragmentación externa, el proceso en CPU y el contenido de cada cola de estado.   
    
    Opción 4 (Generar el html): Procesa toda la simulación internamente, inyecta los resultados en la plantilla "pagina.html" usando el script   "visualizador.py", y abre automáticamente el resultado final interactivo en el navegador web predeterminado.   
    
    Opción 5 (Salir): Finaliza la ejecución del programa y cierra el menú.   

# Analizar los resultados de la simulación
   En la consola (Opción 3) al concluir todos los eventos, se imprimirá una tabla con las estadísticas finales de cada proceso, detallando los tiempos de finalización, retorno y espera, junto con el rendimiento del sistema medido en procesos por unidad de tiempo.

   En el visualizador web (Opción 4) se utilizan los selectores superiores de la "Línea temporal" o el botón "Siguiente" para recorrer gráficamente cada instante de tiempo. Esto te permite visualizar la barra de memoria dinámica, los procesos bloqueados por fragmentación externa, el cambio de contexto en la CPU y los movimientos precisos entre las colas de Nuevos, Listos, Suspendidos y Terminados.
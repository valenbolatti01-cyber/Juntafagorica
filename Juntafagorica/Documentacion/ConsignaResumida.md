# Resumen de consigna

## Objetivo

Implementar un simulador que permita observar el ciclo de vida completo de un proceso, desde su ingreso al sistema hasta su finalizacion, combinando:

- Planificacion a corto plazo.
- Gestion de memoria con particiones variables.
- Un unico procesador.
- Salidas comprensibles para el usuario.

## Requisitos funcionales

- Cargar procesos desde archivo.
- Aceptar como maximo 10 procesos.
- Leer por proceso:
  - ID.
  - Tamano del proceso.
  - Tiempo de arribo.
  - Tiempo de irrupcion.
- Admitir procesos nuevos cuando sea posible.
- No superar 5 procesos en conjunto entre:
  - Ejecucion.
  - Listo.
  - Listo y Suspendido.
- Usar Best-Fit para asignacion de memoria.
- Usar SRTF para planificacion de CPU.
- Mostrar informacion cada vez que:
  - Llega un nuevo proceso.
  - Termina el proceso en ejecucion.
- Evitar corridas completamente ininterrumpidas sin puntos de observacion.

## Memoria

- Memoria total: 550 K.
- Sistema operativo: 100 K.
- Procesos de usuario: 450 K.
- Los procesos de usuario solo pueden ocupar direcciones desde 100 K en adelante.
- La memoria se administra con particiones variables.
- Las particiones libres contiguas deben unirse cuando corresponda.

## Tabla de particiones

La salida debe incluir:

- ID de particion.
- Direccion de comienzo.
- Tamano.
- ID de proceso asignado, si corresponde.
- Fragmentacion interna.

En MVT con particiones creadas exactamente al tamano solicitado, la fragmentacion interna esperada normalmente es 0.

## Estados

- Nuevo: proceso arribado pero aun no admitido.
- Listo: proceso en memoria esperando CPU.
- Listo y Suspendido: proceso admitido logicamente, pero sin memoria disponible para competir por CPU.
- Ejecucion: proceso usando el procesador.
- Terminado: proceso finalizado y con recursos liberados.

## Estadisticas finales

Al finalizar todos los procesos:

- Tiempo de retorno por proceso.
- Tiempo de espera por proceso.
- Promedio de retorno.
- Promedio de espera.
- Rendimiento del sistema: trabajos terminados por unidad de tiempo.

## Casos de prueba obligatorios o recomendados

- Proceso que ocupa exactamente los 450 K de usuario.
- Proceso que no puede ingresar por falta de espacio contiguo suficiente.
- Best-Fit con varios huecos libres de distinto tamano.
- Liberacion de memoria y union de espacios contiguos.
- Llegada de proceso mas corto que el que esta ejecutando.
- Empate entre procesos con igual tiempo restante.
- Llegada de mas de 5 procesos.
- Limite de admision alcanzado aunque exista memoria libre.
- Llegadas simultaneas.
- Archivo con datos incorrectos.
- Verificacion manual de tiempos de espera, retorno y rendimiento.

## Fechas indicadas

- Primera entrega de avance: 06/10.
- Entrega final: 17/11.
from shell import *

memoria = inicializar_memoria()

p1 = Proceso("P1", 30, 0, 5)
p2 = Proceso("P2", 20, 5, 4)

asignar_memoria(memoria, p1)
asignar_memoria(memoria, p2)
mostrar_memoria(memoria)
liberar_memoria(memoria,"P1")
mostrar_memoria(memoria)

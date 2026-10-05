from shell import *

memoria = inicializar_memoria()

p1 = Proceso("P1", 140, 10, 72)
p2 = Proceso("P2", 120, 4, 26)

asignar_memoria(memoria, p1)
asignar_memoria(memoria, p2)

mostrar_memoria(memoria)

from shell import Proceso, inicializar_memoria, mostrar_memoria, asignar_memoria

memoria = inicializar_memoria()

p1 = Proceso("P1", 120, 0, 8)
p2 = Proceso("P2", 60, 1, 4)

asignar_memoria(memoria, p1)
asignar_memoria(memoria, p2)

mostrar_memoria(memoria)

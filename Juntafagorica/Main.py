from shell import *

memoria = inicializar_memoria()

p1 = Proceso("P1", 30, 0, 5)
p2 = Proceso("P2", 20, 5, 4)
p3 = Proceso("P3", 40, 6, 3)

asignar_memoria(memoria, p1)
asignar_memoria(memoria, p2)
mostrar_memoria(memoria)      # P1 @100, P2 @130, Libre 400 @150

liberar_memoria(memoria, "P1")
liberar_memoria(memoria, "P2")
mostrar_memoria(memoria)      # un solo Libre 450 @100 (huecos unidos)

print(asignar_memoria(memoria, p3))  # True
mostrar_memoria(memoria)      # P3 @100, Libre 410 @140

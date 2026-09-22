# CLASE AGENTES DFS
"""
Constructor(mapa, n_agentes):
    agregar los n agentes como 1 en el mapa en el punto de partida (4)
    (como DFS no ve el costo de manera nativa, el cuello de botella
    se produce porque una vez salen del punto de partida, los n agentes no
    pueden compartir una casilla nuevamente).
    
    inicializar una matriz de nx3 con la posición de los agentes en la primera columna,
    su estado vivo o muerto en la segunda y sus stacks en la tercera
        
Movimiento():
    Para cada agente:
        AlgoritmoDFS
        Actualizar mapa (importante actualizar inmediatamente despues para evitar superposiciones)
        de posisiones y tambien del fuego, cambiando el estado de un agente si este esta en una casilla
        afectada.
"""
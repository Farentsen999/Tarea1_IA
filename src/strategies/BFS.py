from collections import deque

class AgenteBFS:
    """
    Representa a un agente individual que navega por el mapa utilizando Breath-First Search.
    """
    def __init__(self, id_agente, pos_inicial):
        """
        Inicializa los atributos del agente DFS.

        Parámetros:
        - id_agente (int): Identificador único del agente en la simulación.
        - pos_inicial (tuple): Coordenadas iniciales (fila, columna) donde se despliega.
        """
        self.id = id_agente
        self.pos_actual = pos_inicial
        self.vivo = True
        self.escapado = False
        
        self.camino = []
        self.paso_actual_idx = 0

    def calcular_ruta_bfs(self, ambiente):
        """
        Ejecuta la lógica de decisión y movimiento de un turno individual mediante DFS.
        
        Parámetros:
        - ambiente (Ambiente): Instancia del mapa con las 3 capas para consultar el entorno.
        """
        inicio = self.pos_actual
        cola = deque([inicio])
        
        padres = {inicio: None}
        salida_encontrada = None

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while cola:
            actual = cola.popleft()
            f, c = actual

            if ambiente.matriz_3d[f, c, 0] == 2:
                salida_encontrada = actual
                break

            for df, dc in movimientos:
                nf, nc = f + df, c + dc
                vecino = (nf, nc)

                if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                    es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                    con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1

                    if not es_pared and not con_fuego and vecino not in padres:
                        padres[vecino] = actual
                        cola.append(vecino)

        if salida_encontrada:
            camino_reconstruido = []
            curr = salida_encontrada
            while curr is not None:
                camino_reconstruido.append(curr)
                curr = padres[curr]
            
            camino_reconstruido.reverse()
            
            self.camino = camino_reconstruido[1:]
            self.paso_actual_idx = 0

    def paso_bfs(self, ambiente):
        if not self.vivo or self.escapado:
            return
        
        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        if not self.camino or self.paso_actual_idx >= len(self.camino):
            self.calcular_ruta_bfs(ambiente)
            if not self.camino:
                return

        siguiente_pos = self.camino[self.paso_actual_idx]
        nf, nc = siguiente_pos

        con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
        con_agente = ambiente.matriz_3d[nf, nc, 2] == 1

        if not con_fuego and not con_agente:
            self.pos_actual = siguiente_pos
            self.paso_actual_idx += 1
        else:
            self.calcular_ruta_bfs(ambiente)


class GestorAgentesBFS:
    """
    Coordinador central encargado de instanciar, controlar el turno de movimiento 
    y sincronizar el estado global de todos los agentes BFS en el ambiente.
    """
    def __init__(self, ambiente, num_agentes):
        """
        Inicializa la población de agentes DFS y los despliega en el mapa.

        Parámetros:
        - ambiente (Ambiente): Instancia del ambiente global de simulación.
        - num_agentes (int): Número de agentes a generar.
        """
        self.ambiente = ambiente
        posiciones_iniciales = ambiente.obtener_posiciones_iniciales(num_agentes)
        
        self.agentes = [
            AgenteBFS(id_agente=i+1, pos_inicial=pos) 
            for i, pos in enumerate(posiciones_iniciales)
        ]
        
        self.ambiente.colocar_agentes([a.pos_actual for a in self.agentes])

    def mover_turno(self):
        """
        Ejecuta el paso DFS para cada agente activo en secuencia.
        Sincroniza la Capa 2 inmediatamente después del paso de cada agente
        para evitar colisiones entre compañeros dentro del mismo turno.
        """
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                agente.paso_bfs(self.ambiente)
                self._sincronizar_capa_agentes()

    def evaluar_impacto_fuego(self):
        """
        Verifica si el fuego que se acaba de propagar en la Capa 1 alcanzó
        la posición actual de algún agente activo, actualizando su estado de vida.
        """
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                f, c = agente.pos_actual
                if self.ambiente.matriz_3d[f, c, 1] == 1:
                    agente.vivo = False
        self._sincronizar_capa_agentes()

    def simulacion_terminada(self):
        """
        Verifica el criterio de finalización global de la simulación.

        Retorna:
        - bool: True si todos los agentes han terminado su ejecución (escaparon o fallecieron).
        """
        return all(not agente.vivo or agente.escapado for agente in self.agentes)

    def _sincronizar_capa_agentes(self):
        """
        Método privado auxiliar que limpia la Capa 2 de la matriz 3D y reasigna
        exclusivamente las coordenadas de los agentes que siguen vivos y dentro del mapa.
        """
        self.ambiente.reiniciar_capa_agentes()
        pos_activa = [a.pos_actual for a in self.agentes if a.vivo and not a.escapado]
        self.ambiente.colocar_agentes(pos_activa)
        
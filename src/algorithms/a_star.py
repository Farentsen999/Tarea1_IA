import heapq

class AgenteAStar:
    """
    Representa a un agente individual que navega por el mapa utilizando A*.
    """
    def __init__(self, id_agente, pos_inicial):
        """
        Inicializa los atributos del agente A*.

        Parámetros:
        - id_agente (int): Identificador único del agente.
        - pos_inicial (tuple): Coordenadas (fila, columna) donde inicia el agente.
        """
        self.id = id_agente
        self.pos_actual = pos_inicial
        self.vivo = True          # Estado de vida (False si lo alcanza el fuego)
        self.escapado = False     # Estado de éxito (True si llegó a una salida)
        
        self.camino = []          # Lista de coordenadas (f, c) planificadas por A*
        self.paso_actual_idx = 0  # Índice de la siguiente casilla a la que debe avanzar
        self.replan_cada = 4      # Cada cuántos pasos se replanifica para captar la congestión actual
        self.pasos_desde_plan = 0

    def _heuristica_manhattan(self, pos, salidas):
        """
        Método que calcula la distancia Manhattan desde la posición dada 
        hasta la salida más cercana disponible.

        Parámetros:
        - pos (tuple): Coordenadas actuales a evaluar (fila, columna).
        - salidas (list): Lista de tuplas con las coordenadas de las salidas (Capa 0 == 2).

        Retorna:
        - int: La menor distancia Manhattan estimada hasta alguna de las salidas.
        """
        f, c = pos
        # Distancia Manhattan
        return min(abs(f - sf) + abs(c - sc) for sf, sc in salidas)

    def calcular_ruta_astar(self, ambiente):
        """
        Ejecuta el algoritmo A* para planificar unar ruta hacia la salida.

        Parámetros:
        - ambiente (Ambiente): Instancia del mapa que contiene la matriz 3D.
        """
        # Si no hay salidas registradas en el mapa, no se puede calcular una ruta
        if not ambiente.posiciones_salidas:
            return

        inicio = self.pos_actual
        
        # Priority Queue para lmacenar elementos en formato (f_score, g_score, posición_actual)
        open_set = []
        heapq.heappush(open_set, (0, 0, inicio))
        
        # Diccionarios de seguimiento para reconstruir la ruta y evaluar costos
        padres = {inicio: None}   # Guarda el nodo previo para cada nodo explorado: padres[hijo] = padre
        g_score = {inicio: 0}     # Costo real acumulado desde el inicio hasta cada nodo
        
        salida_alcanzada = None
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while open_set:
            # Extrae el nodo con la menor heurística.
            _, g_actual, actual = heapq.heappop(open_set)
            # Entrada obsoleta: ya se encontró un camino mejor a este nodo
            if g_actual > g_score.get(actual, float('inf')):
                continue
            f_act, c_act = actual

            # Criterio de término de la búsqueda: Alcanzar una casilla de salida
            if ambiente.matriz_3d[f_act, c_act, 0] == 2:
                salida_alcanzada = actual
                break

            # Exploración de vecinos
            for df, dc in movimientos:
                nf, nc = f_act + df, c_act + dc
                vecino = (nf, nc)

                # Verificar límites de la matriz
                if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                    es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                    con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1

                    # El agente solo explora casillas sin paredes ni fuego
                    if not es_pared and not con_fuego:
                        # Costo de entrada = 1 + penalización por congestión (>= 1, la heurística sigue siendo admisible)
                        nuevo_g = g_actual + ambiente.costo_transito(nf, nc)

                        if vecino not in g_score or nuevo_g < g_score[vecino]:
                            g_score[vecino] = nuevo_g
                            
                            h = self._heuristica_manhattan(vecino, ambiente.posiciones_salidas)
                            f = nuevo_g + h
                            
                            padres[vecino] = actual
                            heapq.heappush(open_set, (f, nuevo_g, vecino))

        # Reconstrucción de la ruta trazando desde la salida hacia el origen
        if salida_alcanzada:
            camino_reconstruido = []
            curr = salida_alcanzada
            while curr is not None:
                camino_reconstruido.append(curr)
                curr = padres[curr]
            
            # Se invierte la lista para que quede en orden cronológico
            camino_reconstruido.reverse()
            
            # Se omite el primer elemento (índice 0) porque corresponde a la posición actual
            self.camino = camino_reconstruido[1:]
            self.paso_actual_idx = 0
            self.pasos_desde_plan = 0

    def paso_astar(self, ambiente):
        """
        Ejecuta el movimiento correspondiente al turno actual del agente.
        Valida las condiciones de victoria, disponibilidad de camino y colisiones dinámicas.

        Parámetros:
        - ambiente (Ambiente): Instancia del mapa para consultar ocupaciones.
        """
        # Si el agente está muerto o ya escapó, no realiza ninguna acción
        if not self.vivo or self.escapado:
            return

        # 1a. Validación de Condición de Victoria
        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        # 1b. Replanificación periódica: sin esto, la congestión solo se
        #     consideraba al planificar y luego se ignoraba durante toda la ruta.
        if self.camino and self.pasos_desde_plan >= self.replan_cada:
            self.calcular_ruta_astar(ambiente)

        # 2. Si no existe un camino planificado o se terminaron los pasos, recalcula con A*
        if not self.camino or self.paso_actual_idx >= len(self.camino):
            self.calcular_ruta_astar(ambiente)
            if not self.camino:
                # No se encontró una ruta viable (el agente esta bloqueado totalmente por fuego o paredes)
                return

        # 3. Inspeccionar el siguiente paso del camino
        siguiente_pos = self.camino[self.paso_actual_idx]
        nf, nc = siguiente_pos

        # Detección de obstáculos dinámicos en la casilla objetivo
        con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
        con_agente = ambiente.matriz_3d[nf, nc, 2] == 1

        if not con_fuego and not con_agente:
            # Casilla libre: Avanza exitosamente
            self.pos_actual = siguiente_pos
            self.paso_actual_idx += 1
            # Escape en el mismo turno en que se pisa la salida
            if ambiente.matriz_3d[nf, nc, 0] == 2:
                self.escapado = True
            self.pasos_desde_plan += 1
        else:
            # Casilla ocupada o inaccesible dinámicamente: Fuerza una re-planificación con A*
            self.calcular_ruta_astar(ambiente)


class GestorAgentesAStar:
    """
    Coordinador central para instanciar, controlar y sincronizar la población de agentes A*.
    """
    def __init__(self, ambiente, num_agentes):
        """
        Inicializa a la comunidad de agentes A* colocándolos en el ambiente.

        Parámetros:
        - ambiente (Ambiente): Instancia del ambiente global.
        - num_agentes (int): Cantidad total de agentes a desplegar.
        """
        self.ambiente = ambiente
        
        # Obtener posiciones válidas distribuidas alrededor del punto de referencia
        posiciones_iniciales = ambiente.obtener_posiciones_iniciales(num_agentes)
        
        # Instanciar cada AgenteAStar
        self.agentes = [
            AgenteAStar(id_agente=i + 1, pos_inicial=pos) 
            for i, pos in enumerate(posiciones_iniciales)
        ]
        
        # Reflejar las ubicaciones iniciales de los agentes en la Capa 2
        self.ambiente.colocar_agentes([a.pos_actual for a in self.agentes])

    def mover_turno(self):
        """
        Ejecuta en secuencia el paso de turno para cada agente activo 
        y luego actualiza la Capa 2 para evitar superposiciones entre compañeros.
        """
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                agente.paso_astar(self.ambiente)
                # Actualiza la posición en tiempo real para el siguiente agente
                self._sincronizar_capa_agentes()

    def evaluar_impacto_fuego(self):
        """
        Revisa si la propagación del fuego en el turno actual alcanzó la casilla 
        de algún agente y actualiza su estado de vida.
        """
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                f, c = agente.pos_actual
                if self.ambiente.matriz_3d[f, c, 1] == 1:
                    agente.vivo = False
        
        # Retira de la Capa 2 a los agentes que acaban de fallecer
        self._sincronizar_capa_agentes()

    def simulacion_terminada(self):
        """
        Evalúa el criterio de parada global de la simulación.

        Retorna:
        - bool: True cuando todos los agentes o bien escaparon o bien fallecieron.
        """
        return all(not agente.vivo or agente.escapado for agente in self.agentes)

    def _sincronizar_capa_agentes(self):
        """
        Método que limpia la Capa 2 de la matriz 3D 
        y vuelve a colocar únicamente las coordenadas de los agentes vivos y activos.
        """
        self.ambiente.reiniciar_capa_agentes()
        pos_activas = [a.pos_actual for a in self.agentes if a.vivo and not a.escapado]
        self.ambiente.colocar_agentes(pos_activas)
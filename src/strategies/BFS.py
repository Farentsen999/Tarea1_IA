from collections import deque

class AgenteBFS:
    def __init__(self, id_agente, pos_inicial):
        self.id = id_agente
        self.pos_actual = pos_inicial
        self.vivo = True
        self.escapado = False
        
        # Ruta óptima calculada hacia la salida
        self.camino = []
        self.paso_actual_idx = 0

    def calcular_ruta_bfs(self, ambiente):
        """
        Calcula el camino más corto hacia la salida más cercana usando BFS.
        Se ejecuta al inicio o cuando el camino actual es bloqueado por fuego/compañeros.
        """
        inicio = self.pos_actual
        cola = deque([inicio])
        
        # Diccionario para rastrear el camino: padres[nodo_hijo] = nodo_padre
        padres = {inicio: None}
        salida_encontrada = None

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)] # 4-conectividad

        while cola:
            actual = cola.popleft()
            f, c = actual

            # Si encontramos una salida (Capa 0 == 2)
            if ambiente.matriz_3d[f, c, 0] == 2:
                salida_encontrada = actual
                break

            for df, dc in movimientos:
                nf, nc = f + df, c + dc
                vecino = (nf, nc)

                if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                    es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                    con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1

                    # BFS avanza por casillas navegables no visitadas previamente
                    if not es_pared and not con_fuego and vecino not in padres:
                        padres[vecino] = actual
                        cola.append(vecino)

        # Reconstruir la ruta si se halló una salida
        if salida_encontrada:
            camino_reconstruido = []
            curr = salida_encontrada
            while curr is not None:
                camino_reconstruido.append(curr)
                curr = padres[curr]
            
            # Invierte la lista para que vaya desde la posición actual hasta la salida
            camino_reconstruido.reverse()
            
            # Guardar el camino omitiendo el nodo inicial donde ya se encuentra
            self.camino = camino_reconstruido[1:]
            self.paso_actual_idx = 0

    def paso_bfs(self, ambiente):
        if not self.vivo or self.escapado:
            return

        # 1. Condición de Victoria
        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        # 2. Si no tiene camino calculado o se quedó sin pasos, calcula uno nuevo
        if not self.camino or self.paso_actual_idx >= len(self.camino):
            self.calcular_ruta_bfs(ambiente)
            if not self.camino:
                # No hay ruta posible hacia la salida (bloqueado por fuego o muros)
                return

        # 3. Intentar dar el siguiente paso planificado
        siguiente_pos = self.camino[self.paso_actual_idx]
        nf, nc = siguiente_pos

        # Validar colisión dinámica en tiempo real
        con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
        con_agente = ambiente.matriz_3d[nf, nc, 2] == 1

        if not con_fuego and not con_agente:
            # El paso está libre: Avanza
            self.pos_actual = siguiente_pos
            self.paso_actual_idx += 1
        else:
            # La ruta planificada fue bloqueada dinámicamente por un agente o fuego:
            # Forzar el recalculamiento de la ruta BFS en el siguiente intento
            self.calcular_ruta_bfs(ambiente)


class GestorAgentesBFS:
    def __init__(self, ambiente, num_agentes):
        self.ambiente = ambiente
        posiciones_iniciales = ambiente.obtener_posiciones_iniciales(num_agentes)
        
        self.agentes = [
            AgenteBFS(id_agente=i+1, pos_inicial=pos) 
            for i, pos in enumerate(posiciones_iniciales)
        ]
        
        self.ambiente.colocar_agentes([a.pos_actual for a in self.agentes])

    def mover_turno(self):
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                agente.paso_bfs(self.ambiente)
                self._sincronizar_capa_agentes()

    def evaluar_impacto_fuego(self):
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                f, c = agente.pos_actual
                if self.ambiente.matriz_3d[f, c, 1] == 1:
                    agente.vivo = False
        self._sincronizar_capa_agentes()

    def simulacion_terminada(self):
        return all(not agente.vivo or agente.escapado for agente in self.agentes)

    def _sincronizar_capa_agentes(self):
        self.ambiente.reiniciar_capa_agentes()
        pos_activa = [a.pos_actual for a in self.agentes if a.vivo and not a.escapado]
        self.ambiente.colocar_agentes(pos_activa)
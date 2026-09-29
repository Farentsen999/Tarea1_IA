class AgenteDFS:
    """
    Representa a un agente individual que navega por el mapa utilizando Depth-First Search.
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
        
        self.stack = [pos_inicial]           
        
        self.visitados = set([pos_inicial])  

    def paso_dfs(self, ambiente):
        if not self.vivo or self.escapado:
            return

        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        vecinos_estructurales = []  # sin pared, sin fuego, sin visitar (bloqueo permanente evaluado)
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for df, dc in movimientos:
            nf, nc = f + df, c + dc
            if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
                ya_visitado = (nf, nc) in self.visitados

                if not es_pared and not con_fuego and not ya_visitado:
                    vecinos_estructurales.append((nf, nc))

        # Agentes que están libres de otros agentes actualmente
        vecinos_libres = [
            pos for pos in vecinos_estructurales
            if ambiente.matriz_3d[pos[0], pos[1], 2] == 0
        ]

        if vecinos_libres:
            vecinos_libres.sort(key=lambda pos: ambiente.costo_transito(*pos))
            siguiente = vecinos_libres[0]
            self.stack.append(siguiente)
            self.visitados.add(siguiente)
            self.pos_actual = siguiente
            if ambiente.matriz_3d[siguiente[0], siguiente[1], 0] == 2:
                self.escapado = True
        elif vecinos_estructurales:
            #solo está bloqueado de forma pasajera.
            return
        else:
            # Callejón sin salida real: todos los vecinos son pared, fuego, o ya
            # fueron visitados por este agente. Aquí sí corresponde retroceder.
            if len(self.stack) > 1:
                self.stack.pop()
                self.pos_actual = self.stack[-1]


class GestorAgentesDFS:
    """
    Coordinador central encargado de instanciar, controlar el turno de movimiento 
    y sincronizar el estado global de todos los agentes DFS en el ambiente.
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
            AgenteDFS(id_agente=i + 1, pos_inicial=pos) 
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
                agente.paso_dfs(self.ambiente)
                
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
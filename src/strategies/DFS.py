class AgenteDFS:
    def __init__(self, id_agente, pos_inicial):
        self.id = id_agente
        self.pos_actual = pos_inicial
        self.vivo = True
        self.escapado = False
        self.stack = [pos_inicial]           # Pila LIFO para DFS
        self.visitados = set([pos_inicial])  # Previene ciclos

    def paso_dfs(self, ambiente):
        # Si ya no está activo, no realiza ningún movimiento
        if not self.vivo or self.escapado:
            return

        # 1. Condición de Victoria: ¿Llegó a una salida?
        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        # 2. Obtener y filtrar vecinos válidos en tiempo real
        vecinos_validos = []
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)] # 4-conectividad
        
        for df, dc in movimientos:
            nf, nc = f + df, c + dc
            if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
                con_agente = ambiente.matriz_3d[nf, nc, 2] == 1
                ya_visitado = (nf, nc) in self.visitados
                
                if not es_pared and not con_fuego and not con_agente and not ya_visitado:
                    vecinos_validos.append((nf, nc))

        # 3. Lógica de Avance / Backtracking
        if vecinos_validos:
            # Avance: Toma un vecino libre, lo mete al stack y actualiza su posición
            siguiente = vecinos_validos[0]
            self.stack.append(siguiente)
            self.visitados.add(siguiente)
            self.pos_actual = siguiente
        else:
            # Backtracking: Retrocede un paso en el stack
            if len(self.stack) > 1:
                self.stack.pop()
                self.pos_actual = self.stack[-1]


class GestorAgentesDFS:
    def __init__(self, ambiente, num_agentes):
        self.ambiente = ambiente
        
        # Desplegar agentes alrededor de la posición de referencia
        posiciones_iniciales = ambiente.obtener_posiciones_iniciales(num_agentes)
        self.agentes = [
            AgenteDFS(id_agente=i+1, pos_inicial=pos) 
            for i, pos in enumerate(posiciones_iniciales)
        ]
        
        # Reflejar posiciones en la Capa 2
        self.ambiente.colocar_agentes([a.pos_actual for a in self.agentes])

    def mover_turno(self):
        """Ejecuta 1 paso para cada agente y actualiza la Capa 2 inmediatamente."""
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                agente.paso_dfs(self.ambiente)
                
                # Actualizar Capa 2 tras CADA movimiento individual para evitar colisiones
                self._sincronizar_capa_agentes()

    def evaluar_impacto_fuego(self):
        """Revisa si el fuego recién propagado alcanzó a algún agente."""
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                f, c = agente.pos_actual
                if self.ambiente.matriz_3d[f, c, 1] == 1:
                    agente.vivo = False
        
        self._sincronizar_capa_agentes()

    def simulacion_terminada(self):
        """Devuelve True cuando TODOS los agentes o bien escaparon o murieron."""
        return all(not agente.vivo or agente.escapado for agente in self.agentes)

    def _sincronizar_capa_agentes(self):
        """Limpia y vuelve a marcar a los agentes vivos en la Capa 2."""
        self.ambiente.reiniciar_capa_agentes()
        pos_activa = [a.pos_actual for a in self.agentes if a.vivo and not a.escapado]
        self.ambiente.colocar_agentes(pos_activa)
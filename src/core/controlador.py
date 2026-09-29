class ControladorSimulacion:
    def __init__(self, ambiente, gestor_estrategia, k_fuego=3, max_turnos=1000):
        self.ambiente = ambiente
        self.gestor = gestor_estrategia
        self.k_fuego = k_fuego
        self.max_turnos = max_turnos
        self.turnos = 0

    def avanzar_turno(self):
        """
        Ejecuta el ciclo de un único turno en la simulación.
        Este método es invocado por el Benchmark o por el bucle de renderizado de la GUI.
        """
        if self.esta_terminada():
            return

        self.turnos += 1

        # 1. Movimiento de agentes según su estrategia
        self.gestor.mover_turno()

        # 2. Registrar tránsito de los agentes activos en su celda actual.
        for agente in self.gestor.agentes:
            if agente.vivo and not agente.escapado:
                f, c = agente.pos_actual
                self.ambiente.registrar_transito(f, c)
        self.ambiente.decaer_transito()

        # 3. Propagación del fuego cada k_fuego turnos
        if self.turnos % self.k_fuego == 0:
            self.ambiente.propagar_fuego()

        # 4. Evaluación de impacto del fuego sobre los agentes
        self.gestor.evaluar_impacto_fuego()

        # 5. Registrar en qué turno escapó cada agente (solo la primera vez
        #    que se detecta).
        for agente in self.gestor.agentes:
            if agente.escapado and not hasattr(agente, "turno_escape"):
                agente.turno_escape = self.turnos

    def esta_terminada(self):
        """
        Indica si la simulación ha llegado a un estado final.
        """
        alcanzo_limite = self.turnos >= self.max_turnos
        agentes_resueltos = self.gestor.simulacion_terminada()
        return agentes_resueltos or alcanzo_limite

    def obtener_estadisticas(self):
        """
        Retorna las métricas finales de la simulación.
        """
        escapados = [a for a in self.gestor.agentes if a.escapado]
        sobrevivientes = len(escapados)
        total_agentes = len(self.gestor.agentes)

        if escapados:
            turnos_despeje = max(getattr(a, "turno_escape", self.turnos) for a in escapados)
        else:
            turnos_despeje = None

        return {
            "sobrevivientes": sobrevivientes,
            "total_agentes": total_agentes,
            "turnos_despeje": turnos_despeje
        }
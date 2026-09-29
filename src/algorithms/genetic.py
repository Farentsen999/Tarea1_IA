import random
import math

# Mapeo de genes discretos (0, 1, 2, 3) a desplazamientos (fila, columna)
DIRECCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Arriba, Abajo, Izquierda, Derecha

class AgenteGen:
    """
    Representa a un agente individual que navega por el mapa utilizando un algoritmo genético, el cual
    posee su propio motor evolutivo interno *(basado en la clase Agent del repo).
    """
    def __init__(self, id_agente, pos_inicial, longitud_cromosoma=20):
        """
        Inicializa el agente y establece los parámetros del Algoritmo Genético.

        Parámetros:
        - id_agente (int): Identificador único.
        - pos_inicial (tuple): Coordenadas de inicio (fila, columna).
        - longitud_cromosoma (int): Cantidad de movimientos (genes) por individuo.
        """
        self.id = id_agente
        self.pos_actual = pos_inicial
        self.vivo = True          # Estado de supervivencia
        self.escapado = False     # Estado de éxito (llegada a la salida)
        
        # Hiperparámetros evolutivos (adaptados del repositorio)
        self.longitud_cromosoma = longitud_cromosoma
        self.tam_poblacion = 25   # Tamaño de la población candidato
        self.generaciones = 15    # Iteraciones del ciclo evolutivo
        self.tasa_cruce = 0.8     # Probabilidad de aplicar crossover
        self.tasa_mutacion = 0.05 # Probabilidad de mutar cada gen *(5% como en el repo)
        
        self.camino = []          # Lista de coordenadas transitables calculada
        self.paso_actual_idx = 0  # Índice del paso dentro de self.camino

    def _generar_cromosoma_aleatorio(self):
        """
        Crea un cromosoma (secuencia de movimientos aleatorios).
        *Equivale a Agent::CreateMoves() del repo.
        """
        return [random.randint(0, 3) for _ in range(self.longitud_cromosoma)]

    def _evaluar_fitness(self, cromosoma, ambiente):
            """
            Calcula el valor de aptitud evaluando la simulación
            del cromosoma en el mapa utilizando Distancia Manhattan, 
            penalización por choque y penalización por repetición de casillas.
            """
            curr_f, curr_c = self.pos_actual
            pasos_dados = 0
            alcanzo_meta = False

            # 1. Variables de control fuera del bucle
            casillas_visitadas_en_sim = set([(curr_f, curr_c)])
            repetidas = 0
            penalizacion_congestion = 0.0

            for gen in cromosoma:
                df, dc = DIRECCIONES[gen]
                nf, nc = curr_f + df, curr_c + dc
                pasos_dados += 1

                # Validar límites de la matriz
                if not (0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas):
                    break 

                es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                es_salida = ambiente.matriz_3d[nf, nc, 0] == 2
                con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1

                # Recompensa si alcanza una salida
                if es_salida:
                    alcanzo_meta = True
                    curr_f, curr_c = nf, nc
                    penalizacion_congestion += ambiente.costo_transito(nf, nc) - 1.0
                    break

                # Penalización si se estrella contra pared o toca fuego
                if es_pared or con_fuego:
                    break 

                # Penalización por congestión en CADA casilla recorrida
                penalizacion_congestion += ambiente.costo_transito(nf, nc) - 1.0

                # Contador de casillas repetidas en el recorrido virtual
                if (nf, nc) in casillas_visitadas_en_sim:
                    repetidas += 1
                else:
                    casillas_visitadas_en_sim.add((nf, nc))

                # Avanzar posición virtual
                curr_f, curr_c = nf, nc

            # 2. Cálculo base de Fitness Score
            if ambiente.posiciones_salidas:
                dist_manhattan = min(
                    abs(curr_f - sf) + abs(curr_c - sc)
                    for sf, sc in ambiente.posiciones_salidas
                )
                
                if dist_manhattan == 0 or alcanzo_meta:
                    fitness = 1000.0 + (self.longitud_cromosoma - pasos_dados) * 10
                else:
                    penalizacion_choque = (self.longitud_cromosoma - pasos_dados) * 2
                    fitness = 1.0 / (dist_manhattan + 0.001) - penalizacion_choque
            else:
                fitness = 0.0001

            # 3. Aplicar penalización por casillas repetidas al fitness final
            fitness -= (repetidas * 0.5)
            fitness -= (penalizacion_congestion * 0.3)

            return fitness

    def _seleccionar_padre_torneo(self, poblacion_evaluada, k=3):
        """
        Selección por torneo: robusta a fitness negativos.
        """
        participantes = random.sample(poblacion_evaluada, min(k, len(poblacion_evaluada)))
        mejor = max(participantes, key=lambda x: x[1])
        return mejor[0][:]

    def _cruce(self, padre1, padre2):
        """
        Cruce en un solo punto (Single Point Crossover).
        *Basado directamente en Agent::Crossover() de agent.cpp.
        """
        if random.random() < self.tasa_cruce:
            punto = random.randint(1, self.longitud_cromosoma - 1)
            hijo1 = padre1[:punto] + padre2[punto:]
            hijo2 = padre2[:punto] + padre1[punto:]
            return hijo1, hijo2
        return padre1[:], padre2[:]

    def _mutacion(self, cromosoma):
        """
        Aplica mutación gen a gen basada en la tasa de mutación.
        *Basado en Agent::Mutate() de agent.cpp.
        """
        for i in range(len(cromosoma)):
            if random.random() < self.tasa_mutacion:
                cromosoma[i] = random.randint(0, 3)

    def calcular_ruta_ga(self, ambiente):
        """
        Ejecuta la simulación evolutiva completa *(Population::Simulate() en el repo).
        Genera la población, evalúa, cruza, muta y extrae el mejor camino.
        """
        if not ambiente.posiciones_salidas:
            return

        # 1. Crear Población Inicial
        poblacion = [self._generar_cromosoma_aleatorio() for _ in range(self.tam_poblacion)]

        # 2. Bucle de Generaciones
        for _ in range(self.generaciones):
            # Se evalua la aptitud de todos los cromosomas
            poblacion_evaluada = []

            for ind in poblacion:
                fit = self._evaluar_fitness(ind, ambiente)
                poblacion_evaluada.append((ind, fit))

            # Se ordena por aptitud descendente
            poblacion_evaluada.sort(key=lambda x: x[1], reverse=True)

            nueva_poblacion = []

            # Elitismo: Conserva al mejor de la generación intacto
            mejor_individuo = poblacion_evaluada[0][0][:]
            nueva_poblacion.append(mejor_individuo)

            # Se generarnnuevos individuos mediante Selección, Cruce y Mutación
            while len(nueva_poblacion) < self.tam_poblacion:
                padre1 = self._seleccionar_padre_torneo(poblacion_evaluada)
                padre2 = self._seleccionar_padre_torneo(poblacion_evaluada)

                hijo1, hijo2 = self._cruce(padre1, padre2)
                self._mutacion(hijo1)
                self._mutacion(hijo2)

                nueva_poblacion.extend([hijo1, hijo2])

            poblacion = nueva_poblacion[:self.tam_poblacion]

        # 3. Se extrae el mejor cromosoma de la última generación
        poblacion_evaluada = [(ind, self._evaluar_fitness(ind, ambiente)) for ind in poblacion]
        poblacion_evaluada.sort(key=lambda x: x[1], reverse=True)
        mejor_cromosoma = poblacion_evaluada[0][0]

        # 4. Se convierte el mejor cromosoma en coordenadas reales
        self._traducir_cromosoma_a_camino(mejor_cromosoma, ambiente)

    def _traducir_cromosoma_a_camino(self, cromosoma, ambiente):
        """Convierte los genes (direcciones) en tuplas de coordenadas (f, c)."""
        curr_f, curr_c = self.pos_actual
        camino_traducido = []

        for gen in cromosoma:
            df, dc = DIRECCIONES[gen]
            nf, nc = curr_f + df, curr_c + dc

            if 0 <= nf < ambiente.filas and 0 <= nc < ambiente.columnas:
                es_pared = ambiente.matriz_3d[nf, nc, 0] == 1
                con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1

                if not es_pared and not con_fuego:
                    camino_traducido.append((nf, nc))
                    curr_f, curr_c = nf, nc
                else:
                    break
            else:
                break

        self.camino = camino_traducido
        self.paso_actual_idx = 0

    def paso_ga(self, ambiente):
        """Ejecuta el paso correspondiente al turno del agente."""
        if not self.vivo or self.escapado:
            return

        # 1. Condición de Victoria
        f, c = self.pos_actual
        if ambiente.matriz_3d[f, c, 0] == 2:
            self.escapado = True
            return

        # 2. Si no hay camino o se agotó, calcula la ruta evolutiva
        if not self.camino or self.paso_actual_idx >= len(self.camino):
            self.calcular_ruta_ga(ambiente)
            if not self.camino:
                return

        # 3. Mover a la siguiente posición si está libre
        siguiente_pos = self.camino[self.paso_actual_idx]
        nf, nc = siguiente_pos

        con_fuego = ambiente.matriz_3d[nf, nc, 1] == 1
        con_agente = ambiente.matriz_3d[nf, nc, 2] == 1

        if not con_fuego and not con_agente:
            self.pos_actual = siguiente_pos
            self.paso_actual_idx += 1
            # Escape en el mismo turno en que se pisa la salida
            if ambiente.matriz_3d[nf, nc, 0] == 2:
                self.escapado = True
        else:
            # Re-evolucionar ruta si el camino fue bloqueado
            self.calcular_ruta_ga(ambiente)


class GestorAgentesGen:
    """
    Coordinador central para instanciar, controlar y sincronizar la población de agentes A*.
    *Equivale conceptualmente a la clase Population de population.cpp.
    """
    def __init__(self, ambiente, num_agentes):
        self.ambiente = ambiente
        posiciones_iniciales = ambiente.obtener_posiciones_iniciales(num_agentes)
        
        self.agentes = [
            AgenteGen(id_agente=i + 1, pos_inicial=pos) 
            for i, pos in enumerate(posiciones_iniciales)
        ]
        
        self.ambiente.colocar_agentes([a.pos_actual for a in self.agentes])

    def mover_turno(self):
        """
        Ejecuta en secuencia el paso de turno para cada agente activo 
        y luego actualiza la Capa 2 para evitar superposiciones entre compañeros.
        """
        for agente in self.agentes:
            if agente.vivo and not agente.escapado:
                agente.paso_ga(self.ambiente)
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
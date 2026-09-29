import numpy as np
from collections import deque


class Ambiente:
    def __init__(self, ruta_mapa):
        """
        Inicializa el ambiente a partir del mapa estructural con codificación:
        0: Espacio libre, 1: Pared, 2: Salida, 3: Origen Fuego, 4: Punto Partida
        """
        self.ruta_mapa = ruta_mapa
        self.pos_fuego_inicial = None
        self.pos_partida_referencia = None
        self.posiciones_salidas = []

        # Cargar el mapa
        capa_estructural_raw = self._cargar_mapa(ruta_mapa)
        self.filas, self.columnas = capa_estructural_raw.shape

        # Crear matriz 3D
        self.matriz_3d = np.zeros((self.filas, self.columnas, 3), dtype=int)

        # Procesar capas e identificar elementos clave
        self._procesar_capas(capa_estructural_raw)

        # Contador de tránsito por celda.
        self.contador_transito = np.zeros((self.filas, self.columnas), dtype=float)

        # Parámetros globales de la función de costo por congestión.
        self.modo_costo = "cuadratico"
        self.alpha_costo = 1.0

    def _cargar_mapa(self, ruta_mapa):
        """Lee el archivo de texto y lo convierte en un array 2D de NumPy."""
        matriz = []
        with open(ruta_mapa, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    matriz.append([int(char) for char in linea])
        return np.array(matriz)

    def _procesar_capas(self, mapa_raw):
        """Separa la matriz 2D en las 3 capas correspondientes."""
        capa_0 = mapa_raw.copy()

        # Guardar lista de todas las salidas
        self.posiciones_salidas = [tuple(p) for p in np.argwhere(mapa_raw == 2)]

        # Identificar y extraer posición del fuego liberando la capa 0
        indices_fuego = np.argwhere(mapa_raw == 3)
        if len(indices_fuego) > 0:
            f, c = indices_fuego[0]
            self.pos_fuego_inicial = (f, c)
            self.matriz_3d[f, c, 1] = 1
            capa_0[f, c] = 0

        # Identificar y extraer punto de referencia para la partida liberando la capa 0
        indices_partida = np.argwhere(mapa_raw == 4)
        if len(indices_partida) > 0:
            f, c = indices_partida[0]
            self.pos_partida_referencia = (f, c)
            capa_0[f, c] = 0

        # Asignar la Capa 0 con la limpia (solo 0, 1 y 2)
        self.matriz_3d[:, :, 0] = capa_0

    def propagar_fuego(self):
        """
        Expande el fuego 1 paso hacia sus casillas adyacentes (Arriba, Abajo, Izquierda, Derecha)
        siempre que no sean paredes (Capa 0 != 1).
        """
        # 1. Obtener todas las celdas con fuego actual (Capa 1 == 1)
        focos_fuego = np.argwhere(self.matriz_3d[:, :, 1] == 1)

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-conectividad

        # 2. Calcular las nuevas celdas que se encenderán este turno
        nuevos_focos = []
        for f, c in focos_fuego:
            for df, dc in movimientos:
                nf, nc = f + df, c + dc

                # Validar límites de la matriz
                if 0 <= nf < self.filas and 0 <= nc < self.columnas:
                    # El fuego avanza si la celda NO es pared (Capa 0 != 1)
                    # y no tiene fuego activado previamente
                    if self.matriz_3d[nf, nc, 0] != 1 and self.matriz_3d[nf, nc, 1] == 0:
                        nuevos_focos.append((nf, nc))

        # 3. Encender el fuego en la Capa 1 para todos los nuevos focos
        for nf, nc in nuevos_focos:
            self.matriz_3d[nf, nc, 1] = 1

    def obtener_posiciones_iniciales(self, n_agentes, factor_pool=10):
        """
        Calcula N posiciones válidas para desplegar a los agentes al inicio,
        elegidas aleatoriamente dentro de un pool de las celdas más cercanas
        al punto de referencia de partida.

        Parámetros:
        - n_agentes (int): cantidad de agentes a desplegar.
        - factor_pool (int): tamaño del pool de celdas candidatas, como
        múltiplo de n_agentes. Un pool más grande da más variedad entre
        corridas pero puede alejar a algunos agentes del punto de partida.
        """
        if not self.pos_partida_referencia:
            raise ValueError("El mapa no define un punto de referencia de partida.")

        pool_objetivo = n_agentes * factor_pool
        alcanzables = []
        visitados = set([self.pos_partida_referencia])
        cola = deque([self.pos_partida_referencia])

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while cola and len(alcanzables) < pool_objetivo:
            f, c = cola.popleft()

            # Las salidas no son puntos de partida válidos ni se atraviesan al explorar.
            if self.matriz_3d[f, c, 0] == 2:
                continue

            # Espacio libre sin fuego: entra al pool de candidatos.
            if self.matriz_3d[f, c, 0] == 0 and self.matriz_3d[f, c, 1] == 0:
                alcanzables.append((f, c))

            for df, dc in movimientos:
                nf, nc = f + df, c + dc
                if 0 <= nf < self.filas and 0 <= nc < self.columnas:
                    if (nf, nc) in visitados:
                        continue
                    visitados.add((nf, nc))
                    # No expandir a través de paredes ni fuego: así el pool
                    # contiene solo celdas realmente alcanzables a pie.
                    if self.matriz_3d[nf, nc, 0] == 1 or self.matriz_3d[nf, nc, 1] == 1:
                        continue
                    cola.append((nf, nc))

        if len(alcanzables) < n_agentes:
            raise ValueError(
                f"Solo hay {len(alcanzables)} celdas alcanzables cerca de la "
                f"partida, pero se pidieron {n_agentes} agentes."
            )

        indices = np.random.choice(len(alcanzables), size=n_agentes, replace=False)
        return [alcanzables[i] for i in indices]

    def colocar_agentes(self, posiciones_agentes):
        """
        Ubica uno o varios agentes según una lista de coordenadas.
        """
        self.reiniciar_capa_agentes()
        for f, c in posiciones_agentes:
            if self.matriz_3d[f, c, 0] != 1:
                self.matriz_3d[f, c, 2] = 1

    def reiniciar_capa_agentes(self):
        """Limpia la Capa 2 (Agentes)."""
        self.matriz_3d[:, :, 2] = 0

    def reiniciar_capa_fuego(self):
        """Restablece el fuego solo a su punto inicial."""
        self.matriz_3d[:, :, 1] = 0
        if self.pos_fuego_inicial:
            f, c = self.pos_fuego_inicial
            self.matriz_3d[f, c, 1] = 1

    def obtener_estado(self):
        """Retorna la matriz tridimensional completa."""
        return self.matriz_3d

    def costo_transito(self, f, c, alpha=None, modo=None):
        """
        Calcula el costo de atravesar la celda (f, c) en función de su nivel
        reciente de ocupación (self.contador_transito).

        Parámetros:
        - alpha (float): intensidad de la penalización.
        - modo (str): "lineal", "cuadratico" o "exponencial".

        Retorna:
        - float: costo >= 1 de moverse hacia esa celda.
        """
        if alpha is None:
            alpha = self.alpha_costo
        if modo is None:
            modo = self.modo_costo
        ocupacion = self.contador_transito[f, c]

        if modo == "lineal":
            return 1.0 + alpha * ocupacion
        elif modo == "cuadratico":
            return 1.0 + alpha * (ocupacion ** 2)
        elif modo == "exponencial":
            return float(np.exp(alpha * ocupacion))
        else:
            raise ValueError(f"Modo de costo desconocido: {modo}")

    def registrar_transito(self, f, c, incremento=1.0):
        """Suma tránsito a una celda. Llamar por cada agente que la ocupa tras moverse."""
        self.contador_transito[f, c] += incremento

    def decaer_transito(self, factor=0.7):
        """
        Atenúa el contador de tránsito de todo el mapa.
        """
        self.contador_transito *= factor
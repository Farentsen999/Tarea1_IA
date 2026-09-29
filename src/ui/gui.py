import sys
import pygame
from src.core.ambiente import Ambiente
from src.core.controlador import ControladorSimulacion

# Paleta de colores RGB
COLOR_VACIO = (245, 245, 245)      # Blanco grisáceo
COLOR_PARED = (40, 40, 40)         # Gris oscuro
COLOR_FUEGO = (235, 60, 35)        # Rojo/Naranja
COLOR_SALIDA = (46, 204, 113)      # Verde
COLOR_AGENTE = (52, 152, 219)      # Azul
COLOR_TEXTO = (20, 20, 20)
COLOR_PANEL = (220, 220, 220)


class SimuladorGUI:
    def __init__(self, ruta_mapa, ClaseGestor, num_agentes=25, k_fuego=3, celda_tam=20, fps=10):
        pygame.init()
        pygame.font.init()

        self.fps = fps
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("Arial", 16, bold=True)

        # Instanciación de componentes
        self.ambiente = Ambiente(ruta_mapa)
        self.gestor = ClaseGestor(self.ambiente, num_agentes=num_agentes)
        self.controlador = ControladorSimulacion(self.ambiente, self.gestor, k_fuego=k_fuego)

        # Dimensiones de ventana segun la matriz del ambiente
        self.filas = len(self.ambiente.matriz_3d)
        self.columnas = len(self.ambiente.matriz_3d[0]) if self.filas > 0 else 0
        self.alto_panel = 50

        # Ajustar tamaño de celda para que el mapa quepa en la pantalla
        ancho_disp, alto_disp = pygame.display.get_desktop_sizes()[0]
        max_ancho = int(ancho_disp * 0.85)
        max_alto = int(alto_disp * 0.75) - self.alto_panel
        self.celda_tam = max(4, min(celda_tam,
                                    max_ancho // self.columnas,
                                    max_alto // self.filas))

        self.ancho_mapa = self.columnas * self.celda_tam
        self.alto_mapa = self.filas * self.celda_tam

        self.pantalla = pygame.display.set_mode((self.ancho_mapa, self.alto_mapa + self.alto_panel))
        pygame.display.set_caption(f"Evacuación - {ClaseGestor.__name__}")

        self.ejecutando = True
        self.pausado = False

    def renderizar(self):
        """Dibuja la matriz del mapa, los agentes y el panel de control."""
        self.pantalla.fill(COLOR_VACIO)

        # 1. Dibujar celdas del ambiente
        for r in range(self.filas):
            for c in range(self.columnas):
                rect = pygame.Rect(c * self.celda_tam, r * self.celda_tam, self.celda_tam, self.celda_tam)

                estructura = int(self.ambiente.matriz_3d[r, c, 0])
                hay_fuego = int(self.ambiente.matriz_3d[r, c, 1]) == 1

                if estructura == 1:        # Pared
                    pygame.draw.rect(self.pantalla, COLOR_PARED, rect)
                elif hay_fuego:            # Fuego (se dibuja sobre celdas no pared)
                    pygame.draw.rect(self.pantalla, COLOR_FUEGO, rect)
                elif estructura == 2:      # Salida
                    pygame.draw.rect(self.pantalla, COLOR_SALIDA, rect)

                # Rejilla suave
                pygame.draw.rect(self.pantalla, (220, 220, 220), rect, 1)
        
        # 2. Dibujar agentes activos
        for agente in self.gestor.agentes:
            if agente.vivo and not agente.escapado:
                r, c = agente.pos_actual
                centro = (c * self.celda_tam + self.celda_tam // 2, r * self.celda_tam + self.celda_tam // 2)
                radio = max(2, self.celda_tam // 2 - 2)
                pygame.draw.circle(self.pantalla, COLOR_AGENTE, centro, radio)

        # 3. Panel de estado inferior
        panel_rect = pygame.Rect(0, self.alto_mapa, self.ancho_mapa, self.alto_panel)
        pygame.draw.rect(self.pantalla, COLOR_PANEL, panel_rect)

        stats = self.controlador.obtener_estadisticas()
        vivos = sum(1 for a in self.gestor.agentes if a.vivo and not a.escapado)
        
        info = (f"Turno: {self.controlador.turnos} | "
                f"Escapados: {stats['sobrevivientes']} | "
                f"En riesgo: {vivos} | "
                f"Estado: {'PAUSADO' if self.pausado else 'CORRIENDO'}")

        texto_surface = self.fuente.render(info, True, COLOR_TEXTO)
        self.pantalla.blit(texto_surface, (10, self.alto_mapa + 15))

        pygame.display.flip()
        
    def iniciar(self):
        """Bucle principal de la interfaz visual."""
        try:
            while self.ejecutando:
                self.reloj.tick(self.fps)

                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        self.ejecutando = False
                    elif evento.type == pygame.KEYDOWN:
                        if evento.key in (pygame.K_ESCAPE, pygame.K_q):
                            self.ejecutando = False
                        elif evento.key == pygame.K_SPACE:
                            self.pausado = not self.pausado
                        elif evento.key == pygame.K_RIGHT and self.pausado:
                            self.controlador.avanzar_turno()

                if not self.pausado and not self.controlador.esta_terminada():
                    self.controlador.avanzar_turno()

                self.renderizar()
        finally:
            pygame.quit()
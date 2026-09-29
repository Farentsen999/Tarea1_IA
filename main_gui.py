from src.ui.gui import SimuladorGUI

from src.algorithms.bfs import GestorAgentesBFS
from src.algorithms.dfs import GestorAgentesDFS
from src.algorithms.gbfs import GestorAgentesGBFS
from src.algorithms.a_star import GestorAgentesAStar
from src.algorithms.genetic import GestorAgentesGen


def main():
    MAPA_SELECCIONADO = "mapas/ambiente3.txt"
    ESTRATEGIA_SELECCIONADA = GestorAgentesDFS

    simulador = SimuladorGUI(
        ruta_mapa=MAPA_SELECCIONADO,
        ClaseGestor=ESTRATEGIA_SELECCIONADA,
        num_agentes=25,
        k_fuego=3,
        celda_tam=50,  
        fps=8           
    )

    simulador.iniciar()


if __name__ == "__main__":
    main()
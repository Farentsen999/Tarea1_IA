import math
import csv
import time
import random
import statistics
import numpy as np

from src.core.ambiente import Ambiente
from src.core.controlador import ControladorSimulacion

from src.algorithms.bfs import GestorAgentesBFS
from src.algorithms.dfs import GestorAgentesDFS
from src.algorithms.gbfs import GestorAgentesGBFS
from src.algorithms.a_star import GestorAgentesAStar
from src.algorithms.genetic import GestorAgentesGen

ESTRATEGIAS = {
    "BFS (No Informada)": GestorAgentesBFS,
    "DFS (No Informada)": GestorAgentesDFS,
    "GBFS (Informada)": GestorAgentesGBFS,
    "A* (Informada)": GestorAgentesAStar,
    "GA (Algoritmo Genético)": GestorAgentesGen
}

MAPAS = {
    "Mapa 1": "data/mapas/ambiente1.txt",
    "Mapa 2": "data/mapas/ambiente2.txt",
    "Mapa 3": "data/mapas/ambiente3.txt"
}


def ejecutar_iteracion(ruta_mapa, ClaseGestor, seed_iteracion, num_agentes=25, k_fuego=3):
    """
    Instancia los componentes, delega la simulación al Controlador y retorna los datos.
    """
    # Se fijan ambos generadores de aleatoriedad: np.random (usado por
    # Ambiente.obtener_posiciones_iniciales) y random (usado por el
    # algoritmo genético).
    np.random.seed(seed_iteracion)
    random.seed(seed_iteracion)

    ambiente = Ambiente(ruta_mapa)
    gestor = ClaseGestor(ambiente, num_agentes=num_agentes)
    controlador = ControladorSimulacion(ambiente, gestor, k_fuego=k_fuego)

    # Bucle de ejecución del experimento a través del controlador
    while not controlador.esta_terminada():
        controlador.avanzar_turno()

    stats = controlador.obtener_estadisticas()
    return stats["sobrevivientes"], stats["total_agentes"], stats["turnos_despeje"]


def correr_benchmark_completo(num_iteraciones=3000, num_agentes=1000, k_fuego=3000):
    """
    Ejecuta la evaluación cuantitativa y guarda los resultados en CSV.
    """
    resultados_globales = []

    print("=" * 85)
    print(f" INICIANDO BENCHMARK DE EVALUACIÓN ({num_iteraciones} ITERACIONES POR PRUEBA)")
    print("=" * 85)

    for nombre_mapa, ruta_mapa in MAPAS.items():
        print(f"\n EVALUANDO ENTORNOS EN: {nombre_mapa} ({ruta_mapa})")
        print("-" * 85)

        for nombre_algo, ClaseGestor in ESTRATEGIAS.items():
            t0 = time.time()

            lista_sobrevivientes = []
            lista_total_agentes = []
            lista_turnos = []
            fallos = 0

            for i in range(num_iteraciones):
                seed = (i + 1) * 100
                try:
                    sobr, tot, t_despeje = ejecutar_iteracion(
                        ruta_mapa, ClaseGestor, seed, num_agentes, k_fuego
                    )
                except Exception as e:
                    # Una iteración fallida no debe tirar las 3000 corridas
                    # del benchmark completo; se registra y se sigue.
                    fallos += 1
                    print(f"  [!] {nombre_algo} / {nombre_mapa} / iteración {i} "
                        f"(seed={seed}) falló: {e}")
                    continue

                lista_sobrevivientes.append(sobr)
                lista_total_agentes.append(tot)
                if t_despeje is not None:
                    lista_turnos.append(t_despeje)

            if not lista_total_agentes:
                print(f"[{nombre_algo.ljust(24)}] -> TODAS las iteraciones fallaron, "
                    f"se omite del CSV.")
                continue

            tasa_supervivencia = (sum(lista_sobrevivientes) / sum(lista_total_agentes)) * 100

            if lista_turnos:
                media_turnos = statistics.mean(lista_turnos)
                std_turnos = statistics.stdev(lista_turnos) if len(lista_turnos) > 1 else 0.0
                min_turnos = min(lista_turnos)
                max_turnos = max(lista_turnos)
            else:
                media_turnos = std_turnos = min_turnos = max_turnos = math.nan

            tiempo_exec = time.time() - t0

            registro = {
                "Mapa": nombre_mapa,
                "Algoritmo": nombre_algo,
                "Tasa_Supervivencia_%": round(tasa_supervivencia, 2),
                "Media_Turnos": round(media_turnos, 2),
                "Std_Turnos": round(std_turnos, 2),
                "Min_Turnos": min_turnos,
                "Max_Turnos": max_turnos,
                "Iteraciones_Fallidas": fallos,
                "Tiempo_Exec_Sec": round(tiempo_exec, 2)
            }
            resultados_globales.append(registro)

            print(f"[{nombre_algo.ljust(24)}] -> Supervivencia: {tasa_supervivencia:6.2f}% | "
                f"Media Turnos: {media_turnos:6.2f} (±{std_turnos:5.2f}) | "
                f"Rango: [{min_turnos}, {max_turnos}] | Fallidas: {fallos} | "
                f"Tiempo: {tiempo_exec:6.2f}s")

    archivo_csv = "benchmark_results.csv"
    campos = ["Mapa", "Algoritmo", "Tasa_Supervivencia_%", "Media_Turnos", "Std_Turnos",
            "Min_Turnos", "Max_Turnos", "Iteraciones_Fallidas", "Tiempo_Exec_Sec"]

    with open(archivo_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados_globales)

    print("\n" + "=" * 85)
    print(f" BENCHMARK FINALIZADO. Resultados guardados en '{archivo_csv}'")
    print("=" * 85)


if __name__ == "__main__":
    correr_benchmark_completo(num_iteraciones=3)
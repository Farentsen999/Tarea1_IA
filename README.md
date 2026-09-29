# Tarea 1 — Escape de la Torre

## Integrantes

- Francisco Arentsen San Martín

## Estructura del repositorio

```
.
├── main.py                    # Punto de entrada del benchmark (sin GUI)
├── main_gui.py                 # Punto de entrada de la visualización interactiva
├── requirements.txt
├── benchmark_results.csv       # Resultados de la última corrida completa
├── Informe/
│   └── InformeTarea1.tex       # Informe en LaTeX
|   |__ Imagen-sin-título.ico   # Logo UdeC
├── mapas/
│   ├── ambiente1.txt           # Mapa 1 (cuello de botella) — formato 0-4
│   ├── ambiente2.txt           # Mapa 2 (laberinto corporativo) — formato 0-4
│   ├── ambiente3.txt           # Mapa 3 (dispersión abierta) — formato 0-4
│   └── Claude_Ambiente*_64x64.txt   # Mapas originales (formato # / espacio), antes de convertir
└── src/
    ├── core/
    │   ├── ambiente.py          # Estado del mundo: estructura, fuego, agentes, congestión
    │   ├── controlador.py       # Orquesta un turno de simulación
    │   └── conversor_de_mapas.py  # Convierte mapas #/espacio al formato 0-4
    ├── algorithms/
    │   ├── bfs.py
    │   ├── dfs.py
    │   ├── gbfs.py
    │   ├── a_star.py
    │   └── genetic.py
    ├── simulation/
    │   └── benchmark.py         # Corre el experimento masivo y genera el CSV
    └── ui/
        └── gui.py                # Visualización con pygame
```

## Requisitos

```
pip install -r requirements.txt
```

Se usa `pygame-ce` (Pygame Community Edition), no el paquete `pygame` clásico.


### Benchmark completo

```bash
python main.py
```

Corre las 5 estrategias sobre los 3 mapas (configuración actual:
`num_iteraciones=128`, `num_agentes=25`, `k_fuego=3`) y guarda los resultados
en `benchmark_results.csv`. Con esta configuración, la corrida completa toma
aproximadamente 3 horas (el Algoritmo Genético es, por lejos, el más costoso).

Para una prueba rápida antes de lanzar la corrida completa, se recomienda
llamar `correr_benchmark_completo(num_iteraciones=3)` primero.

### Visualización interactiva

```bash
python main_gui.py
```

Por defecto corre `GestorAgentesDFS` sobre `mapas/ambiente3.txt` — para
probar otra combinación, editar `MAPA_SELECCIONADO` y
`ESTRATEGIA_SELECCIONADA` en `main_gui.py`.

Controles:

| Tecla | Acción |
|---|---|
| `ESPACIO` | Pausar / reanudar |
| `→` | Avanzar un turno (estando en pausa) |
| `ESC` / `Q` | Salir |

## Resultados

La última corrida completa (128 iteraciones por combinación) está en
`benchmark_results.csv`. Resumen de tasa de supervivencia:

| Mapa | BFS | DFS | GBFS | A* | GA |
|---|---|---|---|---|---|
| 1 (cuello de botella) | 100% | 0% | 100% | 100% | 4.5% |
| 2 (laberinto corporativo) | 37.5% | 0% | 49.75% | 39.4% | 0% |
| 3 (dispersión abierta) | 98% | 0% | 45.9% | 75.9% | 0% |

Ver `Informe/` para el análisis completo, incluyendo por qué DFS queda en
0% de forma sistemática (deadlock por bloqueo mutuo entre agentes) y por qué
el mapa "más difícil" según su topología no fue el de peor desempeño.

## Créditos y referencias

- Mapas base: [Moving AI Lab](https://www.movingai.com/)
- Algoritmo genético adaptado de: [Genetic-Algorithm-Pathfinding](https://github.com/Pojzo/Genetic-Algorithm-Pathfinding.git) (C++, adaptado a Python)
- Código generado con asistencia de IA generativa (Claude, Anthropic) a partir
  de pseudocódigo propio, luego probado y refactorizado,
from src.simulation.benchmark import correr_benchmark_completo

def main():
    correr_benchmark_completo(
        num_iteraciones=128,  # Reducir para pruebas rápidas
        num_agentes=25,
        k_fuego=3
    )

if __name__ == "__main__":
    main()
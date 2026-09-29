import sys

def convertir_mapa(ruta_archivo_entrada, ruta_archivo_salida):
    """
    Lee un archivo de mapa en formato TXT y convierte sus caracteres:
    - Espacios vacíos (' ') -> 0
    - Paredes o muros ('#') -> 1
    - Salida ('*') -> 2
    - Origen del fuego (&) -> 3
    - Punto de partida (+) -> 4
    """
    
    # Mapeo de reemplazos
    equivalencias = {
        ' ': '0',
        '#': '1',
        '*': '2',
        '&': '3',
        '+': '4'
    }

    try:
        with open(ruta_archivo_entrada, 'r', encoding='utf-8') as f_entrada:
            lineas = f_entrada.readlines()

        lineas_transformadas = []
        
        for linea in lineas:
            # Reemplaza carácter por carácter según el mapeo de remplazos 
            linea_convertida = "".join(equivalencias.get(char, char) for char in linea)
            lineas_transformadas.append(linea_convertida)

        # Guarda la matriz resultante en un nuevo archivo
        with open(ruta_archivo_salida, 'w', encoding='utf-8') as f_salida:
            f_salida.writelines(lineas_transformadas)
            
        print(f"Conversión completada con éxito. Archivo guardado en: {ruta_archivo_salida}")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_archivo_entrada}'.")

if __name__ == "__main__":
    # Nombre de los archivos de entrada y salida
    ambientes_originales = ["mapas/Claude_Ambiente1_64x64.txt", "mapas/Claude_Ambiente2_64x64.txt", "mapas/Claude_Ambiente3_64x64.txt"]
    for i in range(3):
        convertir_mapa(ambientes_originales[i], f"ambientes/ambiente{i+1}.txt")
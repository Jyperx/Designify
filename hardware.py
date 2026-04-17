import os
import json
import multiprocessing

ARCHIVO_CONFIG = "ajustes_designify.json"

def detectar_motor_optimo():
    """
    1. Revisa si el usuario ya eligió un motor antes.
    2. Si es la primera vez que se abre el programa, audita el hardware para decidir.
    """
    # 1. Leer preferencias guardadas (La decisión del usuario manda)
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, 'r') as f:
                config = json.load(f)
                return config.get("motor_render", "CPU")
        except Exception:
            pass

    # 2. AUTO-DETECCIÓN (Si es la primera vez que abren el programa)
    print("🔍 Primera ejecución: Analizando hardware...")
    nucleos = multiprocessing.cpu_count()
    
    # Heurística simple: 
    # Las PCs con 8 núcleos o más (ej. Ryzen 7, Core i7) casi siempre tienen GPU dedicada o pueden manejar el Overhead.
    # Las PCs de 4 núcleos o menos (Laptops sencillas, Core i3) sufren con el Overhead de OpenGL.
    if nucleos >= 8:
        motor_elegido = "GPU"
        print(f"✅ Hardware Potente Detectado ({nucleos} núcleos). Motor GPU (OpenGL) Activado.")
    else:
        motor_elegido = "CPU"
        print(f"⚠️ Hardware Estándar Detectado ({nucleos} núcleos). Motor CPU (Nativo) Activado.")

    # Guardamos la decisión para que no vuelva a calcularlo mañana
    with open(ARCHIVO_CONFIG, 'w') as f:
        json.dump({"motor_render": motor_elegido}, f)

    return motor_elegido
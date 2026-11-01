import socket
import json

HOST = '127.0.0.1'
PORT = 5000

def enviar_tarea(operacion, datos, tarea_id=1, timeout=10.0):
    """Crea el socket TCP, envía la tarea en formato JSON y recibe el resultado."""
    peticion = {
        "id": tarea_id,
        "operacion": operacion,
        "datos": datos
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(timeout)
            client_socket.connect((HOST, PORT))
            
            # Envío con delimitador \n
            mensaje = json.dumps(peticion) + "\n"
            client_socket.sendall(mensaje.encode('utf-8'))
            print(f"\nTarea {tarea_id} enviada ({operacion})")
            
            # Recepción de la respuesta del worker
            buffer = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                if b"\n" in buffer:
                    break
            
            if not buffer:
                print(f"Error: Conexión cerrada sin respuesta del servidor para la tarea {tarea_id}.")
                return None
            
            linea, _ = buffer.split(b"\n", 1)
            resultado = json.loads(linea.decode('utf-8').strip())
            print(f"Respuesta recibida: {resultado}")
            return resultado
            
    except ConnectionRefusedError:
        print(f"No se pudo conectar a {HOST}:{PORT}. Verifique que el servidor esté activo.")
    except socket.timeout:
        print(f"Tiempo de espera agotado ({timeout}s) para la tarea {tarea_id}.")
    except Exception as e:
        print(f"Error gestionando tarea {tarea_id}: {e}")
    return None

def ejecutar_pruebas():
    """Ejecuta una serie de pruebas automatizadas."""
    print("\n--- Iniciando pruebas automáticas ---")
    enviar_tarea(operacion="sumar", datos=[10, 20, 30, 40], tarea_id=101)
    enviar_tarea(operacion="invertir", datos="Sistemas Distribuidos", tarea_id=102)
    enviar_tarea(operacion="sumar", datos="texto_invalido", tarea_id=103)
    print("--- Fin de pruebas automáticas ---\n")

def menu_interactivo():
    """Menú por consola para ingresar datos interactivamente."""
    contador_id = 1
    while True:
        print("\n" + "=" * 40)
        print("CLIENTE TCP - GESTIÓN DE TAREAS")
        print("=" * 40)
        print("1. Sumar números")
        print("2. Invertir texto")
        print("3. Tarea personalizada")
        print("4. Ejecutar pruebas automáticas")
        print("5. Salir")
        print("=" * 40)
        
        try:
            opcion = input("Seleccione una opción (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo del cliente.")
            break

        if opcion == "1":
            entrada = input("Ingrese los números separados por coma o espacio (ej: 10, 20, 35.5): ").strip()
            partes = entrada.replace(",", " ").split()
            if not partes:
                print("Error: Debe ingresar al menos un número.")
                continue
            try:
                datos = [float(p) if '.' in p else int(p) for p in partes]
                enviar_tarea(operacion="sumar", datos=datos, tarea_id=contador_id)
                contador_id += 1
            except ValueError:
                print("Error: Uno o más valores no son números válidos.")
                
        elif opcion == "2":
            texto = input("Ingrese el texto a invertir: ")
            enviar_tarea(operacion="invertir", datos=texto, tarea_id=contador_id)
            contador_id += 1
            
        elif opcion == "3":
            op_nombre = input("Ingrese el nombre de la tarea: ").strip()
            if not op_nombre:
                print("Error: El nombre de la tarea no puede estar vacío.")
                continue
            datos = input("Ingrese los datos a enviar: ")
            enviar_tarea(operacion=op_nombre, datos=datos, tarea_id=contador_id)
            contador_id += 1
            
        elif opcion == "4":
            ejecutar_pruebas()
            
        elif opcion == "5":
            print("Cerrando cliente.")
            break
        else:
            print("Opción inválida. Ingrese un número del 1 al 5.")

if __name__ == "__main__":
    menu_interactivo()
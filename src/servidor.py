import socket
import json
import time
from concurrent.futures import ThreadPoolExecutor

HOST = '0.0.0.0'
PORT = 5000
MAX_CONEXIONES_WORKERS = 10
MAX_TAREAS_PARALELO = 4

# Simulación de pool de workers internos para procesamiento
worker_pool = ThreadPoolExecutor(max_workers=MAX_TAREAS_PARALELO)

def ejecutar_tarea_worker(tarea_id, operacion, datos):
    """Lógica ejecutada por un worker del pool."""
    print(f"[Worker] Procesando tarea {tarea_id}: '{operacion}'")
    time.sleep(2)  # Simula cómputo o interacción con storage distribuido
    
    try:
        if operacion == "sumar":
            if not isinstance(datos, (list, tuple)):
                raise ValueError("La operación 'sumar' requiere una lista o tupla de números.")
            resultado = sum(datos)
        elif operacion == "invertir":
            resultado = str(datos)[::-1]
        else:
            resultado = f"Operación '{operacion}' ejecutada con éxito"
            
        return {
            "tarea_id": tarea_id,
            "estado": "COMPLETADA",
            "resultado": resultado
        }
    except Exception as e:
        print(f"[Worker] Error en tarea {tarea_id}: {e}")
        return {
            "tarea_id": tarea_id,
            "estado": "ERROR",
            "error": str(e)
        }

def manejar_cliente(conn, addr):
    """Maneja la recepción de la tarea y la entrega al pool de ejecución."""
    print(f"Conexión establecida desde {addr}")
    buffer = b""
    try:
        with conn:
            while True:
                # Procesa todas las solicitudes completas que se encuentren en el búfer
                while b"\n" in buffer:
                    linea_bytes, buffer = buffer.split(b"\n", 1)
                    linea_str = linea_bytes.decode('utf-8').strip()
                    if not linea_str:
                        continue
                    
                    try:
                        solicitud = json.loads(linea_str)
                    except json.JSONDecodeError:
                        error_resp = {
                            "estado": "ERROR",
                            "error": "Formato JSON inválido"
                        }
                        conn.sendall((json.dumps(error_resp) + "\n").encode('utf-8'))
                        continue
                    
                    t_id = solicitud.get("id")
                    op = solicitud.get("operacion")
                    payload = solicitud.get("datos")
                    
                    # Delegación asíncrona al pool de workers
                    futuro = worker_pool.submit(ejecutar_tarea_worker, t_id, op, payload)
                    resultado_final = futuro.result()  # Espera resultado para responder
                    
                    respuesta = json.dumps(resultado_final) + "\n"
                    conn.sendall(respuesta.encode('utf-8'))

                # Lectura de datos adicionales del socket
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
    except Exception as e:
        print(f"Error gestionando conexión con {addr}: {e}")
    finally:
        print(f"Conexión cerrada con {addr}")

def iniciar_servidor():
    """Inicializa el socket de escucha TCP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((HOST, PORT))
    server_socket.listen(128)
    server_socket.settimeout(1.0)  # Permite responder a KeyboardInterrupt (Ctrl+C) en Windows
    print(f"Servidor de sockets escuchando en {HOST}:{PORT}")
    
    # Pool para atender múltiples clientes simultáneamente
    with ThreadPoolExecutor(max_workers=MAX_CONEXIONES_WORKERS) as listener_pool:
        try:
            while True:
                try:
                    conn, addr = server_socket.accept()
                    listener_pool.submit(manejar_cliente, conn, addr)
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nApagando servidor...")
        finally:
            server_socket.close()
            worker_pool.shutdown(wait=False)

if __name__ == "__main__":
    iniciar_servidor()
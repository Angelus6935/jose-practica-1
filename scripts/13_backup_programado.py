# ============================================
# Script 13 - Backup programado automatico
# Autor: Jose Angel
# Descripcion: Ejecuta backup de todos los
#              dispositivos automaticamente
#              y mantiene historico de 7 dias
# ============================================

import yaml
import time
import os
import schedule
import threading
from netmiko import ConnectHandler
from datetime import datetime, timedelta

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Backup directo routers -----------------
def backup_directo(dispositivo):
    conexion_params = {
        "device_type":          dispositivo["device_type"],
        "host":                 dispositivo["ip"],
        "username":             dispositivo["username"],
        "password":             dispositivo["password"],
        "global_delay_factor":   2,
        "read_timeout_override": 30,
    }
    conexion = ConnectHandler(**conexion_params)
    config   = conexion.send_command("show running-config")
    conexion.disconnect()
    return config

# -- Backup via jump host switches ----------
def backup_jump(dispositivo):
    jump_params = {
        "device_type":          "cisco_ios",
        "host":                 dispositivo["jump_host"],
        "username":             dispositivo["username"],
        "password":             dispositivo["password"],
        "global_delay_factor":   2,
        "read_timeout_override": 30,
    }
    jump = ConnectHandler(**jump_params)
    jump.write_channel(
        f"ssh -l {dispositivo['username']} {dispositivo['ip']}\n"
    )
    time.sleep(5)
    jump.read_channel()
    jump.write_channel(dispositivo["password"] + "\n")
    time.sleep(5)
    jump.read_channel()
    jump.write_channel("show running-config\n")
    time.sleep(5)
    config = jump.read_channel()
    jump.disconnect()
    return config

# -- Guardar backup -------------------------
def guardar_backup(hostname, config, carpeta):
    fecha  = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{carpeta}/{hostname}_{fecha}.txt"
    with open(nombre, "w") as f:
        f.write(config)
    return nombre

# -- Limpiar backups viejos -----------------
def limpiar_backups_viejos(carpeta_base, dias=7):
    limite = datetime.now() - timedelta(days=dias)
    eliminados = 0
    for carpeta in os.listdir(carpeta_base):
        ruta = os.path.join(carpeta_base, carpeta)
        if os.path.isdir(ruta):
            try:
                fecha_dir = datetime.strptime(carpeta, "%Y%m%d")
                if fecha_dir < limite:
                    for archivo in os.listdir(ruta):
                        os.remove(os.path.join(ruta, archivo))
                    os.rmdir(ruta)
                    eliminados += 1
                    print(f"  🗑️  Carpeta eliminada: {carpeta}")
            except:
                pass
    return eliminados

# -- Ejecutar backup completo ---------------
def ejecutar_backup():
    inicio = datetime.now()
    print(f"\n{'='*55}")
    print(f"  BACKUP AUTOMATICO — {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    # Crear carpeta con fecha
    fecha   = datetime.now().strftime("%Y%m%d")
    carpeta = f"backups/{fecha}"
    os.makedirs(carpeta, exist_ok=True)

    # Cargar inventario
    inventario = cargar_inventario("inventory/devices.yaml")
    todos      = inventario["routers"] + inventario["switches"]

    ok   = 0
    fail = 0

    for dispositivo in todos:
        try:
            print(f"  Backup {dispositivo['hostname']}...")
            if "jump_host" in dispositivo:
                config = backup_jump(dispositivo)
            else:
                config = backup_directo(dispositivo)
            archivo = guardar_backup(dispositivo["hostname"], config, carpeta)
            print(f"  ✅ {dispositivo['hostname']} → {archivo}")
            ok += 1
        except Exception as e:
            print(f"  ❌ {dispositivo['hostname']} → {str(e)[:40]}")
            fail += 1

    # Limpiar backups viejos
    print(f"\n  🗑️  Limpiando backups mayores a 7 dias...")
    eliminados = limpiar_backups_viejos("backups")

    duracion = (datetime.now() - inicio).seconds
    print(f"\n{'='*55}")
    print(f"  Exitosos:  {ok}")
    print(f"  Fallidos:  {fail}")
    print(f"  Eliminados: {eliminados} carpetas viejas")
    print(f"  Duracion:  {duracion} segundos")
    print(f"{'='*55}\n")

# -- Main -----------------------------------
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  BACKUP PROGRAMADO — Jose-practica-1")
    print("="*55)
    print("\n  Horarios programados:")
    print("  → 08:00 AM todos los dias")
    print("  → 20:00 PM todos los dias")
    print("\n  Presiona Ctrl+C para detener\n")

    # Programar backups
    schedule.every().day.at("08:00").do(ejecutar_backup)
    schedule.every().day.at("20:00").do(ejecutar_backup)

    # Ejecutar uno inmediatamente al iniciar
    print("  Ejecutando backup inicial...")
    ejecutar_backup()

    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)
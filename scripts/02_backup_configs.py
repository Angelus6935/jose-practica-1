# ============================================
# Script 02 — Backup de configuraciones
# Autor: Jose Angel
# Descripción: Descarga el running-config de
#              todos los dispositivos y guarda
#              en la carpeta backups/
# ============================================

import yaml
import time
import os
from netmiko import ConnectHandler
from datetime import datetime

# ── Cargar inventario ──────────────────────
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# ── Obtener config via conexión directa ────
def backup_directo(dispositivo):
    conexion_params = {
        "device_type": dispositivo["device_type"],
        "host":        dispositivo["ip"],
        "username":    dispositivo["username"],
        "password":    dispositivo["password"],
    }
    conexion = ConnectHandler(**conexion_params)
    config   = conexion.send_command("show running-config")
    conexion.disconnect()
    return config

# ── Obtener config via jump host ───────────
def backup_jump(dispositivo):
    jump_params = {
        "device_type": "cisco_ios",
        "host":        dispositivo["jump_host"],
        "username":    dispositivo["username"],
        "password":    dispositivo["password"],
    }
    jump = ConnectHandler(**jump_params)

    # SSH desde router al switch
    jump.write_channel(
        f"ssh -l {dispositivo['username']} {dispositivo['ip']}\n"
    )
    time.sleep(5)
    jump.read_channel()  # descartar eco

    # Enviar password
    jump.write_channel(dispositivo["password"] + "\n")
    time.sleep(5)
    jump.read_channel()  # descartar prompt

    # Obtener running-config
    jump.write_channel("show running-config\n")
    time.sleep(5)
    config = jump.read_channel()

    jump.disconnect()
    return config

# ── Guardar backup en archivo ──────────────
def guardar_backup(hostname, config, carpeta):
    fecha    = datetime.now().strftime("%Y%m%d_%H%M")
    nombre   = f"{carpeta}/{hostname}_{fecha}.txt"
    with open(nombre, "w") as archivo:
        archivo.write(config)
    return nombre

# ── Backup de un dispositivo ───────────────
def backup_dispositivo(dispositivo, carpeta):
    try:
        print(f"  Haciendo backup de {dispositivo['hostname']} ({dispositivo['ip']})...")

        # Obtener config según tipo
        if "jump_host" in dispositivo:
            config = backup_jump(dispositivo)
        else:
            config = backup_directo(dispositivo)

        # Guardar archivo
        archivo = guardar_backup(dispositivo["hostname"], config, carpeta)

        print(f"  ✅ Guardado: {archivo}")
        return {"hostname": dispositivo["hostname"], "estado": "✅ OK", "archivo": archivo}

    except Exception as e:
        print(f"  ❌ Error: {dispositivo['hostname']} → {str(e)[:50]}")
        return {"hostname": dispositivo["hostname"], "estado": "❌ FAIL", "error": str(e)}

# ── Reporte final ──────────────────────────
def generar_reporte(resultados, inicio):
    duracion = (datetime.now() - inicio).seconds
    ok   = [r for r in resultados if r["estado"] == "✅ OK"]
    fail = [r for r in resultados if r["estado"] == "❌ FAIL"]

    print("\n" + "="*55)
    print(f"  REPORTE DE BACKUP — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:     {len(resultados)}")
    print(f"  Exitosos:  {len(ok)}")
    print(f"  Fallidos:  {len(fail)}")
    print(f"  Duración:  {duracion} segundos")
    print("\n" + "="*55)

# ── Main ───────────────────────────────────
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n🚀 Iniciando backup de configuraciones...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Crear carpeta de backups con fecha
    fecha   = datetime.now().strftime("%Y%m%d")
    carpeta = f"backups/{fecha}"
    os.makedirs(carpeta, exist_ok=True)
    print(f"  📁 Carpeta: {carpeta}\n")

    # Cargar inventario
    inventario = cargar_inventario("inventory/devices.yaml")
    todos      = inventario["routers"] + inventario["switches"]

    # Hacer backup de cada dispositivo
    resultados = []
    for dispositivo in todos:
        resultado = backup_dispositivo(dispositivo, carpeta)
        resultados.append(resultado)

    # Mostrar reporte
    generar_reporte(resultados, inicio)
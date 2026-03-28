# ============================================
# Script 01 — Verificar conectividad
# Autor: Jose Angel
# Descripción: Conecta a todos los dispositivos
#              usando jump_host para switches
# ============================================

import yaml
import time
from netmiko import ConnectHandler
from datetime import datetime

# ── Cargar inventario ──────────────────────
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# ── Verificar un dispositivo ───────────────
def verificar_dispositivo(dispositivo):
    try:
        print(f"  Conectando a {dispositivo['hostname']} ({dispositivo['ip']})...")

        # Parámetros base
        conexion_params = {
            "device_type": dispositivo["device_type"],
            "host":        dispositivo["ip"],
            "username":    dispositivo["username"],
            "password":    dispositivo["password"],
        }

        # Si tiene jump_host → conectar via router
        if "jump_host" in dispositivo:
            jump_params = {
                "device_type": "cisco_ios",
                "host":        dispositivo["jump_host"],
                "username":    dispositivo["username"],
                "password":    dispositivo["password"],
            }
            # Conectar al jump host
            jump = ConnectHandler(**jump_params)

            # SSH desde router al switch
            jump.write_channel(
                f"ssh -l {dispositivo['username']} {dispositivo['ip']}\n"
            )
            time.sleep(5)

            # Leer respuesta del router (descartamos el eco)
            jump.read_channel()

            # Enviar password
            jump.write_channel(dispositivo["password"] + "\n")
            time.sleep(5)

            # Verificar que llegamos al switch
            output = jump.read_channel()
            

            if "#" in output or ">" in output:
                estado = "✅ OK"
                error  = None
            else:
                estado = "❌ FAIL"
                error  = "No se obtuvo prompt del switch"

            jump.disconnect()

        else:
            # Conexión directa para routers
            conexion = ConnectHandler(**conexion_params)
            conexion.disconnect()
            estado = "✅ OK"
            error  = None

        return {
            "hostname": dispositivo["hostname"],
            "ip":       dispositivo["ip"],
            "site":     dispositivo["site"],
            "estado":   estado,
            "error":    error
        }

    except Exception as e:
        return {
            "hostname": dispositivo["hostname"],
            "ip":       dispositivo["ip"],
            "site":     dispositivo["site"],
            "estado":   "❌ FAIL",
            "error":    str(e)
        }

# ── Generar reporte ────────────────────────
def generar_reporte(resultados):
    print("\n" + "="*55)
    print(f"  REPORTE DE CONECTIVIDAD — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)

    ok   = [r for r in resultados if r["estado"] == "✅ OK"]
    fail = [r for r in resultados if r["estado"] == "❌ FAIL"]

    print(f"\n  Total dispositivos: {len(resultados)}")
    print(f"  Conectados:         {len(ok)}")
    print(f"  Fallidos:           {len(fail)}")
    print("\n" + "-"*55)

    sitio_actual = ""
    for r in resultados:
        if r["site"] != sitio_actual:
            sitio_actual = r["site"]
            print(f"\n  📍 {sitio_actual}")
        print(f"     {r['estado']}  {r['hostname']:<15} {r['ip']}")
        if r["error"]:
            print(f"          ⚠️  {r['error'][:60]}")

    print("\n" + "="*55)

# ── Main ───────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Iniciando verificación de dispositivos...")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Cargar inventario
    inventario = cargar_inventario("inventory/devices.yaml")

    # Combinar routers y switches
    todos = inventario["routers"] + inventario["switches"]

    # Verificar cada dispositivo
    resultados = []
    for dispositivo in todos:
        resultado = verificar_dispositivo(dispositivo)
        resultados.append(resultado)

    # Mostrar reporte
    generar_reporte(resultados)
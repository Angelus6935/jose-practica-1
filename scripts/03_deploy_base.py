# ============================================
# Script 03 — Deploy configuración base
# Autor: Jose Angel
# Descripción: Aplica config base a todos los
#              dispositivos usando Jinja2
# ============================================

import yaml
import time
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# ── Cargar inventario ──────────────────────
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# ── Renderizar template Jinja2 ─────────────
def renderizar_template(dispositivo):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("base_config.j2")

    # Variables para el template
    variables = {
        "hostname": dispositivo["hostname"],
        "site":     dispositivo["site"],
        "role":     dispositivo.get("role", "switch"),
        "mgmt_int": "Ethernet0/3" if dispositivo.get("role") == "router" else "Vlan1",
    }
    return template.render(variables)

# ── Aplicar config directa ─────────────────
def deploy_directo(dispositivo, config):
    conexion_params = {
        "device_type":        dispositivo["device_type"],
        "host":               dispositivo["ip"],
        "username":           dispositivo["username"],
        "password":           dispositivo["password"],
        "global_delay_factor": 2,    # ← agregar esta línea
        "read_timeout_override": 30, # ← agregar esta línea
    }
    conexion = ConnectHandler(**conexion_params)
    output   = conexion.send_config_set(
        config.splitlines(),
        read_timeout=30         # ← agregar este parámetro
    )
    conexion.save_config()
    conexion.disconnect()
    return output

# ── Aplicar config via jump host ───────────
def deploy_jump(dispositivo, config):
    jump_params = {
        "device_type": "cisco_ios",
        "host":        dispositivo["jump_host"],
        "username":    dispositivo["username"],
        "password":    dispositivo["password"],
    }
    jump = ConnectHandler(**jump_params)

    # Conectar al switch
    jump.write_channel(
        f"ssh -l {dispositivo['username']} {dispositivo['ip']}\n"
    )
    time.sleep(5)
    jump.read_channel()
    jump.write_channel(dispositivo["password"] + "\n")
    time.sleep(5)
    jump.read_channel()

    # Enviar configuración línea por línea
    jump.write_channel("configure terminal\n")
    time.sleep(2)

    for linea in config.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("!") and not linea.startswith("{"):
            jump.write_channel(linea + "\n")
            time.sleep(0.5)

    jump.write_channel("end\n")
    time.sleep(2)
    jump.write_channel("write memory\n")
    time.sleep(3)
    output = jump.read_channel()
    jump.disconnect()
    return output

# ── Deploy en un dispositivo ───────────────
def deploy_dispositivo(dispositivo):
    try:
        print(f"  Aplicando config en {dispositivo['hostname']} ({dispositivo['ip']})...")

        # Renderizar template
        config = renderizar_template(dispositivo)

        # Aplicar según tipo
        if "jump_host" in dispositivo:
            output = deploy_jump(dispositivo, config)
        else:
            output = deploy_directo(dispositivo, config)

        print(f"  ✅ {dispositivo['hostname']} — config aplicada")
        return {"hostname": dispositivo["hostname"], "estado": "✅ OK"}

    except Exception as e:
        print(f"  ❌ {dispositivo['hostname']} — Error: {str(e)[:50]}")
        return {"hostname": dispositivo["hostname"], "estado": "❌ FAIL", "error": str(e)}

# ── Reporte final ──────────────────────────
def generar_reporte(resultados, inicio):
    duracion = (datetime.now() - inicio).seconds
    ok   = [r for r in resultados if r["estado"] == "✅ OK"]
    fail = [r for r in resultados if r["estado"] == "❌ FAIL"]

    print("\n" + "="*55)
    print(f"  REPORTE DEPLOY BASE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:     {len(resultados)}")
    print(f"  Exitosos:  {len(ok)}")
    print(f"  Fallidos:  {len(fail)}")
    print(f"  Duración:  {duracion} segundos")
    print("\n" + "="*55)

# ── Main ───────────────────────────────────
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n🚀 Iniciando deploy de configuración base...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Cargar inventario
    inventario = cargar_inventario("inventory/devices.yaml")
    todos      = inventario["routers"] + inventario["switches"]

    # Deploy en cada dispositivo
    resultados = []
    for dispositivo in todos:
        resultado = deploy_dispositivo(dispositivo)
        resultados.append(resultado)

    # Mostrar reporte
    generar_reporte(resultados, inicio)
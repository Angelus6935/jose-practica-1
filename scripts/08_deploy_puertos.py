# ============================================
# Script 08 - Deploy puertos acceso y trunk
# Autor: Jose Angel
# Descripcion: Configura puertos de acceso
#              y trunk en todos los switches
# ============================================

import yaml
import time
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño de puertos por switch -----------
PUERTOS = {
    "BA-SW-CORE": {
        "jump_host": "192.168.249.10",
        "trunks": [
            "Ethernet0/0",
            "Ethernet0/1",
            "Ethernet0/2",
        ],
        "acceso_datos_voz":  [],
        "acceso_ap":         [],
        "acceso_servidores": ["Ethernet0/3", "Ethernet1/0"],
        "acceso_invitados":  [],
    },
    "BA-SW-ACC": {
        "jump_host": "192.168.249.10",
        "trunks": ["Ethernet0/0"],
        "acceso_datos_voz":  ["Ethernet0/1", "Ethernet0/2"],
        "acceso_ap":         ["Ethernet0/3", "Ethernet1/0"],
        "acceso_servidores": [],
        "acceso_invitados":  ["Ethernet1/1"],
    },
    "BHA-SW-CORE": {
        "jump_host": "192.168.249.20",
        "trunks": [
            "Ethernet0/0",
            "Ethernet0/1",
            "Ethernet0/2",
        ],
        "acceso_datos_voz":  [],
        "acceso_ap":         [],
        "acceso_servidores": ["Ethernet0/3", "Ethernet1/0"],
        "acceso_invitados":  [],
    },
    "BHA-SW-ACC": {
        "jump_host": "192.168.249.20",
        "trunks": ["Ethernet0/0"],
        "acceso_datos_voz":  ["Ethernet0/1", "Ethernet0/2"],
        "acceso_ap":         ["Ethernet0/3", "Ethernet1/0"],
        "acceso_servidores": [],
        "acceso_invitados":  ["Ethernet1/1"],
    },
    "NQ-SW-CORE": {
        "jump_host": "192.168.249.30",
        "trunks": [
            "Ethernet0/0",
            "Ethernet0/1",
            "Ethernet0/2",
        ],
        "acceso_datos_voz":  [],
        "acceso_ap":         [],
        "acceso_servidores": ["Ethernet0/3", "Ethernet1/0"],
        "acceso_invitados":  [],
    },
    "NQ-SW-ACC": {
        "jump_host": "192.168.249.30",
        "trunks": ["Ethernet0/0"],
        "acceso_datos_voz":  ["Ethernet0/1", "Ethernet0/2"],
        "acceso_ap":         ["Ethernet0/3", "Ethernet1/0"],
        "acceso_servidores": [],
        "acceso_invitados":  ["Ethernet1/1"],
    },
    "NQSUB-SW-ACC": {
        "jump_host": "192.168.249.40",
        "trunks": ["Ethernet0/0"],
        "acceso_datos_voz":  ["Ethernet0/1", "Ethernet0/2"],
        "acceso_ap":         ["Ethernet0/3", "Ethernet1/0"],
        "acceso_servidores": [],
        "acceso_invitados":  ["Ethernet1/1"],
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("puertos.j2")
    return template.render(**datos)

# -- Aplicar config via jump host -----------
def deploy_jump(dispositivo_inv, datos_puerto, config):
    jump_params = {
        "device_type":          "cisco_ios",
        "host":                 datos_puerto["jump_host"],
        "username":             dispositivo_inv["username"],
        "password":             dispositivo_inv["password"],
        "global_delay_factor":   2,
        "read_timeout_override": 30,
    }
    jump = ConnectHandler(**jump_params)

    # Conectar al switch
    jump.write_channel(
        f"ssh -l {dispositivo_inv['username']} {dispositivo_inv['ip']}\n"
    )
    time.sleep(5)
    jump.read_channel()
    jump.write_channel(dispositivo_inv["password"] + "\n")
    time.sleep(5)
    jump.read_channel()

    # Enviar configuración línea por línea con más delay
    jump.write_channel("configure terminal\n")
    time.sleep(3)

    for linea in config.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("{"):
            jump.write_channel(linea + "\n")
            time.sleep(1)  # ← subido de 0.5 a 1 segundo

    jump.write_channel("end\n")
    time.sleep(3)
    jump.write_channel("write memory\n")
    time.sleep(5)  # ← subido de 3 a 5 segundos
    output = jump.read_channel()
    jump.disconnect()
    return output

# -- Main -----------------------------------
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n Iniciando deploy puertos...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    switches   = {s["hostname"]: s for s in inventario["switches"]}

    resultados = []
    for hostname, datos_puerto in PUERTOS.items():
        try:
            print(f"  Configurando puertos en {hostname}...")
            dispositivo = switches[hostname]
            config      = renderizar_template(datos_puerto)
            deploy_jump(dispositivo, datos_puerto, config)
            total = (
                len(datos_puerto["trunks"]) +
                len(datos_puerto["acceso_datos_voz"]) +
                len(datos_puerto["acceso_ap"]) +
                len(datos_puerto["acceso_servidores"]) +
                len(datos_puerto["acceso_invitados"])
            )
            print(f"  OK {hostname} - {total} puertos configurados")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE PUERTOS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
# ============================================
# Script 07 - Deploy VLANs
# Autor: Jose Angel
# Descripcion: Configura VLANs en todos los
#              switches por sitio
# ============================================

import yaml
import time
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño VLANs por sitio -----------------
VLANS = {
    "BA-SW-CORE": {
        "role":          "core",
        "jump_host":     "192.168.249.10",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
        "svi_datos":      "172.16.0.1",
        "svi_voz":        "172.16.1.1",
        "svi_ap":         "172.16.2.1",
        "svi_servidores": "172.16.3.1",
        "svi_invitados":  "172.16.4.1",
    },
    "BA-SW-ACC": {
        "role":          "access",
        "jump_host":     "192.168.249.10",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
    },
    "BHA-SW-CORE": {
        "role":          "core",
        "jump_host":     "192.168.249.20",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
        "svi_datos":      "172.16.10.1",
        "svi_voz":        "172.16.11.1",
        "svi_ap":         "172.16.12.1",
        "svi_servidores": "172.16.13.1",
        "svi_invitados":  "172.16.14.1",
    },
    "BHA-SW-ACC": {
        "role":          "access",
        "jump_host":     "192.168.249.20",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
    },
    "NQ-SW-CORE": {
        "role":          "core",
        "jump_host":     "192.168.249.30",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
        "svi_datos":      "172.16.20.1",
        "svi_voz":        "172.16.21.1",
        "svi_ap":         "172.16.22.1",
        "svi_servidores": "172.16.23.1",
        "svi_invitados":  "172.16.24.1",
    },
    "NQ-SW-ACC": {
        "role":          "access",
        "jump_host":     "192.168.249.30",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
    },
    "NQSUB-SW-ACC": {
        "role":          "access",
        "jump_host":     "192.168.249.40",
        "vlan_datos":     10,
        "vlan_voz":       20,
        "vlan_ap":        30,
        "vlan_servidores": 40,
        "vlan_invitados": 50,
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("vlans.j2")
    return template.render(**datos)

# -- Aplicar config via jump host -----------
def deploy_jump(dispositivo_inv, datos_vlan, config):
    jump_params = {
        "device_type": "cisco_ios",
        "host":        datos_vlan["jump_host"],
        "username":    dispositivo_inv["username"],
        "password":    dispositivo_inv["password"],
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

    # Enviar configuración
    jump.write_channel("configure terminal\n")
    time.sleep(2)
    for linea in config.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("{"):
            jump.write_channel(linea + "\n")
            time.sleep(0.5)
    jump.write_channel("end\n")
    time.sleep(2)
    jump.write_channel("write memory\n")
    time.sleep(3)
    output = jump.read_channel()
    jump.disconnect()
    return output

# -- Main -----------------------------------
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n Iniciando deploy VLANs...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    switches   = {s["hostname"]: s for s in inventario["switches"]}

    resultados = []
    for hostname, datos_vlan in VLANS.items():
        try:
            print(f"  Configurando VLANs en {hostname} ({datos_vlan['role']})...")
            dispositivo = switches[hostname]
            config      = renderizar_template(datos_vlan)
            deploy_jump(dispositivo, datos_vlan, config)
            print(f"  OK {hostname} - 5 VLANs configuradas")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE VLANs - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
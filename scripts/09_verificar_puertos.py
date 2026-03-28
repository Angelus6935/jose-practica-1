# ============================================
# Script 09 - Verificar puertos switches
# Autor: Jose Angel
# Descripcion: Verifica configuracion de
#              puertos en todos los switches
# ============================================

import yaml
import time
from netmiko import ConnectHandler
from datetime import datetime

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Verificar via jump host ----------------
def verificar_switch(dispositivo, jump_host_ip):
    jump_params = {
        "device_type":          "cisco_ios",
        "host":                 jump_host_ip,
        "username":             dispositivo["username"],
        "password":             dispositivo["password"],
        "global_delay_factor":   2,
        "read_timeout_override": 30,
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

    # Obtener info de puertos
    jump.write_channel("show vlan brief\n")
    time.sleep(3)
    vlan_info = jump.read_channel()

    jump.write_channel("show interfaces trunk\n")
    time.sleep(3)
    trunk_info = jump.read_channel()

    jump.write_channel("show running-config | section interface Ethernet0/1\n")
    time.sleep(3)
    port_info = jump.read_channel()

    jump.disconnect()
    return vlan_info, trunk_info, port_info

# -- Main -----------------------------------
if __name__ == "__main__":
    print("\n Verificando puertos de switches...")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    switches   = inventario["switches"]

    # Jump hosts por sitio
    jump_hosts = {
        "Buenos Aires": "192.168.249.10",
        "Bahia Blanca": "192.168.249.20",
        "Neuquen":      "192.168.249.30",
        "NQ-SUB":       "192.168.249.40",
    }

    for switch in switches:
        print(f"\n{'='*55}")
        print(f"  {switch['hostname']} ({switch['ip']})")
        print(f"{'='*55}")
        try:
            jump_ip = jump_hosts[switch["site"]]
            vlan_info, trunk_info, port_info = verificar_switch(switch, jump_ip)

            print("\n  VLANs:")
            for linea in vlan_info.splitlines():
                if any(x in linea for x in ["10", "20", "30", "40", "50", "DATOS", "VOZ", "AP", "SERV", "INV"]):
                    print(f"    {linea.strip()}")

            print("\n  Trunks:")
            for linea in trunk_info.splitlines():
                if "Et" in linea or "trunking" in linea:
                    print(f"    {linea.strip()}")

            print("\n  Puerto Et0/1:")
            for linea in port_info.splitlines():
                if linea.strip():
                    print(f"    {linea.strip()}")

        except Exception as e:
            print(f"  ERROR: {str(e)[:60]}")
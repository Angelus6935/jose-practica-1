# ============================================
# Script 04 - Deploy interfaces WAN
# Autor: Jose Angel
# Descripcion: Configura subinterfaces WAN
#              en todos los routers
# ============================================

import yaml
import time
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Inventario WAN -------------------------
WAN = {
    "BA-R1": [
        {"interfaz_fisica": "Ethernet0/1", "vlan": 10,
         "ip": "10.1.0.1", "mascara": "255.255.255.252",
         "descripcion": "WAN-BA-BHA-PRIMARIO"},
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.1.1", "mascara": "255.255.255.252",
         "descripcion": "WAN-BA-NQ-PRIMARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.0.1", "mascara": "255.255.255.252",
         "descripcion": "HA-BA-R1-R2"},
    ],
    "BA-R2": [
        {"interfaz_fisica": "Ethernet0/1", "vlan": 10,
         "ip": "10.1.0.5", "mascara": "255.255.255.252",
         "descripcion": "WAN-BA-BHA-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.1.5", "mascara": "255.255.255.252",
         "descripcion": "WAN-BA-NQ-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.0.2", "mascara": "255.255.255.252",
         "descripcion": "HA-BA-R2-R1"},
    ],
    "BHA-R1": [
        {"interfaz_fisica": "Ethernet0/1", "vlan": 10,
         "ip": "10.1.0.2", "mascara": "255.255.255.252",
         "descripcion": "WAN-BHA-BA-PRIMARIO"},
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.2.1", "mascara": "255.255.255.252",
         "descripcion": "WAN-BHA-NQ-PRIMARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.1.1", "mascara": "255.255.255.252",
         "descripcion": "HA-BHA-R1-R2"},
    ],
    "BHA-R2": [
        {"interfaz_fisica": "Ethernet0/1", "vlan": 10,
         "ip": "10.1.0.6", "mascara": "255.255.255.252",
         "descripcion": "WAN-BHA-BA-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.2.5", "mascara": "255.255.255.252",
         "descripcion": "WAN-BHA-NQ-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.1.2", "mascara": "255.255.255.252",
         "descripcion": "HA-BHA-R2-R1"},
    ],
    "NQ-R1": [
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.1.2", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-BA-PRIMARIO"},
        {"interfaz_fisica": "Ethernet0/3", "vlan": 20,
         "ip": "10.1.2.2", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-BHA-PRIMARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.2.1", "mascara": "255.255.255.252",
         "descripcion": "HA-NQ-R1-R2"},
        {"interfaz_fisica": "Ethernet1/1", "vlan": 40,
         "ip": "10.1.3.1", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-NQSUB-PRIMARIO"},
    ],
    "NQ-R2": [
        {"interfaz_fisica": "Ethernet0/2", "vlan": 20,
         "ip": "10.1.1.6", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-BA-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet0/3", "vlan": 20,
         "ip": "10.1.2.6", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-BHA-SECUNDARIO"},
        {"interfaz_fisica": "Ethernet1/0", "vlan": 30,
         "ip": "10.2.2.2", "mascara": "255.255.255.252",
         "descripcion": "HA-NQ-R2-R1"},
        {"interfaz_fisica": "Ethernet1/1", "vlan": 40,
         "ip": "10.1.3.5", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQ-NQSUB-SECUNDARIO"},
    ],
    "NQSUB-R1": [
        {"interfaz_fisica": "Ethernet0/1", "vlan": 40,
         "ip": "10.1.3.2", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQSUB-NQ-PRIMARIO"},
        {"interfaz_fisica": "Ethernet0/2", "vlan": 40,
         "ip": "10.1.3.6", "mascara": "255.255.255.252",
         "descripcion": "WAN-NQSUB-NQ-SECUNDARIO"},
    ],
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(subinterfaces):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("wan_interfaces.j2")
    return template.render(subinterfaces=subinterfaces)

# -- Aplicar config -------------------------
def deploy_wan(dispositivo, config):
    conexion_params = {
        "device_type":         dispositivo["device_type"],
        "host":                dispositivo["ip"],
        "username":            dispositivo["username"],
        "password":            dispositivo["password"],
        "global_delay_factor":  2,
        "read_timeout_override": 30,
    }
    conexion = ConnectHandler(**conexion_params)
    output   = conexion.send_config_set(
        config.splitlines(),
        read_timeout=30
    )
    conexion.save_config()
    conexion.disconnect()
    return output

# -- Main -----------------------------------
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n Iniciando deploy de interfaces WAN...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Cargar inventario
    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    resultados = []
    for hostname, subinterfaces in WAN.items():
        try:
            print(f"  Configurando {hostname}...")
            dispositivo = routers[hostname]
            config      = renderizar_template(subinterfaces)
            deploy_wan(dispositivo, config)
           
            print(f"  OK {hostname} - {len(subinterfaces)} subinterfaces")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    # Reporte
    ok   = [r for r in resultados if r["estado"] == "OK"]
    fail = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE WAN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
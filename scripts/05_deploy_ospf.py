# ============================================
# Script 05 - Deploy OSPF
# Autor: Jose Angel
# Descripcion: Configura OSPF en todos los
#              routers por area y sitio
# Area 0 = enlaces WAN entre sitios
# Area 1 = BA, Area 2 = BHA, Area 3 = NQ
# ============================================

import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño OSPF por router -----------------
OSPF = {
    "BA-R1": {
        "process_id": 1,
        "router_id":  "10.0.0.1",
        "redes_ospf": [
            {"ip": "10.0.0.1",      "wildcard": "0.0.0.0",   "area": 1},
            {"ip": "10.1.0.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.1.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.0.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 1},
        ],
        "interfaces_activas": [
            "Ethernet0/1.10",
            "Ethernet0/2.20",
            "Ethernet1/0.30",
        ],
    },
    "BA-R2": {
        "process_id": 1,
        "router_id":  "10.0.0.2",
        "redes_ospf": [
            {"ip": "10.0.0.2",      "wildcard": "0.0.0.0",   "area": 1},
            {"ip": "10.1.0.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.1.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.0.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 1},
        ],
        "interfaces_activas": [
            "Ethernet0/1.10",
            "Ethernet0/2.20",
            "Ethernet1/0.30",
        ],
    },
    "BHA-R1": {
        "process_id": 1,
        "router_id":  "10.0.1.1",
        "redes_ospf": [
            {"ip": "10.0.1.1",      "wildcard": "0.0.0.0",   "area": 2},
            {"ip": "10.1.0.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.2.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.1.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 2},
        ],
        "interfaces_activas": [
            "Ethernet0/1.10",
            "Ethernet0/2.20",
            "Ethernet1/0.30",
        ],
    },
    "BHA-R2": {
        "process_id": 1,
        "router_id":  "10.0.1.2",
        "redes_ospf": [
            {"ip": "10.0.1.2",      "wildcard": "0.0.0.0",   "area": 2},
            {"ip": "10.1.0.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.2.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.1.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 2},
        ],
        "interfaces_activas": [
            "Ethernet0/1.10",
            "Ethernet0/2.20",
            "Ethernet1/0.30",
        ],
    },
    "NQ-R1": {
        "process_id": 1,
        "router_id":  "10.0.2.1",
        "redes_ospf": [
            {"ip": "10.0.2.1",      "wildcard": "0.0.0.0",   "area": 3},
            {"ip": "10.1.1.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.2.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.3.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.2.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 3},
        ],
        "interfaces_activas": [
            "Ethernet0/2.20",
            "Ethernet0/3.20",
            "Ethernet1/0.30",
            "Ethernet1/1.40",
        ],
    },
    "NQ-R2": {
        "process_id": 1,
        "router_id":  "10.0.2.2",
        "redes_ospf": [
            {"ip": "10.0.2.2",      "wildcard": "0.0.0.0",   "area": 3},
            {"ip": "10.1.1.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.2.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.3.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.2.2.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 3},
        ],
        "interfaces_activas": [
            "Ethernet0/2.20",
            "Ethernet0/3.20",
            "Ethernet1/0.30",
            "Ethernet1/1.40",
        ],
    },
    "NQSUB-R1": {
        "process_id": 1,
        "router_id":  "10.0.3.1",
        "redes_ospf": [
            {"ip": "10.0.3.1",      "wildcard": "0.0.0.0",   "area": 3},
            {"ip": "10.1.3.0",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "10.1.3.4",      "wildcard": "0.0.0.3",   "area": 0},
            {"ip": "192.168.100.0", "wildcard": "0.0.0.255", "area": 3},
        ],
        "interfaces_activas": [
            "Ethernet0/1.40",
            "Ethernet0/2.40",
        ],
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos_ospf):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("ospf.j2")
    return template.render(**datos_ospf)

# -- Aplicar config -------------------------
def deploy_ospf(dispositivo, config):
    conexion_params = {
        "device_type":          dispositivo["device_type"],
        "host":                 dispositivo["ip"],
        "username":             dispositivo["username"],
        "password":             dispositivo["password"],
        "global_delay_factor":   2,
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
    print("\n Iniciando deploy OSPF...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    resultados = []
    for hostname, datos_ospf in OSPF.items():
        try:
            print(f"  Configurando OSPF en {hostname}...")
            dispositivo = routers[hostname]
            config      = renderizar_template(datos_ospf)
            deploy_ospf(dispositivo, config)
            print(f"  OK {hostname} - Router-ID {datos_ospf['router_id']}")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE OSPF - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
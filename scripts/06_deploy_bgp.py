# ============================================
# Script 06 - Deploy BGP
# Autor: Jose Angel
# Descripcion: Configura BGP entre sitios
# AS 65001=BA, AS 65002=BHA, AS 65003=NQ+NQSUB
# ============================================

import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño BGP por router ------------------
BGP = {
    "BA-R1": {
        "as_local":  65001,
        "router_id": "10.0.0.1",
        "vecinos": [
            {"ip": "10.1.0.2", "as_remoto": 65002, "descripcion": "BHA-R1-PRIMARIO"},
            {"ip": "10.1.1.2", "as_remoto": 65003, "descripcion": "NQ-R1-PRIMARIO"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.0.1",      "mascara": "255.255.255.255"},
        ],
    },
    "BA-R2": {
        "as_local":  65001,
        "router_id": "10.0.0.2",
        "vecinos": [
            {"ip": "10.1.0.6", "as_remoto": 65002, "descripcion": "BHA-R2-SECUNDARIO"},
            {"ip": "10.1.1.6", "as_remoto": 65003, "descripcion": "NQ-R2-SECUNDARIO"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.0.2",      "mascara": "255.255.255.255"},
        ],
    },
    "BHA-R1": {
        "as_local":  65002,
        "router_id": "10.0.1.1",
        "vecinos": [
            {"ip": "10.1.0.1", "as_remoto": 65001, "descripcion": "BA-R1-PRIMARIO"},
            {"ip": "10.1.2.2", "as_remoto": 65003, "descripcion": "NQ-R1-PRIMARIO"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.1.1",      "mascara": "255.255.255.255"},
        ],
    },
    "BHA-R2": {
        "as_local":  65002,
        "router_id": "10.0.1.2",
        "vecinos": [
            {"ip": "10.1.0.5", "as_remoto": 65001, "descripcion": "BA-R2-SECUNDARIO"},
            {"ip": "10.1.2.6", "as_remoto": 65003, "descripcion": "NQ-R2-SECUNDARIO"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.1.2",      "mascara": "255.255.255.255"},
        ],
    },
    "NQ-R1": {
        "as_local":  65003,
        "router_id": "10.0.2.1",
        "vecinos": [
            {"ip": "10.1.1.1", "as_remoto": 65001, "descripcion": "BA-R1-PRIMARIO"},
            {"ip": "10.1.2.1", "as_remoto": 65002, "descripcion": "BHA-R1-PRIMARIO"},
            {"ip": "10.1.3.2", "as_remoto": 65003, "descripcion": "NQSUB-R1-IBGP"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.2.1",      "mascara": "255.255.255.255"},
            {"ip": "10.0.3.1",      "mascara": "255.255.255.255"},
        ],
    },
    "NQ-R2": {
        "as_local":  65003,
        "router_id": "10.0.2.2",
        "vecinos": [
            {"ip": "10.1.1.5", "as_remoto": 65001, "descripcion": "BA-R2-SECUNDARIO"},
            {"ip": "10.1.2.5", "as_remoto": 65002, "descripcion": "BHA-R2-SECUNDARIO"},
            {"ip": "10.1.3.6", "as_remoto": 65003, "descripcion": "NQSUB-R1-IBGP"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.2.2",      "mascara": "255.255.255.255"},
            {"ip": "10.0.3.1",      "mascara": "255.255.255.255"},
        ],
    },
    "NQSUB-R1": {
        "as_local":  65003,
        "router_id": "10.0.3.1",
        "vecinos": [
            {"ip": "10.1.3.1", "as_remoto": 65003, "descripcion": "NQ-R1-IBGP"},
            {"ip": "10.1.3.5", "as_remoto": 65003, "descripcion": "NQ-R2-IBGP"},
        ],
        "redes_bgp": [
            {"ip": "192.168.100.0", "mascara": "255.255.255.0"},
            {"ip": "10.0.3.1",      "mascara": "255.255.255.255"},
        ],
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos_bgp):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("bgp.j2")
    return template.render(**datos_bgp)

# -- Aplicar config -------------------------
def deploy_bgp(dispositivo, config, as_local):
    conexion_params = {
        "device_type":          dispositivo["device_type"],
        "host":                 dispositivo["ip"],
        "username":             dispositivo["username"],
        "password":             dispositivo["password"],
        "global_delay_factor":   2,
        "read_timeout_override": 30,
    }
    conexion = ConnectHandler(**conexion_params)

    # Borrar BGP existente primero
    conexion.send_config_set(
        [f"no router bgp {as_local}"],
        read_timeout=30
    )

    # Aplicar nueva config
    output = conexion.send_config_set(
        config.splitlines(),
        read_timeout=30
    )
    conexion.save_config()
    conexion.disconnect()
    return output

# -- Main -----------------------------------
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n Iniciando deploy BGP...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    resultados = []
    for hostname, datos_bgp in BGP.items():
        try:
            print(f"  Configurando BGP en {hostname} (AS {datos_bgp['as_local']})...")
            dispositivo = routers[hostname]
            config      = renderizar_template(datos_bgp)
            deploy_bgp(dispositivo, config, datos_bgp["as_local"])
            print(f"  OK {hostname} - {len(datos_bgp['vecinos'])} vecinos configurados")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE BGP - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
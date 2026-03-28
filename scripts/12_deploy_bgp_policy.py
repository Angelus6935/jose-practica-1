# ============================================
# Script 12 - Deploy BGP policies
# Autor: Jose Angel
# Descripcion: Configura route-maps BGP
#              R1=primario(200) R2=secundario(100)
# ============================================

import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño de politicas por router ---------
POLITICAS = {
    "BA-R1": {
        "sitio":             "BA",
        "as_local":          65001,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   ["10.1.0.2", "10.1.1.2"],
        "vecinos_secundarios": [],
    },
    "BA-R2": {
        "sitio":             "BA",
        "as_local":          65001,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   [],
        "vecinos_secundarios": ["10.1.0.6", "10.1.1.6"],
    },
    "BHA-R1": {
        "sitio":             "BHA",
        "as_local":          65002,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   ["10.1.0.1", "10.1.2.2"],
        "vecinos_secundarios": [],
    },
    "BHA-R2": {
        "sitio":             "BHA",
        "as_local":          65002,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   [],
        "vecinos_secundarios": ["10.1.0.5", "10.1.2.6"],
    },
    "NQ-R1": {
        "sitio":             "NQ",
        "as_local":          65003,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   ["10.1.1.1", "10.1.2.1"],
        "vecinos_secundarios": [],
    },
    "NQ-R2": {
        "sitio":             "NQ",
        "as_local":          65003,
        "red_lan":           "192.168.100.0/24",
        "vecinos_primarios":   [],
        "vecinos_secundarios": ["10.1.1.5", "10.1.2.5"],
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("bgp_policy.j2")
    return template.render(**datos)

# -- Aplicar config -------------------------
def deploy_policy(dispositivo, config):
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
    print("\n Iniciando deploy BGP policies...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    resultados = []
    for hostname, datos in POLITICAS.items():
        try:
            print(f"  Aplicando politicas en {hostname}...")
            dispositivo = routers[hostname]
            config      = renderizar_template(datos)
            deploy_policy(dispositivo, config)
            rol = "PRIMARIO" if datos["vecinos_primarios"] else "SECUNDARIO"
            print(f"  OK {hostname} → {rol} (LOCAL-PREF {'200' if rol == 'PRIMARIO' else '100'})")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE BGP POLICY - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
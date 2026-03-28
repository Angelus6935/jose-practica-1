# ============================================
# Script 10 - Deploy HSRP
# Autor: Jose Angel
# Descripcion: Configura HSRP en routers
#              para alta disponibilidad L3
# ============================================

import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime

# -- Diseño HSRP por router -----------------
HSRP = {
    "BA-R1": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      110,
        "interfaz_track": "Ethernet0/1",
    },
    "BA-R2": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      100,
        "interfaz_track": "Ethernet0/1",
    },
    "BHA-R1": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      110,
        "interfaz_track": "Ethernet0/1",
    },
    "BHA-R2": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      100,
        "interfaz_track": "Ethernet0/1",
    },
    "NQ-R1": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      110,
        "interfaz_track": "Ethernet0/2",
    },
    "NQ-R2": {
        "interfaz":       "Ethernet0/0",
        "grupo":          1,
        "vip":            "192.168.100.254",
        "prioridad":      100,
        "interfaz_track": "Ethernet0/2",
    },
}

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Renderizar template --------------------
def renderizar_template(datos_hsrp):
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("hsrp.j2")
    return template.render(**datos_hsrp)

# -- Aplicar config -------------------------
def deploy_hsrp(dispositivo, config):
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
    print("\n Iniciando deploy HSRP...")
    print(f"   Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")

    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    resultados = []
    for hostname, datos_hsrp in HSRP.items():
        try:
            print(f"  Configurando HSRP en {hostname}...")
            dispositivo = routers[hostname]
            config      = renderizar_template(datos_hsrp)
            deploy_hsrp(dispositivo, config)
            rol = "ACTIVO" if datos_hsrp["prioridad"] == 110 else "STANDBY"
            print(f"  OK {hostname} → {rol} VIP {datos_hsrp['vip']}")
            resultados.append({"hostname": hostname, "estado": "OK"})
        except Exception as e:
            print(f"  FAIL {hostname} - {str(e)[:50]}")
            resultados.append({"hostname": hostname, "estado": "FAIL", "error": str(e)})

    ok       = [r for r in resultados if r["estado"] == "OK"]
    fail     = [r for r in resultados if r["estado"] == "FAIL"]
    duracion = (datetime.now() - inicio).seconds

    print("\n" + "="*55)
    print(f"  REPORTE HSRP - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    print(f"\n  Total:    {len(resultados)}")
    print(f"  Exitosos: {len(ok)}")
    print(f"  Fallidos: {len(fail)}")
    print(f"  Duracion: {duracion} segundos")
    print("="*55)
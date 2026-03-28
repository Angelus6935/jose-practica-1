# ============================================
# Script 11 - Validacion completa del lab
# Autor: Jose Angel
# Descripcion: Verifica el estado completo
#              de toda la infraestructura
# ============================================

import yaml
import time
from netmiko import ConnectHandler
from datetime import datetime

# -- Cargar inventario ----------------------
def cargar_inventario(ruta):
    with open(ruta, "r") as archivo:
        return yaml.safe_load(archivo)

# -- Conectar router ------------------------
def conectar(dispositivo):
    return ConnectHandler(
        device_type=          dispositivo["device_type"],
        host=                 dispositivo["ip"],
        username=             dispositivo["username"],
        password=             dispositivo["password"],
        global_delay_factor=   2,
        read_timeout_override= 30,
    )

# -- Verificar OSPF -------------------------
def verificar_ospf(dispositivo):
    try:
        conn   = conectar(dispositivo)
        output = conn.send_command("show ip ospf neighbor")
        conn.disconnect()
        vecinos = [l for l in output.splitlines() if "FULL" in l]
        return len(vecinos), vecinos
    except Exception as e:
        return 0, [str(e)]

# -- Verificar BGP --------------------------
def verificar_bgp(dispositivo):
    try:
        conn   = conectar(dispositivo)
        output = conn.send_command("show ip bgp summary")
        conn.disconnect()
        sesiones = []
        for linea in output.splitlines():
            if linea and linea[0].isdigit():
                partes = linea.split()
                if len(partes) >= 9 and ":" in partes[8]:
                    sesiones.append({
                        "vecino": partes[0],
                        "as":     partes[2],
                        "uptime": partes[8],
                        "prefijos": partes[9] if len(partes) > 9 else "0"
                    })
        return len(sesiones), sesiones
    except Exception as e:
        return 0, [str(e)]

# -- Verificar HSRP -------------------------
def verificar_hsrp(dispositivo):
    try:
        conn   = conectar(dispositivo)
        output = conn.send_command("show standby brief")
        conn.disconnect()
        for linea in output.splitlines():
            if "Et0/0" in linea:
                if "Active" in linea:
                    return "ACTIVO"
                elif "Standby" in linea:
                    return "STANDBY"
        return "NO CONFIGURADO"
    except Exception as e:
        return f"ERROR: {str(e)[:30]}"

# -- Verificar ping entre sitios ------------
def verificar_ping(dispositivo, destinos):
    resultados = []
    try:
        conn = conectar(dispositivo)
        for nombre, ip in destinos.items():
            output = conn.send_command(
                f"ping {ip} source Loopback0 repeat 3",
                read_timeout=15
            )
            if "!!!" in output or "Success rate is 100" in output:
                resultados.append({"destino": nombre, "ip": ip, "estado": "OK"})
            else:
                resultados.append({"destino": nombre, "ip": ip, "estado": "FAIL"})
        conn.disconnect()
    except Exception as e:
        resultados.append({"destino": "ERROR", "ip": "", "estado": str(e)[:30]})
    return resultados

# -- Main -----------------------------------
if __name__ == "__main__":
    inicio = datetime.now()
    print("\n" + "="*60)
    print("  VALIDACION COMPLETA — Jose-practica-1")
    print(f"  Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    inventario = cargar_inventario("inventory/devices.yaml")
    routers    = {r["hostname"]: r for r in inventario["routers"]}

    # ── 1. OSPF ──────────────────────────────
    print("\n📡 OSPF NEIGHBORS")
    print("-"*60)
    ospf_routers = ["BA-R1", "BA-R2", "BHA-R1", "BHA-R2", "NQ-R1", "NQ-R2"]
    for hostname in ospf_routers:
        cantidad, vecinos = verificar_ospf(routers[hostname])
        estado = "✅" if cantidad > 0 else "❌"
        print(f"  {estado} {hostname:<12} → {cantidad} vecinos FULL")
        for v in vecinos:
            print(f"       {v.strip()[:60]}")

    # ── 2. BGP ───────────────────────────────
    print("\n🌐 BGP SESSIONS")
    print("-"*60)
    bgp_routers = ["BA-R1", "BA-R2", "BHA-R1", "BHA-R2", "NQ-R1", "NQ-R2"]
    for hostname in bgp_routers:
        cantidad, sesiones = verificar_bgp(routers[hostname])
        estado = "✅" if cantidad > 0 else "❌"
        print(f"  {estado} {hostname:<12} → {cantidad} sesiones activas")
        for s in sesiones:
            print(f"       Vecino {s['vecino']} AS{s['as']} Up:{s['uptime']} Prefijos:{s['prefijos']}")

    # ── 3. HSRP ──────────────────────────────
    print("\n🔄 HSRP STATE")
    print("-"*60)
    hsrp_routers = ["BA-R1", "BA-R2", "BHA-R1", "BHA-R2", "NQ-R1", "NQ-R2"]
    for hostname in hsrp_routers:
        estado_hsrp = verificar_hsrp(routers[hostname])
        if estado_hsrp == "ACTIVO":
            icono = "✅"
        elif estado_hsrp == "STANDBY":
            icono = "✅"
        else:
            icono = "❌"
        print(f"  {icono} {hostname:<12} → {estado_hsrp}")

    # ── 4. PING entre sitios ─────────────────
    print("\n🏓 PING ENTRE SITIOS (desde BA-R1)")
    print("-"*60)
    destinos = {
        "BA-R2    ": "10.0.0.2",
        "BHA-R1   ": "10.0.1.1",
        "BHA-R2   ": "10.0.1.2",
        "NQ-R1    ": "10.0.2.1",
        "NQ-R2    ": "10.0.2.2",
        "NQSUB-R1 ": "10.0.3.1",
    }
    pings = verificar_ping(routers["BA-R1"], destinos)
    for p in pings:
        icono = "✅" if p["estado"] == "OK" else "❌"
        print(f"  {icono} BA-R1 → {p['destino']} ({p['ip']}) {p['estado']}")

    # ── 5. Reporte final ─────────────────────
    duracion = (datetime.now() - inicio).seconds
    print("\n" + "="*60)
    print(f"  VALIDACION COMPLETADA en {duracion} segundos")
    print("="*60)
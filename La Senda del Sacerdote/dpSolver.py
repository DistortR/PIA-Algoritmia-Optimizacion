"""
dpSolver.py — Programación Dinámica (A* Pruning)
Juego: La Senda del Sacerdote
"""
import time
import copy
import sys
import logic

INF = float("inf")
_memo = {}

def estado(senda) -> tuple:
    return tuple(c["id"] for c in senda)

def generar_acciones(senda) -> list:
    acc = []
    for i, c in enumerate(senda):
        if c.get("subclase") != "MAESTRO" or c.get("es_fijo"): continue
        info = logic.HABILIDADES_INFO.get(c["id"])
        if not info: continue
        cid, t = c["id"], info["tipo"]
        
        if t == "simple":
            if info.get("opciones"):
                for j, txt in enumerate(info["opciones"]): acc.append((i, [j], f"{cid}[{txt}]"))
            else:
                acc.append((i, [0], f"{cid}[auto]"))
        elif t == "direccion":
            for d, txt in info["direcciones"]: acc.append((i, [d], f"{cid}[{txt}]"))
        elif t == "distancia_direccion":
            for ds in info["distancias"]:
                for d, txt in info["direcciones"]: acc.append((i, [ds, d], f"{cid}[dist={ds},{txt}]"))
        elif t == "doble_seleccion":
            for j, o1 in enumerate(info["opciones1"]):
                for d, txt in info["direcciones"]: acc.append((i, [j, d], f"{cid}[{o1},{txt}]"))
    return acc

def dp(s: tuple, k: int) -> tuple:
    key = (s, k)
    if key in _memo: return _memo[key]

    senda = [copy.deepcopy(logic.CARTAS_POR_ID[cid]) for cid in s]
    fin, _ = logic.verificar_fin_juego(senda)
    if fin == "victoria":
        _memo[key] = (0, None); return (0, None)
    if fin == "derrota":
        _memo[key] = (INF, None); return (INF, None)
    if k == 0:
        _memo[key] = (INF, None); return (INF, None)

    # ── PODA HEURÍSTICA (A* Pruning) ──
    ia = next((i for i,c in enumerate(senda) if c["id"]=="aprendiz"), None)
    ih = next((i for i,c in enumerate(senda) if c["id"]=="ah_puch"), None)
    if ia is not None and ih is not None:
        distancia = abs(ih - ia) - 1
        if (distancia // 3) > k:
            _memo[key] = (INF, None); return (INF, None)
    # ──────────────────────────────────

    mejor_costo = INF
    mejor_accion = None

    for idx, vals, desc in generar_acciones(senda):
        nueva_senda, resultado = logic.simular_turno_completo(senda, idx, vals)
        if nueva_senda is None: continue

        if resultado == "victoria":
            mejor_costo = 1
            mejor_accion = desc
            break
        if resultado == "derrota": continue

        sub_costo, _ = dp(estado(nueva_senda), k - 1)
        costo_total = 1 + sub_costo

        if costo_total < mejor_costo:
            mejor_costo = costo_total
            mejor_accion = desc

    _memo[key] = (mejor_costo, mejor_accion)
    return (mejor_costo, mejor_accion)

def obtener_movimiento_optimo(senda_lista, max_k=8):
    if not logic.CARTAS_POR_ID: logic.cargar_datos()
    _memo.clear()
    s_tuple = estado(senda_lista)
    
    for k in range(1, max_k + 1):
        costo, accion_desc = dp(s_tuple, k)
        if costo < INF and accion_desc is not None:
            for idx, vals, desc in generar_acciones(senda_lista):
                if desc == accion_desc:
                    return idx, vals, accion_desc
    return None, None, None

def resolver(senda_inicial, max_k=8):
    if not logic.CARTAS_POR_ID: logic.cargar_datos()
    _memo.clear()
    for k in range(1, max_k + 1):
        print(f"Probando con k={k}…", end=" ", flush=True)
        t0 = time.time()
        costo, _ = dp(estado(senda_inicial), k)
        print(f"|  tiempo: {time.time() - t0:.3f}s")
        if costo < INF:
            print(f"\n¡Solución encontrada en {costo} turnos con k={k}!")
            return costo
    print(f"\nSin solución en {max_k} turnos.")
    return INF

if __name__ == "__main__":
    sys.setrecursionlimit(100_000)
    logic.cargar_datos()
    senda = logic.cargar_senda_inicial()
    resolver(senda, max_k=8)
"""
senda_solver.py  —  Programación Dinámica  (top-down con memoización)
======================================================================
Juego: La Senda del Sacerdote
"""

import copy, json, sys, time

# ─────────────────────────────────────────────────────────────
#  CARGA DE DATOS
# ─────────────────────────────────────────────────────────────

_cartas_por_id: dict = {}

def _init_cartas(ruta: str = "cartas.json"):
    global _cartas_por_id
    with open(ruta) as f:
        data = json.load(f)
    _cartas_por_id = {c["id"]: c for c in data["cartas"]}

def cargar_senda_inicial(ruta: str = "cartas.json", seed: int = None) -> list:
    import random
    if seed is not None: random.seed(seed)
    with open(ruta) as f:
        data = json.load(f)
    todas    = data["cartas"]
    aprendiz = next(c for c in todas if c["id"] == "aprendiz")
    ah_puch  = next(c for c in todas if c["id"] == "ah_puch")
    mezclables = [c for c in todas if not c["es_fijo"]]
    random.shuffle(mezclables)
    return ([copy.deepcopy(aprendiz)]
            + [copy.deepcopy(c) for c in mezclables]
            + [copy.deepcopy(ah_puch)])

def senda_desde_ids(ids: list, ruta: str = "cartas.json") -> list:
    with open(ruta) as f:
        data = json.load(f)
    por_id = {c["id"]: c for c in data["cartas"]}
    return [copy.deepcopy(por_id[i]) for i in ids]

def _estado_a_senda(t: tuple) -> list:
    return [copy.deepcopy(_cartas_por_id[cid]) for cid in t]

# ─────────────────────────────────────────────────────────────
#  LÓGICA PURA DEL JUEGO (AH PUCH INMUTABLE)
# ─────────────────────────────────────────────────────────────

def _ady_mas_bajo(s, i):
    c = []
    if i > 0:          c.append((i-1, s[i-1]["numero"]))
    if i < len(s)-1:   c.append((i+1, s[i+1]["numero"]))
    return min(c, key=lambda x:(x[1],x[0]))[0] if c else None

def _mv(s, f, t):
    if f==t: return s
    if s[f]["id"] == "ah_puch": return s
    c = s.pop(f)
    if t > f: t -= 1
    if t >= len(s): t = len(s) - 1
    s.insert(t, c); return s

def _sw(s, i, j): 
    if s[i]["id"] == "ah_puch" or s[j]["id"] == "ah_puch": return s
    s[i], s[j] = s[j], s[i]; return s

def _del(s, i):   
    if s[i]["id"] == "ah_puch": return s
    s.pop(i); return s

def h_duda(s,i,op,_):
    if i==0 or i==len(s)-1:
        _mv(s,i,i+1 if i==0 else i-1)
    elif op==0: _sw(s,i-1,i+1)
    else:       _mv(s,i,i-1)
    return s

def h_rencor(s,i,_,__):
    o=_ady_mas_bajo(s,i)
    if o is not None: _del(s,o)
    return s

def h_miedo(s,i,_,__):
    o=_ady_mas_bajo(s,i)
    if o is not None:
        if s[o]["id"] == "ah_puch": return s
        c=s.pop(o); s.insert(1 if len(s)>1 else 0,c)
    return s

def h_pereza(s,i,op,_):
    o=_ady_mas_bajo(s,i)
    if o is None: return s
    if op==0:
        np=max(0,o-2)
        if np!=o: return _mv(s,o,np)
    _mv(s,i,i+1 if i<len(s)-1 else i-1); return s

def h_ejercicio(s,i,dist,d,_):
    o=i+d*dist
    if 0<=o<len(s): _sw(s,i,o)
    return s

def h_cizanyoso(s,i,op,_):
    try: ir=next(j for j,c in enumerate(s) if c["id"]=="rencor")
    except StopIteration: return s
    o=_ady_mas_bajo(s,i)
    if o is None: return s
    if s[o]["id"]=="rencor":
        d=-1 if ir>0 else 1; _mv(s,ir,max(0,min(len(s)-1,ir+d*2)))
    elif op==0:
        d=1 if ir>o else -1; _mv(s,o,max(0,min(len(s)-1,ir-d)))
    else:
        d=-1 if ir>0 else 1; _mv(s,ir,max(0,min(len(s)-1,ir+d*2)))
    return s

def h_filosofia(s,i,dist,d,_):
    o=i+d*dist
    if not(0<=o<len(s)): return s
    np=max(0,min(len(s)-1,o+d*(4-dist)))
    if np!=o: _mv(s,o,np)
    return s

def h_herbolaria(s,i,cual,d,_):
    a=i+d
    if not(0<=a<len(s)): return s
    np=(max(0,a-2) if cual==0 else min(len(s)-1,a+1))
    if np!=a: _mv(s,a,np)
    return s

def h_meditacion(s,i,d,_):
    o=i+d*3
    if 0<=o<len(s): _sw(s,i,o)
    return s

def h_oracion(s,i,d,_):
    o=i+d
    if 0<=o<len(s): _sw(s,i,o)
    return s

def h_envidia(s,i,op,_):
    try: ir=next(j for j,c in enumerate(s) if c["id"]=="rencor")
    except StopIteration: return s
    o=_ady_mas_bajo(s,i)
    if o is None: return s
    if s[o]["id"]=="rencor":
        d=-1 if ir>0 else 1; _mv(s,ir,max(0,min(len(s)-1,ir+d*2)))
    elif op==0:
        d=1 if ir>o else -1; _mv(s,o,max(0,min(len(s)-1,o+d*2)))
    else:
        d=-1 if ir>0 else 1; _mv(s,ir,max(0,min(len(s)-1,ir+d*2)))
    return s

def h_peregrino(s,i,d,_):
    a=i+d
    if not(0<=a<len(s)): return s
    np=min(len(s)-1,a+2)
    if np!=a: _mv(s,a,np)
    return s

def h_magia(s,i,cual,d,_):
    a=i+d
    if not(0<=a<len(s)): return s
    np=(max(0,a-3) if cual==0 else min(len(s)-1,a+2))
    if np!=a: _mv(s,a,np)
    return s

def h_cuerpo_astral(s,i,d,_):
    o=i+d*4
    if 0<=o<len(s): _sw(s,i,o)
    return s

HABILIDADES = {
    "duda":          {"f":h_duda,          "tipo":"simple",   "opts":["Intercambiar adyacentes","Mover 1 espacio"]},
    "rencor":        {"f":h_rencor,        "tipo":"simple",   "opts":[]},
    "miedo":         {"f":h_miedo,         "tipo":"simple",   "opts":[]},
    "pereza":        {"f":h_pereza,        "tipo":"simple",   "opts":["Retroceder adyacente 2","Avanzar 1"]},
    "ejercicio":     {"f":h_ejercicio,     "tipo":"dist_dir", "dists":[1,2],   "dirs":[(-1,"Izq"),(1,"Der")]},
    "cizanoso":      {"f":h_cizanyoso,     "tipo":"simple",   "opts":["Mover ante Rencor","Rencor→Aprendiz"]},
    "filosofia":     {"f":h_filosofia,     "tipo":"dist_dir", "dists":[1,2,3], "dirs":[(-1,"Izq"),(1,"Der")]},
    "herbolaria":    {"f":h_herbolaria,    "tipo":"doble",    "opts1":["Retroceder 2","Adelantar 1"], "dirs":[(-1,"Izq"),(1,"Der")]},
    "meditacion":    {"f":h_meditacion,    "tipo":"dir",      "dirs":[(-1,"Izq"),(1,"Der")]},
    "oracion":       {"f":h_oracion,       "tipo":"dir",      "dirs":[(-1,"Izq"),(1,"Der")]},
    "envidia":       {"f":h_envidia,       "tipo":"simple",   "opts":["Mover adyacente→Rencor","Rencor→Aprendiz"]},
    "peregrino":     {"f":h_peregrino,     "tipo":"dir",      "dirs":[(-1,"Izq"),(1,"Der")]},
    "magia":         {"f":h_magia,         "tipo":"doble",    "opts1":["Retroceder 3","Adelantar 2"], "dirs":[(-1,"Izq"),(1,"Der")]},
    "cuerpo_astral": {"f":h_cuerpo_astral, "tipo":"dir",      "dirs":[(-1,"Izq"),(1,"Der")]},
}

def estado(senda) -> tuple:
    return tuple(c["id"] for c in senda)

def verificar_fin(senda):
    ia = next((i for i,c in enumerate(senda) if c["id"]=="aprendiz"), None)
    ih = next((i for i,c in enumerate(senda) if c["id"]=="ah_puch"),  None)
    if ia is None: return "derrota"
    if ih is None: return "victoria"
    if ia == ih-1: return "victoria"
    return None

def ejecutar_habilidad(senda, idx, vals):
    c = senda[idx]
    if c.get("es_fijo") or c["id"] not in HABILIDADES:
        return senda, False
    info = HABILIDADES[c["id"]]
    nueva = copy.deepcopy(senda)
    try:
        t = info["tipo"]
        f = info["f"]
        if   t=="simple":   f(nueva, idx, vals[0] if vals else 0, None)
        elif t=="dir":      f(nueva, idx, vals[0], None)
        elif t=="dist_dir": f(nueva, idx, vals[0], vals[1], None)
        elif t=="doble":    f(nueva, idx, vals[0], vals[1], None)
    except:
        return senda, False
    return nueva, True

def generar_acciones(senda) -> list:
    acc = []
    for i,c in enumerate(senda):
        if c.get("subclase")!="MAESTRO" or c.get("es_fijo"): continue
        info = HABILIDADES.get(c["id"])
        if not info: continue
        cid, t = c["id"], info["tipo"]
        if t=="simple":
            if info["opts"]:
                for j,txt in enumerate(info["opts"]): acc.append((i,[j],f"{cid}[{txt}]"))
            else:
                acc.append((i,[0],f"{cid}[auto]"))
        elif t=="dir":
            for d,txt in info["dirs"]: acc.append((i,[d],f"{cid}[{txt}]"))
        elif t=="dist_dir":
            for ds in info["dists"]:
                for d,txt in info["dirs"]: acc.append((i,[ds,d],f"{cid}[dist={ds},{txt}]"))
        elif t=="doble":
            for j,o1 in enumerate(info["opts1"]):
                for d,txt in info["dirs"]: acc.append((i,[j,d],f"{cid}[{o1},{txt}]"))
    return acc

def aplicar_falsos(senda):
    falsos = sorted(
        [(c["id"],c["numero"]) for c in senda
         if c.get("subclase")=="FALSO MAESTRO" and not c.get("es_fijo")],
        key=lambda x: x[1]
    )
    for cid,_ in falsos:
        idx = next((i for i,c in enumerate(senda) if c["id"]==cid), None)
        if idx is None: continue
        nueva, ok = ejecutar_habilidad(senda, idx, [0])
        if ok: senda = nueva
        r = verificar_fin(senda)
        if r: return senda, r
    return senda, None

def paso_completo(senda, idx, vals):
    nueva, ok = ejecutar_habilidad(senda, idx, vals)
    if not ok: return None, None
    r = verificar_fin(nueva)
    if r: return nueva, r
    nueva, r = aplicar_falsos(nueva)
    return nueva, r

# ─────────────────────────────────────────────────────────────
#  PROGRAMACIÓN DINÁMICA
# ─────────────────────────────────────────────────────────────

INF  = float("inf")
_memo: dict = {}

def dp(s: tuple, k: int) -> tuple:
    key = (s, k)
    if key in _memo: return _memo[key]

    senda = _estado_a_senda(s)
    fin = verificar_fin(senda)
    if fin == "victoria":
        _memo[key] = (0, None); return (0, None)
    if fin == "derrota":
        _memo[key] = (INF, None); return (INF, None)
    if k == 0:
        _memo[key] = (INF, None); return (INF, None)

    mejor_costo  = INF
    mejor_accion = None

    for idx, vals, desc in generar_acciones(senda):
        nueva_senda, resultado = paso_completo(senda, idx, vals)
        if nueva_senda is None: continue

        if resultado == "victoria":
            mejor_costo  = 1
            mejor_accion = desc
            break

        if resultado == "derrota":
            continue

        sub_costo, _ = dp(estado(nueva_senda), k - 1)
        costo_total  = 1 + sub_costo

        if costo_total < mejor_costo:
            mejor_costo  = costo_total
            mejor_accion = desc

    _memo[key] = (mejor_costo, mejor_accion)
    return (mejor_costo, mejor_accion)

def resolver(senda_inicial: list, max_k: int = 8) -> tuple:
    _memo.clear()
    for k in range(1, max_k + 1):
        print(f"  Probando con k={k}…", end=" ", flush=True)
        t0 = time.time()
        costo, _ = dp(estado(senda_inicial), k)
        elapsed  = time.time() - t0
        print(f"subproblemas en memo: {len(_memo):,}  |  tiempo: {elapsed:.3f}s")
        if costo < INF:
            print(f"\n  ✓ Solución óptima encontrada: {costo} turno(s) con k={k}")
            camino = _reconstruir(senda_inicial, k)
            return costo, camino

    print(f"\n  Sin solución en {max_k} turnos.")
    return INF, None

def _reconstruir(senda_inicial: list, k: int) -> list:
    senda  = copy.deepcopy(senda_inicial)
    camino = []
    for turno in range(k):
        s      = estado(senda)
        fin    = verificar_fin(senda)
        if fin == "victoria": break
        if fin == "derrota":  return None
        turnos_restantes = k - turno
        costo, accion = _memo.get((s, turnos_restantes), (INF, None))
        if accion is None and costo == INF: return None
        for idx, vals, desc in generar_acciones(senda):
            if desc == accion:
                nueva, resultado = paso_completo(senda, idx, vals)
                senda = nueva
                camino.append(accion)
                if resultado == "victoria": return camino
                break
    return camino

def mostrar_senda(senda, titulo=""):
    if titulo: print(f"\n{'─'*54}\n  {titulo}\n{'─'*54}")
    ia  = next((i for i,c in enumerate(senda) if c["id"]=="aprendiz"), None)
    ih  = next((i for i,c in enumerate(senda) if c["id"]=="ah_puch"),  None)
    gap = (ih-ia-1) if ia is not None and ih is not None else "?"
    print("  " + " → ".join(f"[{c['id']}]" for c in senda))
    print(f"  Aprendiz pos={ia}  AhPuch pos={ih}  gap={gap}")

def simular(senda_inicial, camino):
    senda = copy.deepcopy(senda_inicial)
    print("\n" + "═"*54 + "\n  SIMULACIÓN DE LA SOLUCIÓN\n" + "═"*54)
    mostrar_senda(senda, "Estado inicial")
    for turno, desc in enumerate(camino, 1):
        for idx, vals, d in generar_acciones(senda):
            if d == desc:
                nueva, resultado = paso_completo(senda, idx, vals)
                senda = nueva
                mostrar_senda(senda, f"Turno {turno}: {desc}")
                if resultado == "victoria": print("  ✓ ¡VICTORIA!")
                elif resultado == "derrota": print("  ✗ DERROTA")
                break
    print("═"*54)

# ─────────────────────────────────────────────────────────────
#  API PARA PYGAME (AUTO-PLAY)
# ─────────────────────────────────────────────────────────────

def obtener_movimiento_optimo(senda_lista, max_k=8):
    global _cartas_por_id
    if not _cartas_por_id:
        try:
            _init_cartas("La Senda del Sacerdote/cartas.json")
        except FileNotFoundError:
            _init_cartas("cartas.json")
            
    _memo.clear()
    s_tuple = estado(senda_lista)
    
    for k in range(1, max_k + 1):
        costo, accion_desc = dp(s_tuple, k)
        if costo < INF and accion_desc is not None:
            for idx, vals, desc in generar_acciones(senda_lista):
                if desc == accion_desc:
                    return idx, vals, accion_desc
    return None, None, None

if __name__ == "__main__":
    sys.setrecursionlimit(100_000)
    # Se eliminó la semilla (seed) fija para que cada ejecución sea aleatoria
    try:
        _init_cartas("La Senda del Sacerdote/cartas.json")
        senda = cargar_senda_inicial("La Senda del Sacerdote/cartas.json")
    except FileNotFoundError:
        _init_cartas("cartas.json")
        senda = cargar_senda_inicial("cartas.json")

    mostrar_senda(senda, "Senda inicial")
    print(f"\nResolviendo con Programación Dinámica  dp(estado, k)…\n")
    costo, camino = resolver(senda, max_k=8)

    if camino:
        print("\nSecuencia óptima de acciones:")
        for i, a in enumerate(camino, 1):
            print(f"  {i}. {a}")
        simular(senda, camino)
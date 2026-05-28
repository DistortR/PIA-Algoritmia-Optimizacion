import json
import random
import copy

CARTAS_POR_ID = {}

def cargar_datos(ruta="La Senda del Sacerdote/cartas.json"):
    global CARTAS_POR_ID
    try:
        with open(ruta) as f:
            data = json.load(f)
    except FileNotFoundError:
        with open("cartas.json") as f:
            data = json.load(f)
            
    CARTAS_POR_ID = {c["id"]: c for c in data["cartas"]}
    return data

def cargar_senda_inicial():
    data = cargar_datos()
    todas = data["cartas"]
    aprendiz = next(c for c in todas if c["id"] == "aprendiz")
    ah_puch = next(c for c in todas if c["id"] == "ah_puch")
    mezclables = [c for c in todas if not c["es_fijo"]]
    random.shuffle(mezclables)
    return ([copy.deepcopy(aprendiz)] + 
            [copy.deepcopy(c) for c in mezclables] + 
            [copy.deepcopy(ah_puch)])

# -------------------- PRIMITIVAS Y REGLAS --------------------
def obtener_adyacente_mas_bajo(senda, idx):
    izquierda = idx - 1 if idx > 0 else None
    derecha = idx + 1 if idx < len(senda)-1 else None
    candidatos = []
    if izquierda is not None:
        candidatos.append((izquierda, senda[izquierda]['numero']))
    if derecha is not None:
        candidatos.append((derecha, senda[derecha]['numero']))
    if not candidatos: return None
    candidatos.sort(key=lambda x: (x[1], x[0]))
    return candidatos[0][0]

def mover_carta(senda, from_idx, to_idx):
    if from_idx == to_idx: return senda
    if senda[from_idx]["id"] == "ah_puch": return senda
    carta = senda.pop(from_idx)
    if to_idx > from_idx: to_idx -= 1
    if to_idx >= len(senda): to_idx = len(senda) - 1
    senda.insert(to_idx, carta)
    return senda

def intercambiar_cartas(senda, i, j):
    if senda[i]["id"] == "ah_puch" or senda[j]["id"] == "ah_puch": return senda
    senda[i], senda[j] = senda[j], senda[i]
    return senda

def destruir_carta(senda, idx, mensajes):
    if senda[idx]["id"] == "ah_puch": return senda
    carta = senda.pop(idx)
    mensajes.append(f"{carta['nombre']} ha sido destruida")
    return senda

def verificar_fin_juego(senda):
    idx_aprendiz = next((i for i,c in enumerate(senda) if c["id"]=="aprendiz"), None)
    idx_ahpuch = next((i for i,c in enumerate(senda) if c["id"]=="ah_puch"), None)
    if idx_aprendiz is None: return "derrota", "El Aprendiz ha sido destruido"
    if idx_ahpuch is None: return "victoria", "Ah Puch ha sido destruido"
    if idx_aprendiz == idx_ahpuch - 1: return "victoria", "El Aprendiz ha llegado a la meta"
    return None, None

def obtener_falsos_ordenados(senda):
    falsos = [(c["id"], c["numero"]) for c in senda if c.get("subclase") == "FALSO MAESTRO" and not c["es_fijo"]]
    falsos.sort(key=lambda x: x[1])
    return falsos

# -------------------- HABILIDADES --------------------
def habilidad_duda(senda, idx, opcion, mensajes):
    if idx == 0 or idx == len(senda)-1:
        mover_carta(senda, idx, idx+1 if idx == 0 else idx-1)
        mensajes.append("Duda se mueve a la orilla")
    elif opcion == 0:
        intercambiar_cartas(senda, idx-1, idx+1)
        mensajes.append("Duda intercambia adyacentes")
    else:
        mover_carta(senda, idx, idx-1)
        mensajes.append("Duda se mueve a la izquierda")
    return senda

def habilidad_rencor(senda, idx, _, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is not None: senda = destruir_carta(senda, objetivo, mensajes)
    return senda

def habilidad_miedo(senda, idx, _, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is not None:
        if senda[objetivo]["id"] == "ah_puch": return senda
        carta = senda.pop(objetivo)
        senda.insert(1 if len(senda) > 1 else 0, carta)
        mensajes.append(f"{carta['nombre']} al inicio")
    return senda

def habilidad_pereza(senda, idx, opcion, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is None: return senda
    if opcion == 0:
        nueva_pos = max(0, objetivo - 2)
        if nueva_pos != objetivo: mover_carta(senda, objetivo, nueva_pos)
        else: mover_carta(senda, idx, idx + 1 if idx < len(senda)-1 else idx-1)
    else:
        mover_carta(senda, idx, idx + 1 if idx < len(senda)-1 else idx-1)
    return senda

def habilidad_ejercicio(senda, idx, dist, dir, mensajes):
    otro = idx + dir * dist
    if 0 <= otro < len(senda): intercambiar_cartas(senda, idx, otro)
    return senda

def habilidad_cizanyoso(senda, idx, opcion, mensajes):
    try: idx_rencor = next(i for i, c in enumerate(senda) if c["id"] == "rencor")
    except StopIteration: return senda
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is None: return senda
    
    if senda[objetivo]["id"] == "rencor":
        direccion = -1 if idx_rencor > 0 else 1
        mover_carta(senda, idx_rencor, max(0, min(len(senda)-1, idx_rencor + direccion * 2)))
    elif opcion == 0:
        direccion = 1 if idx_rencor > objetivo else -1
        mover_carta(senda, objetivo, max(0, min(len(senda)-1, idx_rencor - direccion)))
    else:
        direccion = -1 if idx_rencor > 0 else 1
        mover_carta(senda, idx_rencor, max(0, min(len(senda)-1, idx_rencor + direccion * 2)))
    return senda

def habilidad_filosofia(senda, idx, dist, dir, mensajes):
    otro = idx + dir * dist
    if 0 <= otro < len(senda):
        mover_carta(senda, otro, max(0, min(len(senda)-1, otro + dir * (4 - dist))))
    return senda

def habilidad_herbolaria(senda, idx, cual, dir, mensajes):
    ady = idx + dir
    if 0 <= ady < len(senda):
        mover_carta(senda, ady, max(0, ady - 2) if cual == 0 else min(len(senda)-1, ady + 1))
    return senda

def habilidad_meditacion(senda, idx, dir, mensajes):
    grid = idx + dir * 3
    if 0 <= grid < len(senda): intercambiar_cartas(senda, idx, grid)
    return senda

def habilidad_oracion(senda, idx, dir, mensajes):
    otro = idx + dir
    if 0 <= otro < len(senda): intercambiar_cartas(senda, idx, otro)
    return senda

def habilidad_envidia(senda, idx, opcion, mensajes):
    try: idx_rencor = next(i for i, c in enumerate(senda) if c["id"] == "rencor")
    except StopIteration: return senda
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is None: return senda
    
    if senda[objetivo]["id"] == "rencor":
        direccion = -1 if idx_rencor > 0 else 1
        mover_carta(senda, idx_rencor, max(0, min(len(senda)-1, idx_rencor + direccion * 2)))
    elif opcion == 0:
        direccion = 1 if idx_rencor > objetivo else -1
        mover_carta(senda, objetivo, max(0, min(len(senda)-1, objetivo + direccion * 2)))
    else:
        direccion = -1 if idx_rencor > 0 else 1
        mover_carta(senda, idx_rencor, max(0, min(len(senda)-1, idx_rencor + direccion * 2)))
    return senda

def habilidad_peregrino(senda, idx, dir, mensajes):
    ady = idx + dir
    if 0 <= ady < len(senda): mover_carta(senda, ady, min(len(senda)-1, ady + 2))
    return senda

def habilidad_magia(senda, idx, cual, dir, mensajes):
    ady = idx + dir
    if 0 <= ady < len(senda):
        mover_carta(senda, ady, max(0, ady - 3) if cual == 0 else min(len(senda)-1, ady + 2))
    return senda

def habilidad_cuerpo_astral(senda, idx, dir, mensajes):
    otro = idx + dir * 4
    if 0 <= otro < len(senda): intercambiar_cartas(senda, idx, otro)
    return senda

HABILIDADES_INFO = {
    "duda": {"func": habilidad_duda, "opciones": ["Intercambiar adyacentes", "Mover esta carta 1 espacio"], "tipo": "simple"},
    "rencor": {"func": habilidad_rencor, "opciones": [], "tipo": "simple"},
    "miedo": {"func": habilidad_miedo, "opciones": [], "tipo": "simple"},
    "pereza": {"func": habilidad_pereza, "opciones": ["Retroceder adyacente bajo 2", "Avanza esta carta 1"], "tipo": "simple"},
    "ejercicio": {"func": habilidad_ejercicio, "tipo": "distancia_direccion", "distancias": [1, 2], "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "cizanoso": {"func": habilidad_cizanyoso, "opciones": ["Mover adyacente antes de Rencor", "Mover Rencor hacia Aprendiz"], "tipo": "simple"},
    "filosofia": {"func": habilidad_filosofia, "tipo": "distancia_direccion", "distancias": [1, 2, 3], "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "herbolaria": {"func": habilidad_herbolaria, "tipo": "doble_seleccion", "opciones1": ["Retroceder 2", "Adelantar 1"], "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "meditacion": {"func": habilidad_meditacion, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "oracion": {"func": habilidad_oracion, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "envidia": {"func": habilidad_envidia, "opciones": ["Mover adyacente hacia Rencor", "Mover Rencor hacia Aprendiz"], "tipo": "simple"},
    "peregrino": {"func": habilidad_peregrino, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "magia": {"func": habilidad_magia, "tipo": "doble_seleccion", "opciones1": ["Retroceder 3", "Adelantar 2"], "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "cuerpo_astral": {"func": habilidad_cuerpo_astral, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]}
}

def ejecutar_habilidad(senda, idx, opcion_valores):
    carta = senda[idx]
    if carta["es_fijo"] or carta["id"] not in HABILIDADES_INFO:
        return senda, "No se puede activar", False
    info = HABILIDADES_INFO[carta["id"]]
    mensajes = []
    nueva_senda = copy.deepcopy(senda)
    func = info["func"]
    try:
        if info["tipo"] == "simple":
            param = opcion_valores[0] if opcion_valores else 0
            nueva_senda = func(nueva_senda, idx, param, mensajes)
        elif info["tipo"] == "direccion":
            nueva_senda = func(nueva_senda, idx, opcion_valores[0], mensajes)
        elif info["tipo"] == "distancia_direccion":
            nueva_senda = func(nueva_senda, idx, opcion_valores[0], opcion_valores[1], mensajes)
        elif info["tipo"] == "doble_seleccion":
            nueva_senda = func(nueva_senda, idx, opcion_valores[0], opcion_valores[1], mensajes)
    except Exception as e:
        return senda, f"Error: {e}", False
        
    msg_final = " | ".join(mensajes) if mensajes else "Habilidad ejecutada"
    return nueva_senda, msg_final, True

def simular_turno_completo(senda, idx, vals):
    nueva, _, exito = ejecutar_habilidad(senda, idx, vals)
    if not exito: return None, None
    res, _ = verificar_fin_juego(nueva)
    if res: return nueva, res

    falsos = obtener_falsos_ordenados(nueva)
    for fid, fnum in falsos:
        fidx = next((i for i,c in enumerate(nueva) if c["id"]==fid and c["numero"]==fnum), None)
        if fidx is None: continue
        nueva, _, ok = ejecutar_habilidad(nueva, fidx, [0])
        res, _ = verificar_fin_juego(nueva)
        if res: return nueva, res
        
    return nueva, None
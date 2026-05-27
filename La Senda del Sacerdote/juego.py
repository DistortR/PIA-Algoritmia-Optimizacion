import pygame
import json
import random
import copy

# -------------------- CARGAR DATOS --------------------
def cargar_datos():
    with open("La Senda del Sacerdote/cartas.json") as f:
        data = json.load(f)
    return data

def reiniciar_juego():
    global senda, turno_maestro, falsos_pendientes, victoria, game_over
    global ULTIMA_ACCION, MENSAJE_TEMPORAL, esperando_opcion, seleccion_pendiente
    data = cargar_datos()
    todas = data["cartas"]
    aprendiz = next(c for c in todas if c["id"] == "aprendiz")
    ah_puch = next(c for c in todas if c["id"] == "ah_puch")
    mezclables = [c for c in todas if not c["es_fijo"]]
    random.shuffle(mezclables)
    senda = [copy.deepcopy(aprendiz)] + [copy.deepcopy(c) for c in mezclables] + [copy.deepcopy(ah_puch)]
    for carta in senda:
        carta["selected"] = False
    turno_maestro = True
    falsos_pendientes = []
    victoria = False
    game_over = False
    ULTIMA_ACCION = ""
    MENSAJE_TEMPORAL = ""
    esperando_opcion = False
    seleccion_pendiente = None

# -------------------- INICIALIZAR PYGAME --------------------
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
clock = pygame.time.Clock()

font_nombre    = pygame.font.SysFont("arial", 16, bold=True)
font_subclass  = pygame.font.SysFont("arial", 12)
font_habilidad = pygame.font.SysFont("arial", 15)
font_mensaje   = pygame.font.SysFont("arial", 18, bold=True)
font_turno     = pygame.font.SysFont("arial", 24, bold=True)
font_fin       = pygame.font.SysFont("arial", 32, bold=True)  # fuente más grande para fin del juego

CARD_W, CARD_H = 130, 190
GAP = 15
CARDS_PER_ROW = 8
PANEL_H = 140
PANEL_MARGIN = 20

COLOR_HOVER    = (255, 255, 180)
COLOR_SELECTED = (100, 200, 255)
COLOR_BORDER   = (50, 50, 50)

MENSAJE_TEMPORAL = ""
TIEMPO_MENSAJE = 0
ULTIMA_ACCION = ""

turno_maestro = True
falsos_pendientes = []
esperando_opcion = False
seleccion_pendiente = None
opcion_rects = []
boton_siguiente_rect = None

# -------------------- FUNCIONES AUXILIARES --------------------
def obtener_adyacente_mas_bajo(senda, idx):
    izquierda = idx - 1 if idx > 0 else None
    derecha = idx + 1 if idx < len(senda)-1 else None
    candidatos = []
    if izquierda is not None:
        candidatos.append((izquierda, senda[izquierda]['numero']))
    if derecha is not None:
        candidatos.append((derecha, senda[derecha]['numero']))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: (x[1], x[0]))
    return candidatos[0][0]

def mover_carta(senda, from_idx, to_idx):
    if from_idx == to_idx:
        return senda
    carta = senda.pop(from_idx)
    if to_idx > from_idx:
        to_idx -= 1
    senda.insert(to_idx, carta)
    return senda

def intercambiar_cartas(senda, i, j):
    senda[i], senda[j] = senda[j], senda[i]
    return senda

def destruir_carta(senda, idx, mensajes):
    carta = senda.pop(idx)
    mensajes.append(f"{carta['nombre']} ha sido destruida")
    return senda

# -------------------- HABILIDADES --------------------
def habilidad_duda(senda, idx, opcion, mensajes):
    if idx == 0 or idx == len(senda)-1:
        if idx == 0:
            mover_carta(senda, idx, idx+1)
            mensajes.append("Duda se mueve a la derecha")
        else:
            mover_carta(senda, idx, idx-1)
            mensajes.append("Duda se mueve a la izquierda")
    else:
        if opcion == 0:
            intercambiar_cartas(senda, idx-1, idx+1)
            mensajes.append("Duda intercambia adyacentes")
        else:
            mover_carta(senda, idx, idx-1)
            mensajes.append("Duda se mueve a la izquierda")
    return senda

def habilidad_rencor(senda, idx, _, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is not None:
        senda = destruir_carta(senda, objetivo, mensajes)
    else:
        mensajes.append("Rencor no tiene adyacentes")
    return senda

def habilidad_miedo(senda, idx, _, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is not None:
        carta = senda.pop(objetivo)
        insert_pos = 1 if len(senda) > 1 else 0
        senda.insert(insert_pos, carta)
        mensajes.append(f"{carta['nombre']} enviado al inicio")
    else:
        mensajes.append("Miedo no tiene adyacentes")
    return senda

def habilidad_pereza(senda, idx, opcion, mensajes):
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is not None:
        if opcion == 0:
            nueva_pos = objetivo - 2
            if nueva_pos < 0:
                nueva_pos = 0
            if nueva_pos != objetivo:
                mover_carta(senda, objetivo, nueva_pos)
                mensajes.append("Retrocede adyacente 2")
            else:
                nueva_self = idx + 1 if idx < len(senda)-1 else idx-1
                mover_carta(senda, idx, nueva_self)
                mensajes.append("Pereza avanza 1")
        else:
            nueva_self = idx + 1 if idx < len(senda)-1 else idx-1
            mover_carta(senda, idx, nueva_self)
            mensajes.append("Pereza avanza 1")
    else:
        mensajes.append("Pereza no tiene adyacentes")
    return senda

def habilidad_ejercicio(senda, idx, dist, dir, mensajes):
    otro = idx + dir * dist
    if 0 <= otro < len(senda):
        intercambiar_cartas(senda, idx, otro)
        mensajes.append(f"Ejercicio intercambia con carta a {dist} espacios hacia {'izquierda' if dir==-1 else 'derecha'}")
    else:
        mensajes.append("No hay carta a esa distancia/dirección")
    return senda

def habilidad_cizanyoso(senda, idx, opcion, mensajes):
    try:
        idx_rencor = next(i for i, c in enumerate(senda) if c["id"] == "rencor")
    except StopIteration:
        mensajes.append("No hay Rencor")
        return senda
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is None:
        mensajes.append("Cizañoso no tiene adyacentes")
        return senda
    carta_obj = senda[objetivo]
    if carta_obj["id"] == "rencor":
        direccion = -1 if idx_rencor > 0 else 1
        nueva_pos = idx_rencor - 2 if direccion == -1 else idx_rencor + 2
        nueva_pos = max(0, min(len(senda)-1, nueva_pos))
        mover_carta(senda, idx_rencor, nueva_pos)
        mensajes.append("Rencor se mueve hacia Aprendiz")
    else:
        if opcion == 0:
            if idx_rencor > objetivo:
                nueva_pos = idx_rencor - 1
            else:
                nueva_pos = idx_rencor + 1
            nueva_pos = max(0, min(len(senda)-1, nueva_pos))
            mover_carta(senda, objetivo, nueva_pos)
            mensajes.append(f"{carta_obj['nombre']} se mueve antes de Rencor")
        else:
            direccion = -1 if idx_rencor > 0 else 1
            nueva_pos = idx_rencor - 2 if direccion == -1 else idx_rencor + 2
            nueva_pos = max(0, min(len(senda)-1, nueva_pos))
            mover_carta(senda, idx_rencor, nueva_pos)
            mensajes.append("Rencor se mueve hacia Aprendiz")
    return senda

def habilidad_filosofia(senda, idx, dist, dir, mensajes):
    otro = idx + dir * dist
    if not (0 <= otro < len(senda)):
        mensajes.append("No hay carta a esa distancia/dirección")
        return senda
    mover = 4 - dist
    nueva_pos = otro + dir * mover
    nueva_pos = max(0, min(len(senda)-1, nueva_pos))
    if nueva_pos != otro:
        mover_carta(senda, otro, nueva_pos)
        mensajes.append(f"Filosofía mueve carta a {dist} de distancia {mover} espacios")
    else:
        mensajes.append("No se pudo mover")
    return senda

def habilidad_herbolaria(senda, idx, cual, dir, mensajes):
    ady = idx + dir
    if not (0 <= ady < len(senda)):
        mensajes.append("No hay carta en esa dirección")
        return senda
    if cual == 0:
        nueva_pos = ady - 2
        if nueva_pos < 0:
            nueva_pos = 0
        if nueva_pos != ady:
            mover_carta(senda, ady, nueva_pos)
            mensajes.append("Herbolaria retrocede 2")
        else:
            mensajes.append("No se pudo retroceder")
    else:
        nueva_pos = ady + 1
        if nueva_pos >= len(senda):
            nueva_pos = len(senda)-1
        if nueva_pos != ady:
            mover_carta(senda, ady, nueva_pos)
            mensajes.append("Herbolaria adelanta 1")
        else:
            mensajes.append("No se pudo adelantar")
    return senda

def habilidad_meditacion(senda, idx, dir, mensajes):
    otro = idx + dir * 3
    if 0 <= otro < len(senda):
        intercambiar_cartas(senda, idx, otro)
        mensajes.append("Meditación intercambia a 3 espacios")
    else:
        mensajes.append("No hay carta a 3 espacios en esa dirección")
    return senda

def habilidad_oracion(senda, idx, dir, mensajes):
    otro = idx + dir
    if 0 <= otro < len(senda):
        intercambiar_cartas(senda, idx, otro)
        mensajes.append(f"Oración intercambia con {'izquierda' if dir==-1 else 'derecha'}")
    else:
        mensajes.append("No hay carta en esa dirección")
    return senda

def habilidad_envidia(senda, idx, opcion, mensajes):
    try:
        idx_rencor = next(i for i, c in enumerate(senda) if c["id"] == "rencor")
    except StopIteration:
        mensajes.append("No hay Rencor")
        return senda
    objetivo = obtener_adyacente_mas_bajo(senda, idx)
    if objetivo is None:
        mensajes.append("Envidia no tiene adyacentes")
        return senda
    carta_obj = senda[objetivo]
    if carta_obj["id"] == "rencor":
        direccion = -1 if idx_rencor > 0 else 1
        nueva_pos = idx_rencor - 2 if direccion == -1 else idx_rencor + 2
        nueva_pos = max(0, min(len(senda)-1, nueva_pos))
        mover_carta(senda, idx_rencor, nueva_pos)
        mensajes.append("Rencor se mueve hacia Aprendiz")
    else:
        if opcion == 0:
            if idx_rencor > objetivo:
                nueva_pos = objetivo + 2
            else:
                nueva_pos = objetivo - 2
            nueva_pos = max(0, min(len(senda)-1, nueva_pos))
            mover_carta(senda, objetivo, nueva_pos)
            mensajes.append(f"{carta_obj['nombre']} se mueve hacia Rencor")
        else:
            direccion = -1 if idx_rencor > 0 else 1
            nueva_pos = idx_rencor - 2 if direccion == -1 else idx_rencor + 2
            nueva_pos = max(0, min(len(senda)-1, nueva_pos))
            mover_carta(senda, idx_rencor, nueva_pos)
            mensajes.append("Rencor se mueve hacia Aprendiz")
    return senda

def habilidad_peregrino(senda, idx, dir, mensajes):
    ady = idx + dir
    if not (0 <= ady < len(senda)):
        mensajes.append("No hay carta en esa dirección")
        return senda
    nueva_pos = ady + 2
    if nueva_pos >= len(senda):
        nueva_pos = len(senda)-1
    if nueva_pos != ady:
        mover_carta(senda, ady, nueva_pos)
        mensajes.append("Peregrino mueve adyacente 2 espacios")
    else:
        mensajes.append("No se pudo mover")
    return senda

def habilidad_magia(senda, idx, cual, dir, mensajes):
    ady = idx + dir
    if not (0 <= ady < len(senda)):
        mensajes.append("No hay carta en esa dirección")
        return senda
    if cual == 0:
        nueva_pos = ady - 3
        if nueva_pos < 0:
            nueva_pos = 0
        if nueva_pos != ady:
            mover_carta(senda, ady, nueva_pos)
            mensajes.append("Magia retrocede 3")
        else:
            mensajes.append("No se pudo retroceder")
    else:
        nueva_pos = ady + 2
        if nueva_pos >= len(senda):
            nueva_pos = len(senda)-1
        if nueva_pos != ady:
            mover_carta(senda, ady, nueva_pos)
            mensajes.append("Magia adelanta 2")
        else:
            mensajes.append("No se pudo adelantar")
    return senda

def habilidad_cuerpo_astral(senda, idx, dir, mensajes):
    otro = idx + dir * 4
    if 0 <= otro < len(senda):
        intercambiar_cartas(senda, idx, otro)
        mensajes.append("Cuerpo Astral intercambia a 4 espacios")
    else:
        mensajes.append("No hay carta a 4 espacios en esa dirección")
    return senda

# -------------------- CONFIGURACIÓN DE CARTAS --------------------
HABILIDADES_INFO = {
    "duda": {"func": habilidad_duda, "opciones": ["Intercambiar adyacentes", "Mover esta carta 1 espacio"], "tipo": "simple"},
    "rencor": {"func": habilidad_rencor, "opciones": [], "tipo": "simple"},
    "miedo": {"func": habilidad_miedo, "opciones": [], "tipo": "simple"},
    "pereza": {"func": habilidad_pereza, "opciones": ["Retroceder adyacente bajo 2", "Avanza esta carta 1"], "tipo": "simple"},
    "ejercicio": {
        "func": habilidad_ejercicio,
        "tipo": "distancia_direccion",
        "distancias": [1, 2],
        "direcciones": [(-1, "Izquierda"), (1, "Derecha")]
    },
    "cizanoso": {"func": habilidad_cizanyoso, "opciones": ["Mover adyacente antes de Rencor", "Mover Rencor hacia Aprendiz"], "tipo": "simple"},
    "filosofia": {
        "func": habilidad_filosofia,
        "tipo": "distancia_direccion",
        "distancias": [1, 2, 3],
        "direcciones": [(-1, "Izquierda"), (1, "Derecha")]
    },
    "herbolaria": {
        "func": habilidad_herbolaria,
        "tipo": "doble_seleccion",
        "opciones1": ["Retroceder 2", "Adelantar 1"],
        "direcciones": [(-1, "Izquierda"), (1, "Derecha")]
    },
    "meditacion": {"func": habilidad_meditacion, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "oracion": {"func": habilidad_oracion, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "envidia": {"func": habilidad_envidia, "opciones": ["Mover adyacente hacia Rencor", "Mover Rencor hacia Aprendiz"], "tipo": "simple"},
    "peregrino": {"func": habilidad_peregrino, "tipo": "direccion", "direcciones": [(-1, "Izquierda"), (1, "Derecha")]},
    "magia": {
        "func": habilidad_magia,
        "tipo": "doble_seleccion",
        "opciones1": ["Retroceder 3", "Adelantar 2"],
        "direcciones": [(-1, "Izquierda"), (1, "Derecha")]
    },
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
            dir = opcion_valores[0]
            nueva_senda = func(nueva_senda, idx, dir, mensajes)
        elif info["tipo"] == "distancia_direccion":
            dist, dir = opcion_valores
            nueva_senda = func(nueva_senda, idx, dist, dir, mensajes)
        elif info["tipo"] == "doble_seleccion":
            cual, dir = opcion_valores
            nueva_senda = func(nueva_senda, idx, cual, dir, mensajes)
    except Exception as e:
        return senda, f"Error al ejecutar habilidad: {e}", False
    return nueva_senda, " | ".join(mensajes), True

# -------------------- FUNCIONES DE JUEGO --------------------
def obtener_falsos_ordenados(senda):
    falsos = [(c["id"], c["numero"]) for c in senda if c.get("subclase") == "FALSO MAESTRO" and not c["es_fijo"]]
    falsos.sort(key=lambda x: x[1])
    return falsos

def iniciar_turno_falsos():
    global falsos_pendientes, turno_maestro
    falsos_pendientes = obtener_falsos_ordenados(senda)
    turno_maestro = False

def verificar_fin_juego(senda):
    idx_aprendiz = next((i for i,c in enumerate(senda) if c["id"]=="aprendiz"), None)
    idx_ahpuch = next((i for i,c in enumerate(senda) if c["id"]=="ah_puch"), None)
    if idx_aprendiz is None:
        return "derrota", "El Aprendiz ha sido destruido"
    if idx_ahpuch is None:
        return "victoria", "Ah Puch ha sido destruido"
    if idx_aprendiz == idx_ahpuch - 1:
        return "victoria", "El Aprendiz ha llegado a la meta"
    return None, None

def mostrar_mensaje_temporal(texto):
    global MENSAJE_TEMPORAL, TIEMPO_MENSAJE
    MENSAJE_TEMPORAL = texto
    TIEMPO_MENSAJE = pygame.time.get_ticks() + 2000

def limpiar_seleccion():
    global seleccion_pendiente, esperando_opcion, opcion_rects
    seleccion_pendiente = None
    esperando_opcion = False
    opcion_rects = []

# -------------------- DIBUJO --------------------
def get_card_rect(i):
    row = i // CARDS_PER_ROW
    col = i % CARDS_PER_ROW
    total_width = CARDS_PER_ROW * CARD_W + (CARDS_PER_ROW - 1) * GAP
    start_x = (W - total_width) // 2
    total_height = ((len(senda) + CARDS_PER_ROW - 1) // CARDS_PER_ROW) * (CARD_H + GAP) + GAP
    start_y = (H - total_height) // 2
    x = start_x + col * (CARD_W + GAP)
    y = start_y + row * (CARD_H + GAP)
    return pygame.Rect(x, y, CARD_W, CARD_H)

def color_carta(carta, hovering, seleccionada):
    if seleccionada:
        return COLOR_SELECTED
    if hovering:
        return COLOR_HOVER
    if carta["color"] == "rojo":
        return (220, 80, 80)
    if carta["color"] == "azul":
        return (80, 140, 255)
    return (200, 200, 200)

def dibujar_carta(carta, rect, hovering=False, seleccionada=False):
    pygame.draw.rect(screen, color_carta(carta, hovering, seleccionada), rect, border_radius=10)
    pygame.draw.rect(screen, COLOR_BORDER, rect, width=2, border_radius=10)
    if carta["numero"] not in (0, 15):
        num_surf = font_subclass.render(str(carta["numero"]), True, (0,0,0))
        screen.blit(num_surf, (rect.x+8, rect.y+8))
    nombre = carta["nombre"]
    palabras = nombre.split()
    lineas, linea = [], ""
    for p in palabras:
        prueba = (linea + " " + p).strip()
        if font_nombre.size(prueba)[0] < CARD_W - 10:
            linea = prueba
        else:
            lineas.append(linea)
            linea = p
    lineas.append(linea)
    total_h = len(lineas) * font_nombre.get_height()
    y_texto = rect.centery - total_h // 2
    for linea in lineas:
        surf = font_nombre.render(linea, True, (0,0,0))
        screen.blit(surf, (rect.centerx - surf.get_width()//2, y_texto))
        y_texto += font_nombre.get_height()
    if carta["subclase"]:
        sub = carta["subclase"]
        if "FALSO" in sub:
            sub = "F. MAESTRO"
        elif "MAESTRO" in sub:
            sub = "MAESTRO"
        sub_surf = font_subclass.render(sub, True, (30,30,30))
        screen.blit(sub_surf, (rect.centerx - sub_surf.get_width()//2, rect.bottom - 22))

def dibujar_panel_y_botones(carta_hover):
    global boton_siguiente_rect, opcion_rects
    panel_rect = pygame.Rect(PANEL_MARGIN, H-PANEL_H-PANEL_MARGIN, W-PANEL_MARGIN*2, PANEL_H)
    pygame.draw.rect(screen, (20,20,40), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (150,150,150), panel_rect, width=2, border_radius=10)
    
    if turno_maestro:
        turno_texto = "TURNO: MAESTROS (Azul) - Haz clic en una carta azul"
        color_turno = (80, 140, 255)
    else:
        turno_texto = f"TURNO: FALSOS MAESTROS (Rojo) - Faltan: {len(falsos_pendientes)}"
        color_turno = (220, 80, 80)
    turno_surf = font_turno.render(turno_texto, True, color_turno)
    screen.blit(turno_surf, (W//2 - turno_surf.get_width()//2, 20))
    
    if seleccion_pendiente:
        opciones = seleccion_pendiente["opciones"]
        button_w = 200
        button_h = 40
        spacing = 20
        total_w = len(opciones) * button_w + (len(opciones)-1)*spacing
        start_x = (W - total_w) // 2
        y_buttons = panel_rect.y + 20
        opcion_rects.clear()
        for i, (valor, texto) in enumerate(opciones):
            rect = pygame.Rect(start_x + i*(button_w+spacing), y_buttons, button_w, button_h)
            pygame.draw.rect(screen, (100,100,150), rect, border_radius=5)
            text_surf = font_habilidad.render(texto, True, (255,255,255))
            screen.blit(text_surf, (rect.x+10, rect.y+10))
            opcion_rects.append((rect, i, valor))
        return
    
    if carta_hover and carta_hover["habilidad"]:
        texto = f"{carta_hover['nombre']}: {carta_hover['habilidad']}"
        palabras = texto.split()
        lineas, linea = [], ""
        for p in palabras:
            prueba = (linea+" "+p).strip()
            if font_habilidad.size(prueba)[0] < panel_rect.width - 30:
                linea = prueba
            else:
                lineas.append(linea)
                linea = p
        lineas.append(linea)
        for j, linea in enumerate(lineas):
            surf = font_habilidad.render(linea, True, (200,200,200))
            screen.blit(surf, (panel_rect.x+15, panel_rect.y+10 + j*18))
    else:
        if ULTIMA_ACCION:
            texto = f"Última acción: {ULTIMA_ACCION}"
            palabras = texto.split()
            lineas, linea = [], ""
            for p in palabras:
                prueba = (linea+" "+p).strip()
                if font_habilidad.size(prueba)[0] < panel_rect.width - 30:
                    linea = prueba
                else:
                    lineas.append(linea)
                    linea = p
            lineas.append(linea)
            for j, linea in enumerate(lineas):
                surf = font_habilidad.render(linea, True, (200,200,200))
                screen.blit(surf, (panel_rect.x+15, panel_rect.y+10 + j*18))
        else:
            msg = "Haz clic en una carta MAESTRO (azul)" if turno_maestro else "Presiona 'Siguiente Falso'"
            hint = font_habilidad.render(msg, True, (100,100,120))
            screen.blit(hint, (panel_rect.x+15, panel_rect.centery - hint.get_height()//2))
    
    if not turno_maestro and not seleccion_pendiente and falsos_pendientes:
        btn_rect = pygame.Rect(panel_rect.right - 150, panel_rect.y + 10, 140, 40)
        pygame.draw.rect(screen, (200,100,100), btn_rect, border_radius=5)
        text = font_habilidad.render("Siguiente Falso", True, (255,255,255))
        screen.blit(text, (btn_rect.x+10, btn_rect.y+10))
        boton_siguiente_rect = btn_rect
    else:
        boton_siguiente_rect = None

# -------------------- BUCLE PRINCIPAL --------------------
reiniciar_juego()

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    if TIEMPO_MENSAJE and pygame.time.get_ticks() > TIEMPO_MENSAJE:
        MENSAJE_TEMPORAL = ""
        TIEMPO_MENSAJE = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and (victoria or game_over):
                reiniciar_juego()
                continue
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if victoria or game_over:
                continue
            
            # Selección de opción (MAESTRO)
            if seleccion_pendiente:
                for rect, idx_opt, valor in opcion_rects:
                    if rect.collidepoint(mouse_pos):
                        seleccion_pendiente["valores_actuales"].append(valor)
                        if seleccion_pendiente["paso"] + 1 >= len(seleccion_pendiente["pasos"]):
                            idx_carta = seleccion_pendiente["idx_carta"]
                            valores = seleccion_pendiente["valores_actuales"]
                            nueva_senda, msg, exito = ejecutar_habilidad(senda, idx_carta, valores)
                            if exito:
                                senda = nueva_senda
                                mostrar_mensaje_temporal(msg)
                                ULTIMA_ACCION = msg
                                resultado, msg_fin = verificar_fin_juego(senda)
                                if resultado:
                                    if resultado == "victoria":
                                        victoria = True
                                    else:
                                        game_over = True
                                    mostrar_mensaje_temporal(msg_fin)
                                    ULTIMA_ACCION = msg_fin
                                else:
                                    iniciar_turno_falsos()
                                limpiar_seleccion()
                            else:
                                mostrar_mensaje_temporal(msg)
                                limpiar_seleccion()
                        else:
                            seleccion_pendiente["paso"] += 1
                            paso = seleccion_pendiente["pasos"][seleccion_pendiente["paso"]]
                            if paso["tipo"] == "direcciones":
                                # Generar direcciones válidas (todas, luego validará al ejecutar)
                                opciones = paso["opciones"]  # ya son las direcciones
                                seleccion_pendiente["opciones"] = opciones
                            elif paso["tipo"] == "opciones":
                                seleccion_pendiente["opciones"] = paso["opciones"]
                        break
                continue
            
            # Turno MAESTRO
            if turno_maestro:
                for i, carta in enumerate(senda):
                    if get_card_rect(i).collidepoint(mouse_pos):
                        if carta.get("subclase") == "MAESTRO" and not carta["es_fijo"]:
                            info = HABILIDADES_INFO.get(carta["id"])
                            if not info:
                                mostrar_mensaje_temporal("Carta sin habilidad")
                                break
                            pasos = []
                            if info["tipo"] == "simple":
                                if info["opciones"]:
                                    pasos.append({"tipo": "opciones", "opciones": [(j, txt) for j, txt in enumerate(info["opciones"])]})
                                else:
                                    nueva_senda, msg, exito = ejecutar_habilidad(senda, i, [0])
                                    if exito:
                                        senda = nueva_senda
                                        mostrar_mensaje_temporal(msg)
                                        ULTIMA_ACCION = msg
                                        resultado, msg_fin = verificar_fin_juego(senda)
                                        if resultado:
                                            if resultado == "victoria":
                                                victoria = True
                                            else:
                                                game_over = True
                                            mostrar_mensaje_temporal(msg_fin)
                                            ULTIMA_ACCION = msg_fin
                                        else:
                                            iniciar_turno_falsos()
                                    else:
                                        mostrar_mensaje_temporal(msg)
                                    break
                            elif info["tipo"] == "direccion":
                                pasos.append({"tipo": "direcciones", "opciones": info["direcciones"]})
                            elif info["tipo"] == "distancia_direccion":
                                opciones_dist = [(d, f"A {d} espacios") for d in info["distancias"]]
                                pasos.append({"tipo": "opciones", "opciones": opciones_dist})
                                pasos.append({"tipo": "direcciones", "opciones": info["direcciones"]})
                            elif info["tipo"] == "doble_seleccion":
                                opciones1 = [(j, txt) for j, txt in enumerate(info["opciones1"])]
                                pasos.append({"tipo": "opciones", "opciones": opciones1})
                                pasos.append({"tipo": "direcciones", "opciones": info["direcciones"]})
                            
                            if pasos:
                                seleccion_pendiente = {
                                    "idx_carta": i,
                                    "paso": 0,
                                    "valores_actuales": [],
                                    "pasos": pasos
                                }
                                seleccion_pendiente["opciones"] = pasos[0]["opciones"]
                                esperando_opcion = True
                        else:
                            mostrar_mensaje_temporal("Solo puedes seleccionar cartas MAESTRO (azules)")
                        break
            
            # Turno FALSO: botón siguiente
            elif not turno_maestro and not seleccion_pendiente and boton_siguiente_rect and boton_siguiente_rect.collidepoint(mouse_pos):
                if falsos_pendientes:
                    carta_id, carta_num = falsos_pendientes.pop(0)
                    idx = None
                    for i, c in enumerate(senda):
                        if c["id"] == carta_id and c["numero"] == carta_num:
                            idx = i
                            break
                    if idx is None:
                        mostrar_mensaje_temporal("La carta ya no existe (fue destruida).")
                        if not falsos_pendientes:
                            turno_maestro = True
                            ULTIMA_ACCION = ""
                            mostrar_mensaje_temporal("Turno de MAESTROS nuevamente")
                        continue
                    carta = senda[idx]
                    info = HABILIDADES_INFO.get(carta["id"])
                    if not info:
                        mostrar_mensaje_temporal("Error: carta sin habilidad")
                        continue
                    nueva_senda, msg, exito = ejecutar_habilidad(senda, idx, [0])
                    if exito:
                        senda = nueva_senda
                        mostrar_mensaje_temporal(f"Falso: {msg}")
                        ULTIMA_ACCION = msg
                        resultado, msg_fin = verificar_fin_juego(senda)
                        if resultado:
                            if resultado == "victoria":
                                victoria = True
                            else:
                                game_over = True
                            mostrar_mensaje_temporal(msg_fin)
                            ULTIMA_ACCION = msg_fin
                        if not falsos_pendientes:
                            turno_maestro = True
                            ULTIMA_ACCION = ""
                            mostrar_mensaje_temporal("Turno de MAESTROS nuevamente")
                    else:
                        mostrar_mensaje_temporal(f"Error: {msg}")
                else:
                    turno_maestro = True
    
    # Dibujar
    screen.fill((40,40,60))
    
    carta_hover = None
    for i, carta in enumerate(senda):
        rect = get_card_rect(i)
        if rect.collidepoint(mouse_pos):
            carta_hover = carta
        dibujar_carta(carta, rect, rect.collidepoint(mouse_pos), False)
    
    dibujar_panel_y_botones(carta_hover)
    
    if MENSAJE_TEMPORAL:
        msg_surf = font_mensaje.render(MENSAJE_TEMPORAL, True, (255,255,100))
        msg_rect = msg_surf.get_rect(center=(W//2, H-20))
        screen.blit(msg_surf, msg_rect)
    
    # ---------- MEJORA ESTÉTICA: fondo para mensajes de victoria/derrota ----------
    if victoria or game_over:
        # Crear una superficie semitransparente para el fondo
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # negro con opacidad 180 (0-255)
        screen.blit(overlay, (0, 0))
        
        if victoria:
            texto_principal = "¡VICTORIA!"
            color_texto = (0, 255, 0)
        else:
            texto_principal = "DERROTA"
            color_texto = (255, 0, 0)
        
        # Texto principal
        main_surf = font_fin.render(texto_principal, True, color_texto)
        main_rect = main_surf.get_rect(center=(W//2, H//2 - 40))
        screen.blit(main_surf, main_rect)
        
        # Texto secundario (reinicio)
        sub_surf = font_mensaje.render("Presiona R para reiniciar   |   ESC para salir", True, (255, 255, 255))
        sub_rect = sub_surf.get_rect(center=(W//2, H//2 + 30))
        screen.blit(sub_surf, sub_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
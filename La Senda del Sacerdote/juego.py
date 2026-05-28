import pygame
import sys
import copy

# Importamos la lógica central y la IA
import logic
import dpSolver

def reiniciar_juego():
    global senda, turno_maestro, falsos_pendientes, victoria, game_over
    global ULTIMA_ACCION, MENSAJE_TEMPORAL, esperando_opcion, seleccion_pendiente
    logic.cargar_datos()
    senda = logic.cargar_senda_inicial()
    turno_maestro = True
    falsos_pendientes = []
    victoria = False
    game_over = False
    ULTIMA_ACCION = ""
    MENSAJE_TEMPORAL = ""
    esperando_opcion = False
    seleccion_pendiente = None

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
clock = pygame.time.Clock()

font_nombre    = pygame.font.SysFont("arial", 16, bold=True)
font_subclass  = pygame.font.SysFont("arial", 12)
font_habilidad = pygame.font.SysFont("arial", 15)
font_mensaje   = pygame.font.SysFont("arial", 18, bold=True)
font_turno     = pygame.font.SysFont("arial", 24, bold=True)
font_fin       = pygame.font.SysFont("arial", 32, bold=True)

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

# Variables Modo Auto-Play
auto_play = False
COOLDOWN_AUTO = 700
ultimo_paso_auto = 0

def mostrar_mensaje_temporal(texto):
    global MENSAJE_TEMPORAL, TIEMPO_MENSAJE
    MENSAJE_TEMPORAL = texto
    TIEMPO_MENSAJE = pygame.time.get_ticks() + 2000

def limpiar_seleccion():
    global seleccion_pendiente, esperando_opcion, opcion_rects
    seleccion_pendiente = None
    esperando_opcion = False
    opcion_rects = []

def get_card_rect(i):
    row = i // CARDS_PER_ROW
    col = i % CARDS_PER_ROW
    total_width = CARDS_PER_ROW * CARD_W + (CARDS_PER_ROW - 1) * GAP
    start_x = (W - total_width) // 2
    total_height = ((len(senda) + CARDS_PER_ROW - 1) // CARDS_PER_ROW) * (CARD_H + GAP) + GAP
    start_y = (H - total_height) // 2
    return pygame.Rect(start_x + col * (CARD_W + GAP), start_y + row * (CARD_H + GAP), CARD_W, CARD_H)

def dibujar_carta(carta, rect, hovering=False):
    color = COLOR_HOVER if hovering else ((220, 80, 80) if carta.get("color") == "rojo" else (80, 140, 255) if carta.get("color") == "azul" else (200, 200, 200))
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, COLOR_BORDER, rect, width=2, border_radius=10)
    
    if carta["numero"] not in (0, 15):
        screen.blit(font_subclass.render(str(carta["numero"]), True, (0,0,0)), (rect.x+8, rect.y+8))
        
    # --- RESTAURACIÓN 1: Word-Wrap para nombres de cartas largos (CUERPO ASTRAL) ---
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
    # -----------------------------------------------------------------------------
    
    if carta.get("subclase"):
        sub = "F. MAESTRO" if "FALSO" in carta["subclase"] else "MAESTRO"
        sub_surf = font_subclass.render(sub, True, (30,30,30))
        screen.blit(sub_surf, (rect.centerx - sub_surf.get_width()//2, rect.bottom - 22))

def dibujar_interfaz(carta_hover):
    global boton_siguiente_rect, opcion_rects
    panel_rect = pygame.Rect(PANEL_MARGIN, H-PANEL_H-PANEL_MARGIN, W-PANEL_MARGIN*2, PANEL_H)
    pygame.draw.rect(screen, (20,20,40), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (150,150,150), panel_rect, width=2, border_radius=10)
    
    status_auto = " [AUTO-PLAY ACTIVO]" if auto_play else " [Presiona 'A' para Autoplay]"
    color_turno = (80, 140, 255) if turno_maestro else (220, 80, 80)
    texto_turno = "TURNO: MAESTROS (Azul)" if turno_maestro else f"TURNO: FALSOS MAESTROS (Faltan: {len(falsos_pendientes)})"
    turno_surf = font_turno.render(texto_turno + status_auto, True, color_turno)
    screen.blit(turno_surf, (W//2 - turno_surf.get_width()//2, 20))
    
    if seleccion_pendiente:
        opcion_rects.clear()
        opciones = seleccion_pendiente["opciones"]
        
        # --- RESTAURACIÓN 2: Centrado Dinámico de Botones ---
        button_w = 200
        button_h = 40
        spacing = 20
        total_w = len(opciones) * button_w + (len(opciones)-1) * spacing
        start_x = (W - total_w) // 2
        y_buttons = panel_rect.y + 20
        
        for i, (valor, texto) in enumerate(opciones):
            rect = pygame.Rect(start_x + i*(button_w+spacing), y_buttons, button_w, button_h)
            pygame.draw.rect(screen, (100,100,150), rect, border_radius=5)
            text_surf = font_habilidad.render(texto, True, (255,255,255))
            # Centrar el texto dentro del botón
            screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
            opcion_rects.append((rect, i, valor))
        return
        # ----------------------------------------------------

    texto_mostrar = f"{carta_hover['nombre']}: {carta_hover['habilidad']}" if carta_hover else (f"Última acción: {ULTIMA_ACCION}" if ULTIMA_ACCION else "")
    
    # --- RESTAURACIÓN 4 (Bonus): Word-Wrap para el Panel Inferior ---
    if texto_mostrar:
        palabras = texto_mostrar.split()
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
    # ----------------------------------------------------------------
        
    if not turno_maestro and not seleccion_pendiente and falsos_pendientes and not auto_play:
        boton_siguiente_rect = pygame.Rect(panel_rect.right - 150, panel_rect.y + 10, 140, 40)
        pygame.draw.rect(screen, (200,100,100), boton_siguiente_rect, border_radius=5)
        text_surf = font_habilidad.render("Siguiente Falso", True, (255,255,255))
        screen.blit(text_surf, (boton_siguiente_rect.centerx - text_surf.get_width()//2, boton_siguiente_rect.centery - text_surf.get_height()//2))
    else:
        boton_siguiente_rect = None

reiniciar_juego()
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    ahora_ms = pygame.time.get_ticks()
    
    if TIEMPO_MENSAJE and ahora_ms > TIEMPO_MENSAJE:
        MENSAJE_TEMPORAL = ""
        TIEMPO_MENSAJE = 0

    if auto_play and not victoria and not game_over and (ahora_ms - ultimo_paso_auto > COOLDOWN_AUTO):
        if turno_maestro and not esperando_opcion:
            idx, vals, desc = dpSolver.obtener_movimiento_optimo(senda)
            if idx is not None:
                senda, msg, exito = logic.ejecutar_habilidad(senda, idx, vals)
                mostrar_mensaje_temporal(msg); ULTIMA_ACCION = msg
                res, msg_fin = logic.verificar_fin_juego(senda)
                if res:
                    victoria = (res == "victoria")
                    game_over = not victoria
                    mostrar_mensaje_temporal(msg_fin)
                else:
                    falsos_pendientes = logic.obtener_falsos_ordenados(senda)
                    turno_maestro = False
            else:
                mostrar_mensaje_temporal("IA sin movimientos ganadores.")
                auto_play = False
            ultimo_paso_auto = ahora_ms

        elif not turno_maestro and falsos_pendientes:
            carta_id, carta_num = falsos_pendientes.pop(0)
            idx = next((i for i, c in enumerate(senda) if c["id"] == carta_id and c["numero"] == carta_num), None)
            if idx is not None:
                senda, msg, exito = logic.ejecutar_habilidad(senda, idx, [0])
                mostrar_mensaje_temporal(f"Falso: {msg}"); ULTIMA_ACCION = msg
                res, msg_fin = logic.verificar_fin_juego(senda)
                if res:
                    victoria = (res == "victoria")
                    game_over = not victoria
                    mostrar_mensaje_temporal(msg_fin)
            if not falsos_pendientes:
                turno_maestro = True
            ultimo_paso_auto = ahora_ms

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and (victoria or game_over): reiniciar_juego()
            if event.key == pygame.K_a: auto_play = not auto_play
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not (victoria or game_over or auto_play):
            if seleccion_pendiente:
                for rect, idx_opt, valor in opcion_rects:
                    if rect.collidepoint(mouse_pos):
                        seleccion_pendiente["valores"].append(valor)
                        if seleccion_pendiente["paso"] + 1 >= len(seleccion_pendiente["pasos"]):
                            senda, msg, exito = logic.ejecutar_habilidad(senda, seleccion_pendiente["idx"], seleccion_pendiente["valores"])
                            mostrar_mensaje_temporal(msg); ULTIMA_ACCION = msg
                            res, msg_fin = logic.verificar_fin_juego(senda)
                            if res:
                                victoria = (res == "victoria")
                                game_over = not victoria
                            else:
                                falsos_pendientes = logic.obtener_falsos_ordenados(senda)
                                turno_maestro = False
                            limpiar_seleccion()
                        else:
                            seleccion_pendiente["paso"] += 1
                            seleccion_pendiente["opciones"] = seleccion_pendiente["pasos"][seleccion_pendiente["paso"]]["opciones"]
                        break
                continue
                
            if turno_maestro:
                for i, carta in enumerate(senda):
                    if get_card_rect(i).collidepoint(mouse_pos) and carta.get("subclase") == "MAESTRO" and not carta["es_fijo"]:
                        info = logic.HABILIDADES_INFO.get(carta["id"])
                        pasos = []
                        if info["tipo"] == "simple":
                            if info["opciones"]: pasos.append({"opciones": [(j, txt) for j, txt in enumerate(info["opciones"])]})
                            else:
                                senda, msg, exito = logic.ejecutar_habilidad(senda, i, [0])
                                mostrar_mensaje_temporal(msg); ULTIMA_ACCION = msg
                                res, msg_fin = logic.verificar_fin_juego(senda)
                                if res:
                                    victoria = (res == "victoria")
                                    game_over = not victoria
                                else:
                                    falsos_pendientes = logic.obtener_falsos_ordenados(senda)
                                    turno_maestro = False
                                break
                        elif info["tipo"] == "direccion": pasos.append({"opciones": info["direcciones"]})
                        elif info["tipo"] == "distancia_direccion":
                            pasos.append({"opciones": [(d, f"A {d} espacios") for d in info["distancias"]]})
                            pasos.append({"opciones": info["direcciones"]})
                        elif info["tipo"] == "doble_seleccion":
                            pasos.append({"opciones": [(j, txt) for j, txt in enumerate(info["opciones1"])]})
                            pasos.append({"opciones": info["direcciones"]})
                        
                        if pasos:
                            seleccion_pendiente = {"idx": i, "paso": 0, "valores": [], "pasos": pasos, "opciones": pasos[0]["opciones"]}
                            esperando_opcion = True
                        break
            elif not turno_maestro and boton_siguiente_rect and boton_siguiente_rect.collidepoint(mouse_pos):
                if falsos_pendientes:
                    carta_id, carta_num = falsos_pendientes.pop(0)
                    idx = next((i for i, c in enumerate(senda) if c["id"] == carta_id and c["numero"] == carta_num), None)
                    if idx is not None:
                        senda, msg, exito = logic.ejecutar_habilidad(senda, idx, [0])
                        mostrar_mensaje_temporal(msg); ULTIMA_ACCION = msg
                        res, msg_fin = logic.verificar_fin_juego(senda)
                        if res:
                            victoria = (res == "victoria")
                            game_over = not victoria
                    if not falsos_pendientes: turno_maestro = True

    screen.fill((40,40,60))
    carta_hover = None
    for i, carta in enumerate(senda):
        target_rect = get_card_rect(i)
        if "anim_x" not in carta:
            carta["anim_x"], carta["anim_y"] = target_rect.x, target_rect.y
            
        # LERP
        carta["anim_x"] += (target_rect.x - carta["anim_x"]) * 0.15
        carta["anim_y"] += (target_rect.y - carta["anim_y"]) * 0.15
        
        anim_rect = pygame.Rect(carta["anim_x"], carta["anim_y"], CARD_W, CARD_H)
        if anim_rect.collidepoint(mouse_pos): carta_hover = carta
        dibujar_carta(carta, anim_rect, anim_rect.collidepoint(mouse_pos))
        
    dibujar_interfaz(carta_hover)
    
    if MENSAJE_TEMPORAL:
        msg_surf = font_mensaje.render(MENSAJE_TEMPORAL, True, (255,255,100))
        screen.blit(msg_surf, msg_surf.get_rect(center=(W//2, H-20)))
    
    if victoria or game_over:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        texto, color = ("¡VICTORIA!", (0,255,0)) if victoria else ("DERROTA", (255,0,0))
        main_surf = font_fin.render(texto, True, color)
        screen.blit(main_surf, main_surf.get_rect(center=(W//2, H//2 - 40)))
        
        # --- RESTAURACIÓN 3: Texto de Reinicio/Salir ---
        sub_surf = font_mensaje.render("Presiona R para reiniciar   |   ESC para salir", True, (255, 255, 255))
        screen.blit(sub_surf, sub_surf.get_rect(center=(W//2, H//2 + 30)))
        # -----------------------------------------------
        
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
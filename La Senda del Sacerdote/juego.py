import pygame
import json
import random

with open("cartas.json") as f:
    data = json.load(f)

todas = data["cartas"]
aprendiz   = next(c for c in todas if c["id"] == "aprendiz")
ah_puch    = next(c for c in todas if c["id"] == "ah_puch")
mezclables = [c for c in todas if not c["es_fijo"]]

random.shuffle(mezclables)
senda = [aprendiz] + mezclables + [ah_puch]

for carta in senda:
    carta["selected"] = False

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
clock = pygame.time.Clock()

font_nombre    = pygame.font.SysFont("arial", 16, bold=True)
font_subclass  = pygame.font.SysFont("arial", 12)
font_habilidad = pygame.font.SysFont("arial", 15)

CARD_W, CARD_H = 130, 190
GAP = 15
CARDS_PER_ROW = 8
PANEL_H = 80
PANEL_MARGIN = 20

COLOR_HOVER    = (255, 255, 180)
COLOR_SELECTED = (100, 200, 255)
COLOR_BORDER   = (50, 50, 50)

def color_carta(carta, hovering):
    if carta["selected"]:
        return COLOR_SELECTED
    if hovering:
        return COLOR_HOVER
    if carta["color"] == "rojo":
        return (220, 80, 80)
    if carta["color"] == "azul":
        return (80, 140, 255)
    return (200, 200, 200)

def get_card_rect(i):
    row = i // CARDS_PER_ROW
    col = i % CARDS_PER_ROW
    total_width = CARDS_PER_ROW * CARD_W + (CARDS_PER_ROW - 1) * GAP
    start_x = (W - total_width) // 2
    total_height = 2 * CARD_H + GAP * 6
    start_y = (H - total_height) // 2
    x = start_x + col * (CARD_W + GAP)
    y = start_y + row * (CARD_H + GAP * 6)
    return pygame.Rect(x, y, CARD_W, CARD_H)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, carta in enumerate(senda):
                if get_card_rect(i).collidepoint(mouse_pos):
                    carta["selected"] = not carta["selected"]

    screen.fill((40, 40, 60))

    # ✅ Detectar hover ANTES del loop de dibujo
    carta_hover = None
    for i, carta in enumerate(senda):
        if get_card_rect(i).collidepoint(mouse_pos):
            carta_hover = carta
            break

    # ✅ Dibujar cartas (loop limpio, sin panel adentro)
    for i, carta in enumerate(senda):
        rect = get_card_rect(i)
        hovering = rect.collidepoint(mouse_pos)
        draw_rect = rect.move(0, -10 if hovering else 0)

        pygame.draw.rect(screen, color_carta(carta, hovering), draw_rect, border_radius=10)
        pygame.draw.rect(screen, COLOR_BORDER, draw_rect, width=2, border_radius=10)

        if carta["numero"] not in (0, 15):
            num_surf = font_subclass.render(str(carta["numero"]), True, (0, 0, 0))
            screen.blit(num_surf, (draw_rect.x + 8, draw_rect.y + 8))

        nombre = carta["nombre"]
        palabras = nombre.split()
        lineas, linea_actual = [], ""
        for palabra in palabras:
            prueba = (linea_actual + " " + palabra).strip()
            if font_nombre.size(prueba)[0] < CARD_W - 10:
                linea_actual = prueba
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        lineas.append(linea_actual)

        total_texto_h = len(lineas) * font_nombre.get_height()
        y_texto = draw_rect.centery - total_texto_h // 2
        for linea in lineas:
            surf = font_nombre.render(linea, True, (0, 0, 0))
            screen.blit(surf, (draw_rect.centerx - surf.get_width() // 2, y_texto))
            y_texto += font_nombre.get_height()

        if carta["subclase"]:
            sub_surf = font_subclass.render(carta["subclase"], True, (30, 30, 30))
            if sub_surf.get_width() > CARD_W - 10:
                abrev = "F. MAESTRO" if "FALSO" in carta["subclase"] else "MAESTRO"
                sub_surf = font_subclass.render(abrev, True, (30, 30, 30))
            screen.blit(sub_surf, (draw_rect.centerx - sub_surf.get_width() // 2, draw_rect.bottom - 22))

    # ✅ Panel DESPUÉS del loop, se dibuja una sola vez
    panel_rect = pygame.Rect(PANEL_MARGIN, H - PANEL_H - PANEL_MARGIN,
                             W - PANEL_MARGIN * 2, PANEL_H)
    pygame.draw.rect(screen, (20, 20, 40), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (150, 150, 150), panel_rect, width=2, border_radius=10)

    if carta_hover and carta_hover["habilidad"]:
        titulo = font_nombre.render(carta_hover["nombre"], True, (255, 255, 255))
        screen.blit(titulo, (panel_rect.x + 15, panel_rect.y + 10))

        texto = carta_hover["habilidad"]
        palabras = texto.split()
        lineas, linea_actual = [], ""
        for palabra in palabras:
            prueba = (linea_actual + " " + palabra).strip()
            if font_habilidad.size(prueba)[0] < panel_rect.width - 30:
                linea_actual = prueba
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        lineas.append(linea_actual)

        for j, linea in enumerate(lineas):
            surf = font_habilidad.render(linea, True, (200, 200, 200))
            screen.blit(surf, (panel_rect.x + 15, panel_rect.y + 32 + j * 18))
    else:
        hint = font_habilidad.render("Pasa el cursor sobre una carta para ver su habilidad.", True, (100, 100, 120))
        screen.blit(hint, (panel_rect.x + 15, panel_rect.centery - hint.get_height() // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
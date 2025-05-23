import sys# Importa el módulo sys para usar
import cv2  # OpenCV: permite capturar video desde la cámara y procesar imágenes.
import mediapipe as mp  # MediaPipe: herramienta de Google para detección de manos.
import pygame  # Pygame: biblioteca para crear videojuegos en Python.
import random  # Generador de números aleatorios.
import os  # Interacción con el sistema operativo (no se usa aún en este fragmento).
import time  # Manejo de tiempo (pausas, timestamps, etc).
import math  # Funciones matemáticas como raíz cuadrada.
import numpy as np
import copy
import heapq
from collections import deque
from random import choice, randint
import tkinter as tk
from tkinter import Listbox, Label

# Inicializar pygame
pygame.init()  # Inicializa todos los módulos de Pygame.
# ------------------------------------------------SONIDOS Y MUSICA--------------------------------------------------------
pygame.mixer.init()  # Inicializa el módulo de sonido (mezclador de audio).


# Pantalla redimensionable
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)  # Pantalla completa y redimensionable.
WINDOW_WIDTH, WINDOW_HEIGHT = screen.get_size()  # Captura el tamaño actual de la ventana.

# Colores
IMG_FOLDER = os.path.join("IMG")
WHITE = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
BLACK = (0, 0, 0)  # Color negro.
SKY_BLUE = (135, 206, 235)  # Azul cielo para el fondo.
BUTTON_BG_COLOR = (204, 130, 76)  # #cc824c
BUTTON_BORDER_COLOR = (221, 162, 105)  # #dda269
BLUE = (100, 149, 237)
HOVER = (230, 160, 100)
SAVE_BG = (204, 130, 76)   # #cc824c
SAVE_BORDER = (221, 162, 105)  # #dda269
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 105, 180), (0, 255, 255), (0, 0, 0)]
BUTTON_COLOR = (100, 200, 100)  # Verde
ancho=1920
alto=1080
TEXT_COLOR = (30, 30, 30)
SHADOW_COLOR = (180, 180, 220)


class CameraManager:
    def __init__(self, window_width=1620, window_height=900, use_dynamic_threshold=True):
        # Inicializar la cámara
        self.cap_camera = cv2.VideoCapture(0)
        if not self.cap_camera.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

        # Inicialización de MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Tamaño de la ventana
        self.window_width = window_width
        self.window_height = window_height

        # Variables del cursor
        self.cursor_x = self.window_width // 2
        self.cursor_y = self.window_height // 2
        self.is_shooting = False

        # Umbral dinámico de clic
        self.use_dynamic_threshold = use_dynamic_threshold
        self.click_threshold = 0.1

        # Inactividad
        self.frames_without_hand = 0

        # Fuente para mostrar mensaje
        pygame.font.init()
        self.font = pygame.font.Font(None, 48)

        # FPS
        self.clock = pygame.time.Clock()
        self.mensaje_mostrado = False
    def get_hand_position(self):
        ret, frame = self.cap_camera.read()
        if not ret:
            return None

        # Convertir a RGB y procesar
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            self.frames_without_hand = 0  # Reiniciar contador de inactividad

            hand_landmarks = results.multi_hand_landmarks[0]
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]

            # Coordenadas promedio entre índice y pulgar
            avg_x = (thumb_tip.x + index_tip.x) / 2
            avg_y = (thumb_tip.y + index_tip.y) / 2

            factor = 2
            new_cursor_x = int((1 - avg_x) * self.window_width * factor)
            new_cursor_y = int(avg_y * self.window_height * factor)

            # Suavizado del cursor
            self.cursor_x = int(self.cursor_x * 0.7 + new_cursor_x * 0.3)
            self.cursor_y = int(self.cursor_y * 0.7 + new_cursor_y * 0.3)

            # Requiere que realmente se toquen (distancia mínima)
            distance = math.sqrt((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2)

            # Fijar umbral manualmente a algo muy pequeño
            self.click_threshold = 0.02  # Puedes ajustar esto si aún es muy sensible

            self.is_shooting = distance < self.click_threshold

        else:
            self.frames_without_hand += 1
            self.is_shooting = False

        return self.cursor_x, self.cursor_y, self.is_shooting

    def mostrar_mensaje_ayuda(self, screen, mano_detectada):
        mensaje = "Pon tu mano frente a la cámara ;)"
        box_width, box_height = 600, 100
        x_final = self.window_width - box_width - 20
        y = self.window_height - box_height - 20
        x_inicial = self.window_width
        # Inicializar variables persistentes
        if not hasattr(self, 'cartel_estado'):
            self.cartel_estado = "oculto"  # Estados: oculto, entrando, visible, saliendo
            self.cartel_x = x_inicial
        # Transiciones de estado
        if self.cartel_estado == "oculto":
            if not mano_detectada:  # No hay mano → mostrar cartel
                self.cartel_estado = "entrando"
        elif self.cartel_estado == "entrando":
            self.cartel_x -= 20
            if self.cartel_x <= x_final:
                self.cartel_x = x_final
                self.cartel_estado = "visible"
        elif self.cartel_estado == "visible":
            if mano_detectada:  # Mano detectada → ocultar cartel
                self.cartel_estado = "saliendo"
        elif self.cartel_estado == "saliendo":
            self.cartel_x += 20
            if self.cartel_x >= x_inicial:
                self.cartel_x = x_inicial
                self.cartel_estado = "oculto"

        # Dibujar solo si el cartel no está oculto
        if self.cartel_estado != "oculto":
            box_rect = pygame.Rect(self.cartel_x, y, box_width, box_height)
            pygame.draw.rect(screen, SAVE_BG, box_rect, border_radius=15)
            pygame.draw.rect(screen, SAVE_BORDER, box_rect, 4, border_radius=15)

            text_surface = self.font.render(mensaje, True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=box_rect.center)
            screen.blit(text_surface, text_rect)

    def release(self):
        if hasattr(self, 'hands') and self.hands is not None:
            try:
                self.hands.close()
            except ValueError:
                pass
            self.hands = None

        if hasattr(self, 'cap_camera') and self.cap_camera is not None:
            self.cap_camera.release()
            self.cap_camera = None

    def restablecer_camara(self):
        self.cap_camera = cv2.VideoCapture(0)
        if not self.cap_camera.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
class ConfigManager:
    def __init__(self):
        self.daltonismo_actual = 0  # 0 = Ninguno, 1 = Protanopía, etc.
        self.volumen_musica = 1.0
        self.volumen_efectos = 1.0
        self.musica_pausada = False
        self.efectos_silenciados = False

        # Lista de canciones disponibles
        self.canciones = {
            "Spc80s": "Pistas//Spc80s.mp3",
            "SpcBeach": "Pistas//SpcBeach.mp3",
            "SpcDefault": "Pistas//SpcDefault.mp3",
            "SpcMain": "Pistas//SpcMain.mp3",
            "SpcPlayground": "Pistas//SpcPlayground.mp3",
            "SpcRoom": "Pistas//SpcRoom.mp3",
            "SpcSky": "Pistas//SpcSky.mp3",
            "SpcStar": "Pistas//SpcStar.mp3",
            "SpcWhy": "Pistas//SpcWhy.mp3"
        }

        # Seleccionar una canción aleatoria al iniciar
        self.musica_actual = random.choice(list(self.canciones.keys()))

        # Cargar y reproducir la música seleccionada
        self.cargar_musica()

    def cargar_musica(self):
        """Carga y reproduce la música actual con el volumen configurado"""
        pygame.mixer.music.load(self.canciones[self.musica_actual])
        pygame.mixer.music.play(-1)  # Reproducir en bucle
        pygame.mixer.music.set_volume(self.volumen_musica)
        self.musica_pausada = False
    def aplicar_filtro_daltonismo(self, screen):
        """Aplica el filtro de daltonismo actual a la pantalla"""
        if self.daltonismo_actual == 0:  # Ninguno
            return

        arr = pygame.surfarray.pixels3d(screen)
        if self.daltonismo_actual == 1:  # Protanopía
            arr[:, :, 0] = arr[:, :, 1]  # Red channel replaced with green
        elif self.daltonismo_actual == 2:  # Deuteranopía
            arr[:, :, 1] = arr[:, :, 0]  # Green channel replaced with red
        elif self.daltonismo_actual == 3:  # Tritanopía
            arr[:, :, 2] = arr[:, :, 0]  # Blue channel replaced with red
        del arr
def draw_text_centered(text, y, font_size=60, color=(0, 0, 0)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    x = WINDOW_WIDTH // 2 - text_surface.get_width() // 2
    screen.blit(text_surface, (x, y))
# dibujar una cruz como cursor
def draw_pointer(x, y, area_ancho, area_alto):
    # Calcular las coordenadas del rectángulo centrado
    left = (ancho - area_ancho) // 2
    right = left + area_ancho
    top = (alto - area_alto) // 2
    bottom = top + area_alto

    # Restringir x e y a esa área centrada
    x = max(left, min(x, right))
    y = max(top, min(y, bottom))

    # Dibujar el puntero
    pygame.draw.line(screen, BLACK, (x - 10, y), (x + 10, y), 2)  # Línea horizontal
    pygame.draw.line(screen, BLACK, (x, y - 10), (x, y + 10), 2)  # Línea vertical
def main_menu(camera_manager, config_manager):
    global WINDOW_WIDTH, WINDOW_HEIGHT

    # Configuraciones iniciales
    menu_running = True
    options = ["Inicio", "Instrucciones", "Configuración", "Salir"]
    selected_option = -1
    clock = pygame.time.Clock()

    # Cargar fondo del menú
    background_image = pygame.image.load("IMG//fondo menu principal.png")
    background_image = pygame.transform.scale(background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))

    # Cursor gestual
    cursor_x, cursor_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    is_shooting = False

    while menu_running:
        screen.blit(background_image, (0, 0))

        # Obtener posición de la mano
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)

        # Animación título (igual que antes)…
        # draw_text_centered(...)

        # Dibujar opciones como botones
        for i, option in enumerate(options):
            rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 250 + i*100, 300, 60)

            # Estilo base
            bg = BUTTON_BG_COLOR
            border = BUTTON_BORDER_COLOR

            # Hover gestual
            if rect.collidepoint(cursor_x, cursor_y):
                bg = HOVER

                # Si además “clickeo”:
                if is_shooting:
                    pygame.time.wait(200)
                    if i == 0:
                        playing_menu(camera_manager, config_manager)
                    elif i == 1:
                        show_instructions(camera_manager, "IMG//Instrucciones_Spectra.mp4", config_manager)
                    elif i == 2:
                        show_Config(camera_manager, config_manager)
                    elif i == 3:
                        salir()

            # Dibujar botón con radio y borde
            pygame.draw.rect(screen, bg,    rect, border_radius=10)
            pygame.draw.rect(screen, border,rect, 3,         border_radius=10)

            # Texto centrado
            draw_text_centered(option, rect.y + 10, 50, BLACK)

        # Puntero gestual
        draw_pointer(cursor_x, cursor_y, 1920, 1080)

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(30)

        # Manejo de QUIT/Escape
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                return "salir"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                camera_manager.release()
                pygame.quit()
                return "salir"
def playing_menu(camera_manager, config_manager):
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    background = pygame.image.load("IMG//Juegos_menu.png")
    screen_width, screen_height = screen.get_size()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    screen.blit(background, (0, 0))

    pygame.display.set_caption(" Spectra ")

    clock = pygame.time.Clock()
    # Definir botón "Volver"
    button_width = 200
    button_height = 60
    back_button_rect = pygame.Rect(1200, screen_height - button_height - 50, button_width, button_height)
    back_button_font = pygame.font.Font(None, 36)

    # Cargar las imágenes de colorear
    coloring_images_paths = [
        os.path.join(IMG_FOLDER, "dibujo.webp"),
        os.path.join(IMG_FOLDER, "tarjeta6.png"),
        os.path.join(IMG_FOLDER, "puzzle.webp"),
        os.path.join(IMG_FOLDER, "construc.webp"),
    ]
    coloring_images = [pygame.image.load(path) for path in coloring_images_paths]

    # Redimensionarlas para el menú
    thumbnail_size = (200, 200)
    thumbnails = [pygame.transform.scale(img, thumbnail_size) for img in coloring_images]

    # Posiciones en forma de mosaico
    spacing = 50
    start_x = (screen_width - (thumbnail_size[0] * 3 + spacing * 2)) // 2
    start_y = (screen_height - (thumbnail_size[1] * 2 + spacing)) // 2

    thumbnail_positions = [(510, 510), (510, 120), (940, 120), (940, 510)]
    thumbnail_rects = []

    for i, pos in enumerate(thumbnail_positions):
        rect = pygame.Rect(pos[0], pos[1], thumbnail_size[0], thumbnail_size[1])
        thumbnail_rects.append(rect)

    while True:
        # Obtener posición de la mano
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        else:
            cursor_x, cursor_y, is_shooting = screen_width // 2, screen_height // 2, False

        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        # Dibujar fondo
        screen.blit(background, (0, 0))
        # Detectar hover
        if back_button_rect.collidepoint(cursor_x, cursor_y):
            back_color = HOVER
            if is_shooting:
                main_menu(camera_manager, config_manager)
        else:
            back_color = BUTTON_BG_COLOR

        # Dibujar botón "Volver"
        pygame.draw.rect(screen, back_color, back_button_rect, border_radius=10)  # Fondo
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, back_button_rect, 3, border_radius=10)  # Borde

        text_surf = back_button_font.render("Volver", True, WHITE)
        text_rect = text_surf.get_rect(center=back_button_rect.center)
        screen.blit(text_surf, text_rect)
        # Acción del botón con gestos
        if back_button_rect.collidepoint(cursor_x, cursor_y):
            back_color = HOVER
            if is_shooting:
                return
        else:
            back_color = BUTTON_BG_COLOR

        # Dibujar miniaturas
        for i, rect in enumerate(thumbnail_rects):
            screen.blit(thumbnails[i], rect)

            if rect.collidepoint(cursor_x, cursor_y):
                pygame.draw.rect(screen, HOVER, rect, 5)
                if is_shooting:
                    pygame.time.wait(0)
                    if i == 0:
                        main_menu_DIBUJO(camera_manager,config_manager)
                    if i==1:
                        ejecutar_juego_memoria(camera_manager, config_manager)
                    if i==2:
                        ejecutar_puzzle_animales(camera_manager, config_manager)
                    else:
                        img="IMG//construccion.png"
                        show_under_construction(screen, img, camera_manager, config_manager)

        draw_pointer(cursor_x, cursor_y, 1920, 1080)
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(5)
def show_instructions(camera_manager, video_path, config_manager):
    running = True
    clock = pygame.time.Clock()

    # Cargar video de instrucciones
    cap_video = cv2.VideoCapture(video_path)

    # Inicializar posición del cursor
    cursor_x, cursor_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    is_shooting = False

    # Botón "Volver"
    font = pygame.font.SysFont("comicsans", 30)
    volver_rect = pygame.Rect(WINDOW_WIDTH - 290, WINDOW_HEIGHT - 150, 120, 50)

    while running:
        # Obtener datos de la mano (usando CameraManager)
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)
        # Leer frame del video
        ret_vid, frame_vid = cap_video.read()
        if not ret_vid:
            cap_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Procesar el frame de video para Pygame
        frame_vid = cv2.cvtColor(frame_vid, cv2.COLOR_BGR2RGB)
        frame_vid = cv2.resize(frame_vid, (WINDOW_WIDTH, WINDOW_HEIGHT))
        frame_vid = np.rot90(frame_vid, 1)
        frame_vid = np.flip(frame_vid, axis=0)
        frame_surface = pygame.surfarray.make_surface(frame_vid)

        # Dibujar el fondo de video
        screen.blit(frame_surface, (0, 0))

        # Dibujar botón "Volver"
        pygame.draw.rect(screen, BUTTON_BG_COLOR, volver_rect)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, volver_rect, 4)
        text = font.render("Volver", True, BLACK)
        text_rect = text.get_rect(center=volver_rect.center)
        screen.blit(text, text_rect)

        # Dibujar puntero
        draw_pointer(cursor_x, cursor_y, 1920, 1080)

        # Eventos de sistema
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                cap_video.release()
                pygame.quit()
                exit()

        # Detectar clic sobre botón "Volver"
     # ---------- DETECTAR CLIC EN "VOLVER" ----------
        if volver_rect.collidepoint(cursor_x, cursor_y) and is_shooting:
            pygame.time.wait(0)
            return "inicio"

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(0)

    # Liberar recursos (precaución extra)
    camera_manager.release()
    cap_video.release()
fondo_config = pygame.image.load("IMG//Configuracion.png")
fondo_config = pygame.transform.scale(fondo_config, (WINDOW_WIDTH, WINDOW_HEIGHT))
font = pygame.font.SysFont("comicsans", 30)
def show_Config(camera_manager, config_manager):
    running = True
    cursor_x, cursor_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    is_shooting = False
    shooting_debounce = False

    clock = pygame.time.Clock()

    dropdown_open = False
    daltonismo_dropdown_open = False
    daltonismo_opciones = ["Ninguno", "Protanopía", "Deuteranopía", "Tritanopía"]

    def dibujar_boton(rect, texto, color_fondo=BUTTON_BG_COLOR, color_borde=BUTTON_BORDER_COLOR):
        pygame.draw.rect(screen, color_fondo, rect, border_radius=10)
        pygame.draw.rect(screen, color_borde, rect, 4, border_radius=10)
        text = font.render(texto, True, BLACK)
        screen.blit(text, text.get_rect(center=rect.center))

    def dibujar_switch(rect, estado):
        pygame.draw.rect(screen, (200, 200, 200), rect, border_radius=20)
        color = (100, 255, 100) if not estado else (255, 100, 100)
        text = "ON" if not estado else "OFF"
        knob_rect = pygame.Rect(rect.x + (rect.width - 40 if estado else 0), rect.y, 40, rect.height)
        pygame.draw.rect(screen, color, knob_rect, border_radius=20)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, rect, 2, border_radius=20)
        txt = font.render(text, True, BLACK)
        screen.blit(txt, txt.get_rect(center=rect.center))

    def dibujar_barra_volumen(rect, valor, color_relleno=(100, 200, 100)):
        pygame.draw.rect(screen, (200, 200, 200), rect, border_radius=5)
        fill = pygame.Rect(rect.x, rect.y, int(rect.width * valor), rect.height)
        pygame.draw.rect(screen, color_relleno, fill, border_radius=5)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, rect, 2, border_radius=5)
        percent = int(valor * 100)
        text = font.render(f"{percent}%", True, BLACK)
        screen.blit(text, text.get_rect(center=rect.center))

        if rect.collidepoint(cursor_x, cursor_y) and is_shooting:
            valor = (cursor_x - rect.x) / rect.width
            return max(0.0, min(1.0, valor))
        return valor

    def manejar_dropdown():
        nonlocal dropdown_open
        if not dropdown_open:
            return
        h = 40
        for i, nombre in enumerate(config_manager.canciones.keys()):
            r = pygame.Rect(boton_dropdown.x, boton_dropdown.y + (i + 1) * h, boton_dropdown.width, h)
            color = (180, 220, 255) if nombre == config_manager.musica_actual else SAVE_BG
            pygame.draw.rect(screen, color, r, border_radius=5)
            pygame.draw.rect(screen, SAVE_BORDER, r, 1, border_radius=5)
            text = font.render(nombre, True, BLACK)
            screen.blit(text, text.get_rect(center=r.center))
            if r.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
                config_manager.musica_actual = nombre
                config_manager.cargar_musica()  # Usa el método para cargar música
                dropdown_open = False

    def manejar_dropdown_daltonismo():
        nonlocal daltonismo_dropdown_open
        if not daltonismo_dropdown_open:
            return
        h = 40
        for i, nombre in enumerate(daltonismo_opciones):
            r = pygame.Rect(daltonismo_boton_rect.x, daltonismo_boton_rect.y + (i + 1) * h,
                            daltonismo_boton_rect.width, h)
            color = (180, 220, 255) if i == config_manager.daltonismo_actual else SAVE_BG
            pygame.draw.rect(screen, color, r, border_radius=5)
            pygame.draw.rect(screen, SAVE_BORDER, r, 1, border_radius=5)
            text = font.render(nombre, True, BLACK)
            screen.blit(text, text.get_rect(center=r.center))
            if r.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
                config_manager.daltonismo_actual = i
                daltonismo_dropdown_open = False

    while running:
        screen.blit(fondo_config, (0, 0))

        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
            cursor_x = max(0, min(WINDOW_WIDTH, cursor_x))
            cursor_y = max(0, min(WINDOW_HEIGHT, cursor_y))
        else:
            cursor_x, cursor_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
            is_shooting = False

        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)

        if not is_shooting:
            shooting_debounce = False

        volver_rect = pygame.Rect(WINDOW_WIDTH - 290, WINDOW_HEIGHT - 150, 120, 50)
        dibujar_boton(volver_rect, "Volver")
        if volver_rect.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
            return "inicio"

        pos_y = 100
        espacio = 40
        col1_x = screen.get_width() // 2 - 250
        col2_x = screen.get_width() // 2 + 20

        # Sección de Música
        titulo_rect = pygame.Rect(col1_x, pos_y, 200, 40)
        boton_dropdown = pygame.Rect(col2_x, pos_y, 250, 40)
        pygame.draw.rect(screen, SAVE_BG, titulo_rect, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, titulo_rect, 2, border_radius=10)
        screen.blit(font.render("Música", True, BLACK), titulo_rect.move(20, 5))
        pygame.draw.rect(screen, SAVE_BG, boton_dropdown, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, boton_dropdown, 2, border_radius=10)
        screen.blit(font.render(config_manager.musica_actual + "*", True, BLACK), boton_dropdown.move(20, 5))
        if boton_dropdown.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
            dropdown_open = not dropdown_open
            shooting_debounce = True

        pos_y += titulo_rect.height + espacio

        # Control de Pausa
        pausa_label = pygame.Rect(col1_x, pos_y, 200, 40)
        switch_rect = pygame.Rect(col2_x, pos_y, 100, 40)
        pygame.draw.rect(screen, SAVE_BG, pausa_label, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, pausa_label, 2, border_radius=10)
        screen.blit(font.render("Pausa", True, BLACK), pausa_label.move(20, 5))
        dibujar_switch(switch_rect, config_manager.musica_pausada)
        if switch_rect.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                config_manager.musica_pausada = True
            else:
                pygame.mixer.music.unpause()
                config_manager.musica_pausada = False
            shooting_debounce = True

        pos_y += switch_rect.height + espacio

        # Control de Volumen Música
        rect_vol_mus = pygame.Rect(col1_x, pos_y, 500, 25)
        screen.blit(font.render("Volumen Música:", True, BLACK), (col1_x, pos_y - 45))
        config_manager.volumen_musica = dibujar_barra_volumen(rect_vol_mus, config_manager.volumen_musica)
        pygame.mixer.music.set_volume(config_manager.volumen_musica)

        pos_y += rect_vol_mus.height + espacio

        # Control de Efectos
        efectos_label = pygame.Rect(col1_x, pos_y, 200, 40)
        switch_efectos = pygame.Rect(col2_x, pos_y, 100, 40)
        pygame.draw.rect(screen, SAVE_BG, efectos_label, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, efectos_label, 2, border_radius=10)
        screen.blit(font.render("Efectos", True, BLACK), efectos_label.move(20, 5))
        dibujar_switch(switch_efectos, config_manager.efectos_silenciados)
        if switch_efectos.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
            config_manager.efectos_silenciados = not config_manager.efectos_silenciados
            shooting_debounce = True

        pos_y += switch_efectos.height + espacio

        # Control de Volumen Efectos
        rect_vol_fx = pygame.Rect(col1_x, pos_y, 500, 25)
        screen.blit(font.render("Volumen Efectos:", True, BLACK), (col1_x, pos_y - 45))
        config_manager.volumen_efectos = dibujar_barra_volumen(rect_vol_fx, config_manager.volumen_efectos, (100, 100, 200))

        pos_y += rect_vol_fx.height + espacio

        # Control de Daltonismo
        daltonismo_label = pygame.Rect(col1_x, pos_y, 200, 40)
        daltonismo_boton_rect = pygame.Rect(col2_x, pos_y, 250, 40)
        pygame.draw.rect(screen, SAVE_BG, daltonismo_label, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, daltonismo_label, 2, border_radius=10)
        screen.blit(font.render("Daltonismo:", True, BLACK), daltonismo_label.move(20, 5))
        pygame.draw.rect(screen, SAVE_BG, daltonismo_boton_rect, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, daltonismo_boton_rect, 2, border_radius=10)
        screen.blit(font.render(daltonismo_opciones[config_manager.daltonismo_actual], True, BLACK),
                    daltonismo_boton_rect.move(20, 5))
        if daltonismo_boton_rect.collidepoint(cursor_x, cursor_y) and is_shooting and not shooting_debounce:
            daltonismo_dropdown_open = not daltonismo_dropdown_open
            shooting_debounce = True

        manejar_dropdown()
        manejar_dropdown_daltonismo()
        draw_pointer(cursor_x, cursor_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Aplicar filtro de daltonismo
        config_manager.aplicar_filtro_daltonismo(screen)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                exit()

def salir():
    pygame.quit()  # Cerramos Pygame
    sys.exit()  # Salimos del programa
def show_under_construction(screen, image_path, camera_manager, config_manager):
    pygame.font.init()
    clock = pygame.time.Clock()

    # Fuentes
    title_font = pygame.font.SysFont("arial", 36, bold=True)
    text_font = pygame.font.SysFont("arial", 20)

    # Dimensiones de la ventana
    screen_width, screen_height = screen.get_size()

    # Recuadro
    box_width = screen_width * 0.7
    box_height = screen_height * 0.6
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    padding = 20

    # Cargar imagen
    try:
        image = pygame.image.load(image_path).convert_alpha()
        max_img_width = box_width - 2 * padding
        max_img_height = box_height * 0.4
        image = scale_image(image, max_img_width, max_img_height)
    except Exception as e:
        print(f"Error al cargar la imagen: {e}")
        image = None

    # Texto
    title_surface = title_font.render("¡Estamos en construcción!", True, TEXT_COLOR)
    text_lines = [
        "Estamos trabajando para tu bienestar y diversión.",
        "Muy pronto esta área estará disponible."
    ]
    text_surfaces = [text_font.render(line, True, TEXT_COLOR) for line in text_lines]

    cursor_x, cursor_y = screen_width // 2, screen_height // 2
    background_image = pygame.image.load("IMG//fondo menu Juegos.png").convert()
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

    while True:
        clock.tick(60)
        screen.blit(background_image, (0, 0))

        # === Entrada gestual ===
        hand_data = camera_manager.get_hand_position()
        is_shooting = False
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)

        # === Dibujo superpuesto (NO se limpia pantalla) ===

        # Sombra
        shadow_offset = 6
        shadow_rect = box_rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=12)

        # Recuadro principal
        pygame.draw.rect(screen, SAVE_BG, box_rect, border_radius=10)
        pygame.draw.rect(screen, SAVE_BORDER, box_rect, width=4, border_radius=10)

        # Contenido
        current_y = box_y + padding

        # Título
        title_x = box_x + (box_width - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, current_y))
        current_y += title_surface.get_height() + 20

        # Imagen
        if image:
            img_x = box_x + (box_width - image.get_width()) // 2
            screen.blit(image, (img_x, current_y))
            current_y += image.get_height() + 20

        # Texto descriptivo
        for surface in text_surfaces:
            text_x = box_x + (box_width - surface.get_width()) // 2
            screen.blit(surface, (text_x, current_y))
            current_y += surface.get_height() + 5

        # Puntero gestual visual (opcional)
        draw_pointer(cursor_x, cursor_y, screen_width, screen_height)

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()

        # Salir si se hace clic gestual fuera del recuadro
        if hand_data and is_shooting and not box_rect.collidepoint(cursor_x, cursor_y):
            pygame.time.wait(200)
            return

        # Manejo de eventos para permitir salida segura
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

def scale_image(image, max_width, max_height):
    img_width, img_height = image.get_size()
    ratio = min(max_width / img_width, max_height / img_height)
    new_size = (int(img_width * ratio), int(img_height * ratio))
    return pygame.transform.smoothscale(image, new_size)

def draw_pointer(x, y, screen_width, screen_height):
    """Dibuja un cursor gestual visual como un pequeño círculo."""
    pygame.draw.circle(pygame.display.get_surface(), (255, 0, 0), (int(x), int(y)), 10)
def scale_image(image, max_width, max_height):
    img_width, img_height = image.get_size()
    ratio = min(max_width / img_width, max_height / img_height)
    new_size = (int(img_width * ratio), int(img_height * ratio))
    return pygame.transform.smoothscale(image, new_size)

# ----------------------------JUEGO DE PINTAR-------------------------------------------------------
# Inicializar pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
pygame.display.set_caption("Spectra Dibujo")

# Paths de imágenes
BACKGROUND_IMG = os.path.join(IMG_FOLDER, "FONDO_DIBUJAR.png")  # Fondo general
ERASE_IMG = os.path.join(IMG_FOLDER, "Borrar.png")
SAVE_IMG = os.path.join(IMG_FOLDER, "Guardar.png")
BACK_IMG = os.path.join(IMG_FOLDER, "Home.png")

# Cargar imágenes
background = pygame.image.load(BACKGROUND_IMG)
background = pygame.transform.scale(background, (screen_width, screen_height))

erase_icon = pygame.image.load(ERASE_IMG)
save_icon = pygame.image.load(SAVE_IMG)
back_icon = pygame.image.load(BACK_IMG)

# Redimensionar iconos
ICON_SIZE = (60, 60)
erase_icon = pygame.transform.scale(erase_icon, ICON_SIZE)
save_icon = pygame.transform.scale(save_icon, ICON_SIZE)
back_icon = pygame.transform.scale(back_icon, ICON_SIZE)

# Tamaño del selector de colores
COLOR_BOX_SIZE = 50

# Grosor del pincel
BRUSH_SIZE = 8

# Fuente
title_font = pygame.font.SysFont("arial", 60)
button_font = pygame.font.SysFont("arial", 40)
save_message_font = pygame.font.SysFont("arial", 30)

# Nuevo tamaño y posición para el área de dibujo
DRAWING_AREA_WIDTH = 1420
DRAWING_AREA_HEIGHT = 700
DRAWING_AREA_X = 85
DRAWING_AREA_Y = 63
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.text_color = WHITE  # Color del texto
        self.font = pygame.font.Font(None, 40)  # Inicializa la fuente en el constructor
        self.bg_color = BUTTON_BG_COLOR  # Color de fondo
        self.border_color = BUTTON_BORDER_COLOR  # Color del borde

    def draw(self, screen, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            color = (self.bg_color[0] + 20, self.bg_color[1] + 20,
                     self.bg_color[2] + 20)  # Ligera modificación al fondo para hover
        else:
            color = self.bg_color

            # Dibujar el fondo del botón con radio de borde
        pygame.draw.rect(screen, color, self.rect, border_radius=15)

        # Dibujar el borde del botón
        pygame.draw.rect(screen, self.border_color, self.rect, 4, border_radius=15)

        # Dibujar el texto centrado
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, cursor_pos, is_shooting):
        return self.rect.collidepoint(cursor_pos) and is_shooting
button_width = 300
button_height = 80
spacing = 40
menu_buttons = [
    Button(
        ((screen_width - button_width) // 2, screen_height // 3, button_width, button_height),
        "Modo Libre"
    ),
    Button(
        ((screen_width - button_width) // 2, screen_height // 3 + (button_height + spacing), button_width, button_height),
        "Modo Colorea"
    ),
    Button(
        ((screen_width - button_width) // 2, screen_height // 3 + 2 * (button_height + spacing), button_width, button_height),
        "Volver"
    )
]
def run_drawing_mode(camera_manager, config_manager):
    # Inicializar Pygame y pantalla
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Modo Libre - Spectra Dibujo")

    clock = pygame.time.Clock()
    canvas = pygame.Surface((DRAWING_AREA_WIDTH, DRAWING_AREA_HEIGHT))
    canvas.fill(WHITE)

    current_color = BLACK
    drawing = False
    save_message_timer = 0

    # Botones
    erase_button = pygame.Rect(1230, 790, 50, 50)
    save_button  = pygame.Rect(1330, 790, 50, 50)
    back_button  = pygame.Rect(1430, 790, 50, 50)

    # Colores
    color_positions = [
        (100, screen_height - COLOR_BOX_SIZE - 60),
        (205, screen_height - COLOR_BOX_SIZE - 60),
        (305, screen_height - COLOR_BOX_SIZE - 60),
        (405, screen_height - COLOR_BOX_SIZE - 60),
        (505, screen_height - COLOR_BOX_SIZE - 60),
        (605, screen_height - COLOR_BOX_SIZE - 60),
        (705, screen_height - COLOR_BOX_SIZE - 60)
    ]

    # Cursor gestual
    cursor_x, cursor_y = screen_width // 2, screen_height // 2
    is_shooting = False
    prev_shooting = False

    last_pos = None

    while True:
        # Obtener datos de la mano para cursor y gesto
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        else:
            # Si no hay datos, no disparo
            is_shooting = False
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)
        # Dibujar fondo, canvas, paleta y botones
        screen.blit(background, (0, 0))
        screen.blit(canvas, (DRAWING_AREA_X, DRAWING_AREA_Y))
        for i, (cx, cy) in enumerate(color_positions):
            pygame.draw.rect(screen, COLORS[i], (cx, cy, COLOR_BOX_SIZE, COLOR_BOX_SIZE))

        def draw_icon_button(rect, icon_img):
            if rect.collidepoint(cursor_x, cursor_y):
                scaled = pygame.transform.scale(icon_img, (60, 60))
                offset = (-5, -5)
            else:
                scaled = icon_img
                offset = (0, 0)
            screen.blit(scaled, (rect.x + offset[0], rect.y + offset[1]))

        draw_icon_button(erase_button, erase_icon)
        draw_icon_button(save_button, save_icon)
        draw_icon_button(back_button, back_icon)

        # Detectar evento de "clic" gestual
        click_event = is_shooting and not prev_shooting
        prev_shooting = is_shooting

        if click_event:
            # Priorizar botones
            if erase_button.collidepoint(cursor_x, cursor_y):
                current_color = WHITE
            elif save_button.collidepoint(cursor_x, cursor_y):
                pygame.image.save(canvas, "mi_dibujo.png")
                save_message_timer = pygame.time.get_ticks()
            elif back_button.collidepoint(cursor_x, cursor_y):
                return
            else:
                # Paleta de colores
                for i, (cx, cy) in enumerate(color_positions):
                    if pygame.Rect(cx, cy, COLOR_BOX_SIZE, COLOR_BOX_SIZE).collidepoint(cursor_x, cursor_y):
                        current_color = COLORS[i]
                        break
                else:
                    # Iniciar dibujo si clic fuera de controles
                    if (DRAWING_AREA_X <= cursor_x <= DRAWING_AREA_X + DRAWING_AREA_WIDTH and
                        DRAWING_AREA_Y <= cursor_y <= DRAWING_AREA_Y + DRAWING_AREA_HEIGHT):
                        drawing = True
                        last_pos = None

        # Dibujar mientras se mantiene el gesto
        if drawing:
            if not is_shooting:
                drawing = False
                last_pos = None
            else:
                if last_pos is None:
                    last_pos = (cursor_x, cursor_y)
                canvas_pos = (cursor_x - DRAWING_AREA_X, cursor_y - DRAWING_AREA_Y)
                pygame.draw.circle(canvas, current_color, canvas_pos, BRUSH_SIZE)

        # Mensaje guardado
        if save_message_timer and pygame.time.get_ticks() - save_message_timer < 2000:
            msg = save_message_font.render("¡Guardado!", True, BLACK)
            rect = msg.get_rect(center=(screen_width // 2, 50))
            pygame.draw.rect(screen, SAVE_BG, rect.inflate(40, 20))
            pygame.draw.rect(screen, SAVE_BORDER, rect.inflate(40, 20), 5)
            screen.blit(msg, rect)

        # Dibujar puntero gestual
        draw_pointer(cursor_x, cursor_y, 1920, 1080)

        # Eventos de sistema
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                sys.exit()

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(60)  # FPS
def main_menu_DIBUJO(camera_manager, config_manager):

    while True:
        screen.blit(background, (0, 0))

        # Obtener posición de la mano y si está "disparando"
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        else:
            cursor_x, cursor_y, is_shooting = (0, 0, False)  # Default si no se detecta
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)
        cursor_pos = (cursor_x, cursor_y)

        # Título
        title_surf = title_font.render("Spectra Dibujo", True, BLACK)
        title_rect = title_surf.get_rect(center=(screen_width // 2, screen_height // 6))
        screen.blit(title_surf, title_rect)

        # Botones
        for i, button in enumerate(menu_buttons):
            button.draw(screen, cursor_pos)
            if button.is_clicked(cursor_pos, is_shooting):
                pygame.time.wait(200)  # Pequeña pausa para evitar doble entrada
                if i == 0:
                    run_drawing_mode(camera_manager, config_manager)
                elif i == 1:
                    run_coloring_menu(camera_manager, config_manager)
                elif i == 2:
                    playing_menu(camera_manager, config_manager)

        # Dibujar el puntero virtual
        draw_pointer(cursor_x, cursor_y, 960, 540)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                sys.exit()

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
def run_coloring_menu(camera_manager, config_manager):
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    background = pygame.image.load("IMG//Colorear_menu.png")
    screen_width, screen_height = screen.get_size()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    pygame.display.set_caption("Modo Colorea - Spectra Dibujo")
    clock = pygame.time.Clock()

    # Botón Volver
    button_width, button_height = 200, 60
    back_button_rect = pygame.Rect(1200, screen_height - button_height - 50,
                                   button_width, button_height)
    back_button_font = pygame.font.Font(None, 36)

    # Miniaturas
    coloring_images_paths = [
        os.path.join(IMG_FOLDER, f"dibujo{i+1}.png") for i in range(5)
    ]
    coloring_images = [pygame.image.load(p) for p in coloring_images_paths]
    thumbnail_size = (200, 200)
    thumbnails = [pygame.transform.scale(img, thumbnail_size)
                  for img in coloring_images]
    thumbnail_positions = [(1130, 100), (330, 100), (730, 100),
                           (940, 480), (480, 480)]
    thumbnail_rects = [pygame.Rect(x, y, *thumbnail_size)
                       for x, y in thumbnail_positions]

    # Cursor gestual
    cursor_x, cursor_y = screen_width // 2, screen_height // 2
    is_shooting = False
    prev_shooting = False

    while True:
        # 1) Leer gesto
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)
        # Crear evento de clic sólo en la transición cerrado-abierto
        click_event = is_shooting and not prev_shooting
        prev_shooting = is_shooting

        # 2) Procesar eventos Pygame básicos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                sys.exit()

        # 3) Dibujar interfaz
        screen.blit(background, (0, 0))

        # Botón Volver
        back_color = HOVER if back_button_rect.collidepoint(cursor_x, cursor_y) else BUTTON_BG_COLOR
        pygame.draw.rect(screen, back_color, back_button_rect, border_radius=10)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, back_button_rect, 3, border_radius=10)
        txt = back_button_font.render("Volver", True, WHITE)
        screen.blit(txt, txt.get_rect(center=back_button_rect.center))

        # Miniaturas
        for i, rect in enumerate(thumbnail_rects):
            screen.blit(thumbnails[i], rect)
            if rect.collidepoint(cursor_x, cursor_y):
                pygame.draw.rect(screen, HOVER, rect, 5)

        # 4) Atender click_event: primero Volver, luego miniaturas
        if click_event:
            if back_button_rect.collidepoint(cursor_x, cursor_y):
                # volver al menú padre sin liberar la cámara
                return

            for i, rect in enumerate(thumbnail_rects):
                if rect.collidepoint(cursor_x, cursor_y):
                    pygame.time.wait(200)
                    run_coloring_mode(camera_manager, coloring_images_paths[i], config_manager)
                    return

        # 5) Puntero gestual
        draw_pointer(cursor_x, cursor_y, 960, 540)
        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(30)
def flood_fill(canvas, start_pos, color, mask, brush_size):
    x, y = start_pos
    width, height = canvas.get_size()
    queue = deque([(x, y)])
    visited = set()

    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) in visited:
            continue
        if not (0 <= cx < width and 0 <= cy < height):  # Fuera del canvas
            continue

        # Revisar si el punto está sobre las líneas
        if mask.get_at((cx, cy)):  # Si la máscara nos dice que es línea
            continue

        # Marcar como visitado y pintar
        visited.add((cx, cy))
        pygame.draw.circle(canvas, color, (cx, cy), brush_size)

        # Agregar los puntos vecinos a la cola para seguir rellenando
        queue.append((cx + 1, cy))
        queue.append((cx - 1, cy))
        queue.append((cx, cy + 1))
        queue.append((cx, cy - 1))
def bresenham(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points
def can_paint_area(mask, x, y, radius):
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                nx, ny = x + dx, y + dy
                if 0 <= nx < DRAWING_AREA_WIDTH and 0 <= ny < DRAWING_AREA_HEIGHT:
                    if mask.get_at((nx, ny)):
                        return False
    return True
def run_coloring_mode(camera_manager, image_path, config_manager):
    # Inicializar Pygame y pantalla
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Modo Colorear - Spectra Dibujo")

    clock = pygame.time.Clock()

    # Cargar imagen de colorear y preparar canvas
    coloring_image = pygame.image.load(image_path).convert_alpha()
    coloring_image = pygame.transform.scale(coloring_image, (DRAWING_AREA_WIDTH, DRAWING_AREA_HEIGHT))
    canvas = pygame.Surface((DRAWING_AREA_WIDTH, DRAWING_AREA_HEIGHT), pygame.SRCALPHA)
    canvas.blit(coloring_image, (0, 0))
    mask = pygame.mask.from_threshold(coloring_image, (0, 0, 0, 255), (40, 40, 40, 10))

    current_color = BLACK
    drawing = False
    save_message_timer = 0

    # Botones de acción
    erase_button = pygame.Rect(1230, 790, 50, 50)
    save_button = pygame.Rect(1330, 790, 50, 50)
    back_button = pygame.Rect(1430, 790, 50, 50)

    # Paleta de colores
    color_positions = [
        (100, screen_height - COLOR_BOX_SIZE - 60),
        (205, screen_height - COLOR_BOX_SIZE - 60),
        (305, screen_height - COLOR_BOX_SIZE - 60),
        (405, screen_height - COLOR_BOX_SIZE - 60),
        (505, screen_height - COLOR_BOX_SIZE - 60),
        (605, screen_height - COLOR_BOX_SIZE - 60),
        (705, screen_height - COLOR_BOX_SIZE - 60)
    ]

    # Cursor gestual
    cursor_x, cursor_y = screen_width // 2, screen_height // 2
    is_shooting = False
    prev_shooting = False
    last_pos = None

    # Helper para dibujar iconos
    def draw_icon_button(rect, icon_img):
        if rect.collidepoint(cursor_x, cursor_y):
            scaled = pygame.transform.scale(icon_img, (60, 60)); offset = (-5, -5)
        else:
            scaled = icon_img; offset = (0, 0)
        screen.blit(scaled, (rect.x + offset[0], rect.y + offset[1]))

    while True:
        # 1) Obtener gesto de la mano
        hand_data = camera_manager.get_hand_position()
        if hand_data:
            cursor_x, cursor_y, is_shooting = hand_data
        else:
            is_shooting = False
        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(screen, mano_detectada=True)
        # 2) Detectar click gestual (inicio de disparo)
        click_event = is_shooting and not prev_shooting
        prev_shooting = is_shooting

        # 3) Dibujar fondo y canvas
        screen.blit(background, (0, 0))
        screen.blit(canvas, (DRAWING_AREA_X, DRAWING_AREA_Y))

        # 4) Dibujar paleta de colores
        for i, (cx, cy) in enumerate(color_positions):
            pygame.draw.rect(screen, COLORS[i], (cx, cy, COLOR_BOX_SIZE, COLOR_BOX_SIZE))

        # 5) Dibujar botones
        draw_icon_button(erase_button, erase_icon)
        draw_icon_button(save_button, save_icon)
        draw_icon_button(back_button, back_icon)

        # 6) Procesar click gestual: botones primero
        if click_event:
            # Botones de acción
            if erase_button.collidepoint(cursor_x, cursor_y):
                current_color = WHITE
                click_event = False
            elif save_button.collidepoint(cursor_x, cursor_y):
                pygame.image.save(canvas, "mi_coloreo.png")
                save_message_timer = pygame.time.get_ticks()
                click_event = False
            elif back_button.collidepoint(cursor_x, cursor_y):
                return

            # Selección de color
            if click_event:
                for i, (cx, cy) in enumerate(color_positions):
                    if pygame.Rect(cx, cy, COLOR_BOX_SIZE, COLOR_BOX_SIZE).collidepoint(cursor_x, cursor_y):
                        current_color = COLORS[i]
                        click_event = False
                        break

            # Iniciar dibujo si no fue botón ni color
            if click_event:
                if (DRAWING_AREA_X <= cursor_x <= DRAWING_AREA_X + DRAWING_AREA_WIDTH and
                    DRAWING_AREA_Y <= cursor_y <= DRAWING_AREA_Y + DRAWING_AREA_HEIGHT):
                    drawing = True
                    last_pos = None

        # 7) Dibujar mientras se mantiene el gesto
        if drawing:
            if not is_shooting:
                drawing = False
                last_pos = None
            else:
                canvas_x = cursor_x - DRAWING_AREA_X
                canvas_y = cursor_y - DRAWING_AREA_Y
                if 0 <= canvas_x < DRAWING_AREA_WIDTH and 0 <= canvas_y < DRAWING_AREA_HEIGHT:
                    if last_pos is not None:
                        points = list(bresenham(last_pos[0], last_pos[1], canvas_x, canvas_y))
                        if all(can_paint_area(mask, x, y, BRUSH_SIZE) for x, y in points):
                            for x, y in points:
                                pygame.draw.circle(canvas, current_color, (x, y), BRUSH_SIZE+1)
                        else:
                            last_pos = None
                    else:
                        if can_paint_area(mask, canvas_x, canvas_y, BRUSH_SIZE):
                            pygame.draw.circle(canvas, current_color, (canvas_x, canvas_y), BRUSH_SIZE)
                    last_pos = (canvas_x, canvas_y)

        # 8) Mostrar mensaje guardado
        if save_message_timer and pygame.time.get_ticks() - save_message_timer < 2000:
            msg = save_message_font.render("¡Guardado!", True, BLACK)
            rect = msg.get_rect(center=(screen_width//2, 50))
            pygame.draw.rect(screen, SAVE_BG, rect.inflate(40,20))
            pygame.draw.rect(screen, SAVE_BORDER, rect.inflate(40,20), 5)
            screen.blit(msg, rect)

        # 9) Dibujar puntero gestual
        draw_pointer(cursor_x, cursor_y, 1920, 1080)

        # 10) Eventos de sistema
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera_manager.release(); pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        clock.tick(60)
#----------------------------------------JUEGO DE MEMORIA------------------------------------------
def ejecutar_juego_memoria(camera_manager, config_manager):
    pygame.init()
    pygame.mixer.init()

    # Cargar sonidos (sin cambios)
    try:
        sonido_match = pygame.mixer.Sound("Pistas/sonido_match.wav")
        sonido_voltear = pygame.mixer.Sound("Pistas/sonido_voltear.wav")
        sonido_ganar = pygame.mixer.Sound("Pistas/correcto.wav")
        sonido_error = pygame.mixer.Sound("Pistas/incorrecto.wav")
    except:
        sonido_match = pygame.mixer.Sound(buffer=bytearray(44))
        sonido_voltear = pygame.mixer.Sound(buffer=bytearray(44))
        sonido_ganar = pygame.mixer.Sound(buffer=bytearray(44))
        sonido_error = pygame.mixer.Sound(buffer=bytearray(44))

    # Configuración de pantalla
    pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    ANCHO_PANTALLA, ALTO_PANTALLA = pantalla.get_size()
    reloj = pygame.time.Clock()

    # Fondo original
    fondo = pygame.image.load("IMG/fondo tarjetas.png")
    fondo = pygame.transform.scale(fondo, (ANCHO_PANTALLA, ALTO_PANTALLA))

    # Fuente original
    fuente = pygame.font.SysFont(None, 48)

    # Cargar imágenes de tarjetas
    imagenes = [pygame.image.load(f"IMG/tarjeta{i}.png") for i in range(1, 7)]
    imagen_reverso = pygame.image.load("IMG/vuelta.png")
    imagenes = [pygame.transform.scale(img, (186, 186)) for img in imagenes]
    imagen_reverso = pygame.transform.scale(imagen_reverso, (186, 186))

    # Configuración inicial del juego
    imagenes_tarjetas = imagenes * 2
    random.shuffle(imagenes_tarjetas)

    puntaje = 0
    tarjetas = []
    filas, columnas = 4, 3
    ancho_tarjeta, alto_tarjeta = 186, 186
    espacio = 20
    inicio_x = 200  # Posición X original
    inicio_y = (ALTO_PANTALLA - (filas * alto_tarjeta + (filas - 1) * espacio)) // 2

    # Crear tarjetas con posiciones originales
    for fila in range(filas):
        for col in range(columnas):
            x = inicio_x + col * (ancho_tarjeta + espacio)
            y = inicio_y + fila * (alto_tarjeta + espacio)
            indice = fila * columnas + col
            tarjetas.append({
                "imagen": imagenes_tarjetas[indice],
                "rect": pygame.Rect(x, y, ancho_tarjeta, alto_tarjeta),
                "estado": "vista_previa",
                "angulo": 0,
                "escala": 1.0,
                "color_brillo": None
            })

    estado_juego = "vista_previa"
    temporizador_vista = pygame.time.get_ticks()
    seleccionadas = []
    tiempo_ultima_verificacion = None

    # Botón de volver con imagen Home.png
    try:
        boton_volver_img = pygame.image.load("IMG/Home.png")
        boton_volver_img = pygame.transform.scale(boton_volver_img, (50, 50))
    except:
        boton_volver_img = pygame.Surface((50, 50))
        boton_volver_img.fill(SAVE_BG)
        pygame.draw.rect(boton_volver_img, SAVE_BORDER, (0, 0, 50, 50), 3)

    boton_volver = pygame.Rect(ANCHO_PANTALLA - 260, ALTO_PANTALLA - 100, 200, 50)

    # Efecto de confeti para victoria
    confeti = []
    tiempo_fin_juego = 0
    mostrando_confeti = False

    while True:
        # Manejo de entrada (original)
        datos_mano = camera_manager.get_hand_position()
        if datos_mano:
            cursor_x, cursor_y, clic = datos_mano
        else:
            cursor_x, cursor_y, clic = 0, 0, False

        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(pantalla, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(pantalla, mano_detectada=True)

        evento_clic = clic

        # Dibujar fondo original
        pantalla.blit(fondo, (0, 0))

        # Animación de confeti al ganar
        if mostrando_confeti:
            ahora = pygame.time.get_ticks()
            if ahora - tiempo_fin_juego > 2000:  # Reducido a 2 segundos
                # Reiniciar juego después de la animación
                random.shuffle(imagenes_tarjetas)
                # Mezclar también las posiciones de las tarjetas
                posiciones = [t["rect"].topleft for t in tarjetas]
                random.shuffle(posiciones)

                for i, tarjeta in enumerate(tarjetas):
                    tarjeta["imagen"] = imagenes_tarjetas[i]
                    tarjeta["rect"].topleft = posiciones[i]
                    tarjeta["estado"] = "vista_previa"
                    tarjeta["angulo"] = 0
                    tarjeta["escala"] = 1.0
                    tarjeta["color_brillo"] = None

                seleccionadas.clear()
                estado_juego = "vista_previa"
                temporizador_vista = pygame.time.get_ticks()
                mostrando_confeti = False
                confeti = []
            else:
                # Generar confeti
                if random.random() < 0.3:
                    confeti.append({
                        "x": random.randint(0, ANCHO_PANTALLA),
                        "y": -10,
                        "color": (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)),
                        "size": random.randint(5, 15),
                        "speed": random.randint(3, 8),
                        "sway": random.uniform(-1, 1)
                    })

                # Dibujar confeti
                for c in confeti:
                    pygame.draw.circle(pantalla, c["color"], (int(c["x"]), int(c["y"])), c["size"])
                    c["y"] += c["speed"]
                    c["x"] += c["sway"]
                    if c["y"] > ALTO_PANTALLA:
                        confeti.remove(c)

        # Dibujar y actualizar tarjetas (con animaciones)
        for indice, tarjeta in enumerate(tarjetas):
            # Animación de volteo
            if tarjeta["estado"] == "revelada" and tarjeta["angulo"] < 90:
                tarjeta["angulo"] += 18
            elif tarjeta["estado"] == "oculta" and tarjeta["angulo"] > 0:
                tarjeta["angulo"] -= 18

            # Efecto de carta encontrada
            if tarjeta["estado"] == "encontrada" and tarjeta["escala"] < 1.1:
                tarjeta["escala"] += 0.02
                if tarjeta["color_brillo"] is None:
                    tarjeta["color_brillo"] = (random.randint(200, 255), random.randint(200, 255),
                                               random.randint(200, 255))

            # Dibujar tarjeta con animación
            if tarjeta["angulo"] == 0 or tarjeta["angulo"] == 90:
                imagen = tarjeta["imagen"] if tarjeta["estado"] in ["vista_previa", "revelada",
                                                                    "encontrada"] else imagen_reverso
                if tarjeta["escala"] != 1.0:
                    new_size = (int(ancho_tarjeta * tarjeta["escala"]), int(alto_tarjeta * tarjeta["escala"]))
                    imagen = pygame.transform.scale(imagen, new_size)
                    rect = imagen.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(imagen, rect)
                else:
                    pantalla.blit(imagen, tarjeta["rect"])
            else:
                # Animación de volteo 3D
                if tarjeta["angulo"] < 90:
                    escala = 1.0 - (tarjeta["angulo"] / 90)
                    temp_img = pygame.transform.scale(imagen_reverso, (int(ancho_tarjeta * escala), alto_tarjeta))
                    rect = temp_img.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(temp_img, rect)
                else:
                    escala = (tarjeta["angulo"] - 90) / 90
                    temp_img = pygame.transform.scale(tarjeta["imagen"], (int(ancho_tarjeta * escala), alto_tarjeta))
                    rect = temp_img.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(temp_img, rect)

            # Brillo para cartas encontradas
            if tarjeta["estado"] == "encontrada" and tarjeta["color_brillo"]:
                s = pygame.Surface((tarjeta["rect"].width, tarjeta["rect"].height), pygame.SRCALPHA)
                pygame.draw.rect(s, (*tarjeta["color_brillo"], 30),
                                 (0, 0, tarjeta["rect"].width, tarjeta["rect"].height))
                pantalla.blit(s, tarjeta["rect"].topleft)

            # Manejar clic en tarjetas
            if evento_clic and estado_juego == "jugando" and tarjeta["estado"] == "oculta":
                if tarjeta["rect"].collidepoint(cursor_x, cursor_y) and len(seleccionadas) < 2:
                    tarjeta["estado"] = "revelada"
                    seleccionadas.append(indice)
                    sonido_voltear.play()
                    evento_clic = False
                    if len(seleccionadas) == 2:
                        estado_juego = "verificando"
                        tiempo_ultima_verificacion = pygame.time.get_ticks()

        # Lógica del juego
        ahora = pygame.time.get_ticks()

        # Vista previa inicial
        if estado_juego == "vista_previa" and ahora - temporizador_vista > 3000:
            for tarjeta in tarjetas:
                tarjeta["estado"] = "oculta"
            estado_juego = "jugando"

        # Verificar parejas
        elif estado_juego == "verificando" and ahora - tiempo_ultima_verificacion > 1000:
            if tarjetas[seleccionadas[0]]["imagen"] == tarjetas[seleccionadas[1]]["imagen"]:
                tarjetas[seleccionadas[0]]["estado"] = "encontrada"
                tarjetas[seleccionadas[1]]["estado"] = "encontrada"
                puntaje += 1
                sonido_match.play()
            else:
                tarjetas[seleccionadas[0]]["estado"] = "oculta"
                tarjetas[seleccionadas[1]]["estado"] = "oculta"
                sonido_error.play()
            seleccionadas.clear()
            estado_juego = "jugando"

        # Detectar victoria
        if all(t["estado"] == "encontrada" for t in tarjetas) and not mostrando_confeti:
            sonido_ganar.play()
            tiempo_fin_juego = pygame.time.get_ticks()
            mostrando_confeti = True

        # Botón de volver (diseño original)
        pygame.draw.rect(pantalla, SAVE_BORDER, boton_volver, border_radius=10)
        pygame.draw.rect(pantalla, SAVE_BG, boton_volver.inflate(-6, -6), border_radius=10)
        if boton_volver_img:
            img_rect = boton_volver_img.get_rect(center=boton_volver.center)
            pantalla.blit(boton_volver_img, img_rect)

        # Manejar clic en botón
        if clic and boton_volver.collidepoint(cursor_x, cursor_y):
            return playing_menu(camera_manager, config_manager)

        # Puntero y puntaje
        draw_pointer(cursor_x, cursor_y, ANCHO_PANTALLA, ALTO_PANTALLA)

        # Mostrar puntaje (diseño original)
        texto_puntaje = fuente.render(f"Puntaje: {puntaje}", True, (255, 255, 255))
        fondo_puntaje = pygame.Rect(ANCHO_PANTALLA - texto_puntaje.get_width() - 70,
                                    100,
                                    texto_puntaje.get_width() + 20,
                                    texto_puntaje.get_height())
        pygame.draw.rect(pantalla, SAVE_BORDER, fondo_puntaje, border_radius=5)
        pygame.draw.rect(pantalla, SAVE_BG, fondo_puntaje.inflate(-4, -4), border_radius=5)
        pantalla.blit(texto_puntaje, (ANCHO_PANTALLA - texto_puntaje.get_width() - 60, 100))

        # Eventos del sistema
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_volver.collidepoint(evento.pos):
                    return main_menu(camera_manager)

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        reloj.tick(60)
#----------------------------------------JUEGO DE PUZZLE-------------------------------------------
def ejecutar_puzzle_animales(camera_manager, config_manager):
    pygame.init()
    pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    ANCHO, ALTO = pantalla.get_size()
    reloj = pygame.time.Clock()

    # --- Configuración Visual ---
    # Colores
    COLOR_TITULO = (255, 255, 255)  # Blanco
    COLOR_TEXTO = (255, 255, 255)  # Blanco

    # Fuentes
    fuente_titulo = pygame.font.SysFont("comicsans", 60, bold=True)
    fuente_normal = pygame.font.SysFont("comicsans", 40)

    # Cargar imágenes y sonidos
    fondo = pygame.image.load("IMG/fondo menu Juegos.png")
    fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))

    # Cargar imágenes de botones
    img_home = pygame.image.load("IMG/Home.png")
    img_home = pygame.transform.scale(img_home, (60, 60))
    img_reiniciar = pygame.image.load("IMG/reiniciar.png")
    img_reiniciar = pygame.transform.scale(img_reiniciar, (60, 60))

    # Animales y sus hábitats
    animales = {
        "pez": {"imagen": "IMG/animal_pez.png", "habitat": "agua"},
        "leon": {"imagen": "IMG/animal_leon.png", "habitat": "sabana"},
        "pinguino": {"imagen": "IMG/animal_pinguino.png", "habitat": "hielo"},
        "mono": {"imagen": "IMG/animal_mono.png", "habitat": "jungla"}
    }

    habitats = {
        "agua": {"imagen": "IMG/habitat_agua.png", "rect": None},
        "sabana": {"imagen": "IMG/habitat_sabana.png", "rect": None},
        "hielo": {"imagen": "IMG/habitat_hielo.png", "rect": None},
        "jungla": {"imagen": "IMG/habitat_jungla.png", "rect": None}
    }

    # Tamaños
    TAMANO_ANIMAL = (ANCHO // 8, ANCHO // 8)
    TAMANO_HABITAT = (ANCHO // 5, ALTO // 5)

    # Cargar imágenes
    for key in animales:
        animales[key]["imagen"] = pygame.image.load(animales[key]["imagen"])
        animales[key]["imagen"] = pygame.transform.scale(animales[key]["imagen"], TAMANO_ANIMAL)

    for key in habitats:
        habitats[key]["imagen"] = pygame.image.load(habitats[key]["imagen"])
        habitats[key]["imagen"] = pygame.transform.scale(habitats[key]["imagen"], TAMANO_HABITAT)

    # --- Posicionamiento ---
    # Título en recuadro centrado
    titulo_texto = fuente_titulo.render("¡Ayuda a cada animal a llegar a su hábitat!", True, COLOR_TITULO)
    titulo_ancho = titulo_texto.get_width() + 60
    titulo_alto = 80
    titulo_rect = pygame.Rect(ANCHO // 2 - titulo_ancho // 2, 30, titulo_ancho, titulo_alto)

    # Hábitats en posición más alta y con más espacio
    margen_horizontal = ANCHO // 12
    espacio_entre_habitats = (ANCHO - 2 * margen_horizontal - 4 * TAMANO_HABITAT[0]) // 5

    for i, (habitat_nombre, habitat) in enumerate(habitats.items()):
        x = margen_horizontal + i * (TAMANO_HABITAT[0] + espacio_entre_habitats)
        y = ALTO - TAMANO_HABITAT[1] - 150
        habitats[habitat_nombre]["rect"] = pygame.Rect(x, y, TAMANO_HABITAT[0], TAMANO_HABITAT[1])

    # Función para obtener posiciones base alineadas
    def obtener_posiciones_base():
        altura_fija = ALTO // 3
        espacio_entre_animales = (ANCHO - 4 * TAMANO_ANIMAL[0]) // 5
        posiciones = []

        for i in range(4):
            x = espacio_entre_animales + i * (TAMANO_ANIMAL[0] + espacio_entre_animales)
            y = altura_fija
            posiciones.append((x, y))

        return posiciones

    # Función para posicionar animales intercambiando sus posiciones
    def posicionar_animales():
        animales_activos = []
        posiciones_base = obtener_posiciones_base()

        # Crear lista de animales en orden aleatorio
        animales_mezclados = list(animales.items())
        random.shuffle(animales_mezclados)

        # Asignar cada animal a una posición base diferente
        for i, (animal_nombre, animal) in enumerate(animales_mezclados):
            x, y = posiciones_base[i]

            animales_activos.append({
                "tipo": animal_nombre,
                "imagen": animal["imagen"],
                "rect": pygame.Rect(x, y, TAMANO_ANIMAL[0], TAMANO_ANIMAL[1]),
                "arrastrando": False,
                "pos_original": (x, y)
            })

        return animales_activos

    # Posicionar animales inicialmente
    animales_activos = posicionar_animales()

    # Botones en parte inferior izquierda
    boton_menu = pygame.Rect(50, ALTO - 100, 70, 70)
    boton_reiniciar = pygame.Rect(140, ALTO - 100, 70, 70)

    # Recuadros de información en parte inferior derecha
    ancho_recuadros = 220
    vidas_rect = pygame.Rect(ANCHO - ancho_recuadros - 20, ALTO - 140, ancho_recuadros, 60)
    puntaje_rect = pygame.Rect(ANCHO - ancho_recuadros - 20, ALTO - 70, ancho_recuadros, 60)

    # Variables del juego
    puntaje = 0
    vidas = 3
    modo = "normal"
    tiempo_restante = 120 if modo == "contrareloj" else None
    ultimo_tiempo = pygame.time.get_ticks()
    animal_arrastrado = None
    feedback_positivo = None
    feedback_tiempo = 0

    # Sonidos
    sonido_correcto = pygame.mixer.Sound("Pistas/correcto.wav")
    sonido_incorrecto = pygame.mixer.Sound("Pistas/incorrecto.wav")

    # Bucle principal del juego
    while True:
        # Obtener datos de la mano
        datos_mano = camera_manager.get_hand_position()
        if datos_mano:
            cursor_x, cursor_y, clic = datos_mano
        else:
            cursor_x, cursor_y, clic = ANCHO // 2, ALTO // 2, False

        if camera_manager.frames_without_hand > 60:
            camera_manager.mostrar_mensaje_ayuda(pantalla, mano_detectada=False)
        else:
            camera_manager.mostrar_mensaje_ayuda(pantalla, mano_detectada=True)

        # Actualizar temporizador
        if modo == "contrareloj":
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_tiempo > 1000:
                tiempo_restante -= 1
                ultimo_tiempo = ahora
                if tiempo_restante <= 0:
                    mensaje = fuente_titulo.render("¡Tiempo terminado!", True, COLOR_TITULO)
                    pantalla.blit(mensaje, (ANCHO // 2 - mensaje.get_width() // 2, ALTO // 2))
                    pygame.display.flip()
                    pygame.time.delay(2000)
                    return

        # Dibujar fondo
        pantalla.blit(fondo, (0, 0))

        # Dibujar recuadro del título
        pygame.draw.rect(pantalla, SAVE_BG, titulo_rect, border_radius=15)
        pygame.draw.rect(pantalla, SAVE_BORDER, titulo_rect, 3, border_radius=15)
        pantalla.blit(titulo_texto, (titulo_rect.x + titulo_rect.width // 2 - titulo_texto.get_width() // 2,
                                     titulo_rect.y + titulo_rect.height // 2 - titulo_texto.get_height() // 2))

        # Dibujar habitats
        for habitat in habitats.values():
            pantalla.blit(habitat["imagen"], habitat["rect"])

        # Dibujar animales
        for animal in animales_activos:
            if animal["arrastrando"]:
                sombra = pygame.Surface(TAMANO_ANIMAL, pygame.SRCALPHA)
                sombra.fill((0, 0, 0, 100))
                pantalla.blit(sombra, (animal["rect"].x + 5, animal["rect"].y + 5))

            pantalla.blit(animal["imagen"], animal["rect"])

            if animal["arrastrando"]:
                animal["rect"].x = cursor_x - TAMANO_ANIMAL[0] // 2
                animal["rect"].y = cursor_y - TAMANO_ANIMAL[1] // 2

        # Manejar clic gestual
        if clic:
            if animal_arrastrado is None:
                for animal in animales_activos:
                    if animal["rect"].collidepoint(cursor_x, cursor_y):
                        animal["arrastrando"] = True
                        animal_arrastrado = animal
                        break

            # Verificar botones
            if boton_menu.collidepoint(cursor_x, cursor_y):
                return playing_menu(camera_manager, config_manager)
            elif boton_reiniciar.collidepoint(cursor_x, cursor_y):
                # Reiniciar mezclando las posiciones de los animales
                animales_activos = posicionar_animales()
                puntaje = 0
                vidas = 3
        else:
            # Soltar animal
            if animal_arrastrado is not None:
                animal_arrastrado["arrastrando"] = False

                # Verificar si se soltó en un habitat
                emparejado = False
                for habitat_nombre, habitat in habitats.items():
                    if habitat["rect"].collidepoint(cursor_x, cursor_y):
                        if animales[animal_arrastrado["tipo"]]["habitat"] == habitat_nombre:
                            # !Correcto!
                            puntaje += 10
                            sonido_correcto.play()
                            feedback_positivo = "¡Correcto!"
                            feedback_tiempo = pygame.time.get_ticks()
                            animales_activos.remove(animal_arrastrado)
                            emparejado = True

                            if not animales_activos:
                                # 1. Preparación inicial
                                sonido_correcto.play()  # Asegúrate de tener este sonido configurado
                                tiempo_inicio = pygame.time.get_ticks()
                                duracion_animacion = 3000  # 3 segundos de animación

                                # Efectos especiales
                                particulas = []
                                brillo_actual = 0
                                direccion_brillo = 1

                                # 2. Bucle de animación épica
                                while pygame.time.get_ticks() - tiempo_inicio < duracion_animacion:
                                    # Manejo de eventos
                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            camera_manager.release()
                                            pygame.quit()
                                            sys.exit()

                                    # Limpiar pantalla
                                    pantalla.blit(fondo, (0, 0))

                                    # Dibujar animales (aunque ya estén emparejados)
                                    for animal in animales_activos:
                                        pantalla.blit(animal["imagen"], animal["rect"])

                                    # --- EFECTOS ESPECIALES WOW ---
                                    # 1. Mensaje con efecto de aparición
                                    progreso = min(1.0, (pygame.time.get_ticks() - tiempo_inicio) / duracion_animacion)

                                    # Texto principal con efecto de zoom
                                    tam_texto = int(60 + 40 * math.sin(progreso * 10))
                                    fuente_animada = pygame.font.SysFont("comicsans", tam_texto, bold=True)
                                    mensaje = fuente_animada.render("¡VICTORIA!", True, (255, 255, 255))
                                    sombra = fuente_animada.render("¡VICTORIA!", True, (0, 0, 0))

                                    # Posición con ligero movimiento
                                    pos_x = ANCHO // 2 - mensaje.get_width() // 2
                                    pos_y = ALTO // 3 + 10 * math.sin(progreso * 15)

                                    # Dibujar sombra y texto
                                    pantalla.blit(sombra, (pos_x + 3, pos_y + 3))
                                    pantalla.blit(mensaje, (pos_x, pos_y))

                                    # 2. Efecto de brillo pulsante
                                    brillo_actual += 0.05 * direccion_brillo
                                    if brillo_actual > 1.0 or brillo_actual < 0:
                                        direccion_brillo *= -1

                                    capa_brillo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                                    capa_brillo.fill((255, 255, 255, int(30 * brillo_actual)))
                                    pantalla.blit(capa_brillo, (0, 0))

                                    # 3. Lluvia de confeti
                                    if random.random() < 0.3:
                                        particulas.append({
                                            "x": random.randint(0, ANCHO),
                                            "y": -10,
                                            "color": (random.randint(50, 255), random.randint(50, 255),
                                                      random.randint(50, 255)),
                                            "size": random.randint(5, 15),
                                            "speed": random.randint(3, 10),
                                            "sway": random.uniform(-2, 2)
                                        })

                                    for p in particulas[:]:
                                        pygame.draw.circle(pantalla, p["color"], (int(p["x"]), int(p["y"])), p["size"])
                                        p["y"] += p["speed"]
                                        p["x"] += p["sway"]
                                        if p["y"] > ALTO:
                                            particulas.remove(p)

                                    # 4. Destello final
                                    if progreso > 0.9:
                                        destello = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                                        intensidad = int(200 * (progreso - 0.9) * 10)
                                        destello.fill((255, 255, 255, intensidad))
                                        pantalla.blit(destello, (0, 0))

                                    # --- APLICAR FILTRO DE DALTONISMO ---
                                    config_manager.aplicar_filtro_daltonismo(pantalla)

                                    pygame.display.flip()
                                    reloj.tick(60)

                                # 3. Pantalla final de victoria
                                tiempo_inicio = pygame.time.get_ticks()
                                while pygame.time.get_ticks() - tiempo_inicio < 2000:  # 2 segundos
                                    # Dibujar fondo y elementos
                                    pantalla.blit(fondo, (0, 0))
                                    for animal in animales_activos:
                                        pantalla.blit(animal["imagen"], animal["rect"])

                                    # Mensaje final centrado
                                    mensaje_final = fuente_titulo.render("¡NIVEL COMPLETADO!", True, (255, 255, 255))
                                    pantalla.blit(mensaje_final,
                                                  (ANCHO // 2 - mensaje_final.get_width() // 2, ALTO // 2))

                                    # Aplicar filtro
                                    config_manager.aplicar_filtro_daltonismo(pantalla)

                                    pygame.display.flip()
                                    reloj.tick(60)

                                return
                        else:
                            # Incorrecto
                            puntaje = max(0, puntaje - 5)
                            vidas -= 1
                            sonido_incorrecto.play()
                            feedback_positivo = "Intenta de nuevo"
                            feedback_tiempo = pygame.time.get_ticks()

                            if vidas <= 0:
                                mensaje = fuente_titulo.render("¡Se acabaron las vidas!", True, COLOR_TITULO)
                                pantalla.blit(mensaje, (ANCHO // 2 - mensaje.get_width() // 2, ALTO // 2))
                                pygame.display.flip()
                                pygame.time.delay(2000)
                                return

                if not emparejado:
                    # Regresar a posición original
                    animal_arrastrado["rect"].x = animal_arrastrado["pos_original"][0]
                    animal_arrastrado["rect"].y = animal_arrastrado["pos_original"][1]

                animal_arrastrado = None

        # Mostrar feedback
        if feedback_positivo and pygame.time.get_ticks() - feedback_tiempo < 1000:
            texto = fuente_titulo.render(feedback_positivo, True, COLOR_TITULO)
            pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, ALTO // 2 - 100))

        # Dibujar recuadro de vidas
        pygame.draw.rect(pantalla, SAVE_BG, vidas_rect, border_radius=15)
        pygame.draw.rect(pantalla, SAVE_BORDER, vidas_rect, 3, border_radius=15)
        texto_vidas = fuente_normal.render(f"Vidas: {vidas}/3", True, COLOR_TEXTO)
        pantalla.blit(texto_vidas, (vidas_rect.x + vidas_rect.width // 2 - texto_vidas.get_width() // 2,
                                    vidas_rect.y + vidas_rect.height // 2 - texto_vidas.get_height() // 2))

        # Dibujar recuadro de puntaje
        pygame.draw.rect(pantalla, SAVE_BG, puntaje_rect, border_radius=15)
        pygame.draw.rect(pantalla, SAVE_BORDER, puntaje_rect, 3, border_radius=15)
        texto_puntaje = fuente_normal.render(f"Puntos: {puntaje}", True, COLOR_TEXTO)
        pantalla.blit(texto_puntaje, (puntaje_rect.x + puntaje_rect.width // 2 - texto_puntaje.get_width() // 2,
                                      puntaje_rect.y + puntaje_rect.height // 2 - texto_puntaje.get_height() // 2))

        # Dibujar botones con imágenes
        pygame.draw.rect(pantalla, SAVE_BG, boton_menu, border_radius=15)
        pygame.draw.rect(pantalla, SAVE_BORDER, boton_menu, 3, border_radius=15)
        pantalla.blit(img_home, (boton_menu.x + boton_menu.width // 2 - img_home.get_width() // 2,
                                 boton_menu.y + boton_menu.height // 2 - img_home.get_height() // 2))

        pygame.draw.rect(pantalla, SAVE_BG, boton_reiniciar, border_radius=15)
        pygame.draw.rect(pantalla, SAVE_BORDER, boton_reiniciar, 3, border_radius=15)
        pantalla.blit(img_reiniciar, (boton_reiniciar.x + boton_reiniciar.width // 2 - img_reiniciar.get_width() // 2,
                                      boton_reiniciar.y + boton_reiniciar.height // 2 - img_reiniciar.get_height() // 2))

        # Dibujar puntero
        draw_pointer(cursor_x, cursor_y, ANCHO, ALTO)

        # Eventos del sistema
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                camera_manager.release()
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return

        # Aplicar filtro de daltonismo si está activo
        config_manager.aplicar_filtro_daltonismo(screen)
        pygame.display.flip()
        reloj.tick(60)
if __name__ == "__main__":
    mp_hands = mp.solutions.hands

    camera_manager = CameraManager()  # Crear CameraManager una sola vez
    config_manager=ConfigManager()
    action = main_menu(camera_manager, config_manager)  # Entrar al menú pasando la cámara

    if action == "jugar":
        main(camera_manager, config_manager)  # Pasar el mismo camera_manager a main
    else:
        camera_manager.release()  # Liberar solo si ya no vas a usar más la cámara


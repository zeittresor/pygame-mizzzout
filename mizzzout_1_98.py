# Version 1.98 - Mizzzout v1.98beta by github.com/zeittresor

import pygame
import random
import logging
import sys
from datetime import datetime
import traceback
import os
from PIL import Image, ImageDraw
import tkinter
from tkinter import messagebox

# Prüfe auf die Cheat-Codes und den -dev Parameter
dev_mode = '-dev' in sys.argv
cheat_funds = '-cheat-FUNDS' in sys.argv

# Handle '-version' command line parameter
if '-version' in sys.argv:
    root = tkinter.Tk()
    root.withdraw()  # Verstecke das Hauptfenster
    messagebox.showinfo("Version Information", "Mizzzout by zeittresor.de / 05-2025 / v1.98")
    root.destroy()
    sys.exit()

# Initialisiere Logging
if dev_mode:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('game_log.txt'),
            logging.StreamHandler(sys.stdout)
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Initialisiere pygame
pygame.init()
pygame.joystick.init()

# Joystick initialisieren
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    logging.info(f"Joystick detected: {joystick.get_name()}")
else:
    logging.info("No joystick detected.")

# Erhalte die Bildschirmdimensionen
infoObject = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = infoObject.current_w, infoObject.current_h

# Frames per second
FPS = 60

# Initialisiere den Bildschirm im Vollbildmodus
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Car Game")

# Mauszeiger ausblenden
pygame.mouse.set_visible(False)

# Farben definieren
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Pfade zu den Bildern
IMG_PATH = "images"
SCALED_PREFIX_SMALL = "kleiner"
SCALED_PREFIX_LARGE = "groesser"

# Spielerautogröße
PLAYER_CAR_SIZE = (150, 150)

# Skalierungsfaktoren und Größen für die entgegenkommenden Autos
MIN_CAR_SIZE_FACTOR = 0.3
MAX_CAR_SIZE_FACTOR = 1.2
SCALE_FACTORS = [i / 10.0 for i in range(3, 13)]  # 0.3 bis 1.2
CAR_SIZES = [(int(PLAYER_CAR_SIZE[0] * factor), int(PLAYER_CAR_SIZE[1] * factor)) for factor in SCALE_FACTORS]

# Neue Größenkategorien für besondere Effekte
SMALL_CAR_SIZE = (256, 256)
MEDIUM_CAR_SIZE = (385, 385)
LARGE_CAR_SIZE = (512, 512)

# Funktion zum Generieren von Platzhalterbildern
def create_placeholder_image(path, size=(256, 256), color=(255, 0, 0)):
    try:
        image = Image.new('RGBA', size, color)
        draw = ImageDraw.Draw(image)
        draw.ellipse([(0, 0), size], fill=color)  # Kreis zeichnen
        image.save(path)
        logging.info(f"Created placeholder image at {path}")
    except Exception as e:
        logging.error(f"Failed to create placeholder image at {path}: {e}")

# Funktion zum Laden von Bildern
def load_image(path, size=None, use_scaled=True, is_big_car=False, force_scale=False, maintain_aspect_ratio=True):
    if use_scaled and size:
        # Bestimme, ob das Bild vergrößert oder verkleinert wird
        # Lade die Originalgröße des Bildes
        if os.path.exists(path):
            try:
                original_image = Image.open(path)
                original_size = original_image.size
            except Exception as e:
                logging.error(f"Failed to open image {path} to get size: {e}")
                original_size = None
        else:
            logging.warning(f"Original image {path} not found.")
            original_size = None

        # Adjust size to maintain aspect ratio if needed
        if maintain_aspect_ratio and original_size:
            original_width, original_height = original_size
            target_width, target_height = size
            original_ratio = original_width / original_height
            target_ratio = target_width / target_height

            if original_ratio > target_ratio:
                # Breite begrenzt
                new_width = target_width
                new_height = int(target_width / original_ratio)
            else:
                # Höhe begrenzt
                new_height = target_height
                new_width = int(target_height * original_ratio)
            size = (new_width, new_height)

        # Bestimme, ob das Bild vergrößert oder verkleinert wird
        if original_size and (size[0] > original_size[0] or size[1] > original_size[1]):
            # Bild wird vergrößert
            scale_prefix = SCALED_PREFIX_LARGE
        else:
            # Bild wird verkleinert oder gleich groß
            scale_prefix = SCALED_PREFIX_SMALL

        # Skalierter Dateiname basierend auf gewünschter Größe
        directory, filename = os.path.split(path)
        scaled_filename = f"{scale_prefix}_{size[0]}x{size[1]}_{filename}"
        scaled_path = os.path.join(directory, scaled_filename)

        if not os.path.exists(scaled_path) or force_scale:
            # Skaliertes Bild erstellen
            if original_size:
                try:
                    original_image = original_image.convert("RGBA")
                    scaled_image = original_image.resize(size, Image.LANCZOS)
                    scaled_image.save(scaled_path)
                    logging.info(f"Created scaled image at {scaled_path}")
                except Exception as e:
                    logging.error(f"Failed to create scaled image at {scaled_path}: {e}")
                    create_placeholder_image(scaled_path, size=size)
            else:
                # Originalbild fehlt oder konnte nicht geladen werden
                logging.warning(f"Original image {path} not found or could not be loaded.")
                create_placeholder_image(scaled_path, size=size)

        # Lade das skalierte Bild
        try:
            image = pygame.image.load(scaled_path).convert_alpha()
            logging.debug(f"Loaded scaled image: {scaled_path}")
            return image
        except Exception as e:
            logging.error(f"Failed to load scaled image {scaled_path}: {e}")
            return None
    else:
        # Verwende Originalbild
        if not os.path.exists(path):
            # Originalbild fehlt, Platzhalterbild erstellen
            logging.warning(f"Original image {path} not found.")
            create_placeholder_image(path)
        try:
            image = pygame.image.load(path).convert_alpha()
            if size and not is_big_car:
                # Adjust size to maintain aspect ratio if needed
                if maintain_aspect_ratio:
                    original_size = image.get_size()
                    original_width, original_height = original_size
                    target_width, target_height = size
                    original_ratio = original_width / original_height
                    target_ratio = target_width / target_height

                    if original_ratio > target_ratio:
                        # Breite begrenzt
                        new_width = target_width
                        new_height = int(target_width / original_ratio)
                    else:
                        # Höhe begrenzt
                        new_height = target_height
                        new_width = int(target_height * original_ratio)
                    size = (new_width, new_height)
                image = pygame.transform.smoothscale(image, size)
            logging.debug(f"Loaded image: {path}")
            return image
        except Exception as e:
            logging.error(f"Failed to load image {path}: {e}")
            return None

# Funktion zum Generieren der skalierten Bilder für alle Autos und Größen
def generate_scaled_images(car_image_paths):
    for path in car_image_paths:
        for size in CAR_SIZES:
            load_image(path, size=size, use_scaled=True)
    logging.info("All scaled images generated.")

# Funktion zum Laden der Bilder für die Autos
def load_car_images():
    car_images = []
    for i in range(1, 11):
        path = f"{IMG_PATH}/car{i}.png"
        if os.path.exists(path):
            car_images.append(path)
        else:
            # Platzhalterbild erstellen
            create_placeholder_image(path)
            car_images.append(path)
    return car_images

# Funktion zum Laden der Blocker-Bilder
def load_blocker_images():
    blocker_images = []
    for i in range(1, 6):
        path = f"{IMG_PATH}/blocker{i}.png"
        if os.path.exists(path):
            blocker_images.append(path)
        else:
            logging.info(f"Blocker image {path} not found. Skipping.")
    return blocker_images

# Explosion Bild laden
EXPLOSION_IMAGE = f"{IMG_PATH}/explosion.png"
explosion_image_original = load_image(EXPLOSION_IMAGE)
if explosion_image_original is None:
    logging.error("Failed to load explosion image.")

# Funktion zum Laden des Hintergrundbildes
BACKGROUND_IMAGE = f"{IMG_PATH}/scrolling_bg.png"
background_tile = load_image(BACKGROUND_IMAGE)
if background_tile is None:
    logging.error("Failed to load background tile.")

# Pfade zu den anderen Bildern
PLAYER_CAR = f"{IMG_PATH}/player_car.png"
TITLE_BACKGROUND_IMAGE = f"{IMG_PATH}/title_background.png"
TITLE_IMAGES = [f"{IMG_PATH}/title{i}.png" for i in range(1, 11)]
LOGO_IMAGE = f"{IMG_PATH}/logo.png"
BULLET_IMAGE = f"{IMG_PATH}/bullet.png"

# Klassen für Autos, Explosionen und Schüsse
class GameObject:
    def __init__(self, image, rect, mask):
        self.image = image
        self.rect = rect
        self.mask = mask

class Car(GameObject):
    def __init__(self, image, rect, mask, speed):
        super().__init__(image, rect, mask)
        self.speed = speed
        self.angle = 0  # Aktueller Winkel
        self.target_angle = 0  # Zielwinkel
        self.rotation_speed = 2  # Geschwindigkeit der Winkeländerung
        self.original_image = image  # Originalbild für die Rotation
        self.rotated_images = self.pre_rotate_images()  # Vorgerenderte Bilder
        self.size_category = self.determine_size_category()

    def pre_rotate_images(self):
        rotated_images = {}
        for angle in range(-15, 16, 5):  # Von -15° bis 15° in 5°-Schritten
            rotated_image = pygame.transform.rotate(self.original_image, angle)
            rotated_images[angle] = rotated_image
        return rotated_images

    def update_angle(self):
        if self.angle < self.target_angle:
            self.angle = min(self.angle + self.rotation_speed, self.target_angle)
        elif self.angle > self.target_angle:
            self.angle = max(self.angle - self.rotation_speed, self.target_angle)
        # Verwende das vorgerenderte Bild
        closest_angle = 5 * round(self.angle / 5)
        self.image = self.rotated_images.get(closest_angle, self.original_image)
        # Maske und Rect aktualisieren
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.rect.center)

    def determine_size_category(self):
        width, height = self.rect.size
        max_dimension = max(width, height)
        if 256 <= max_dimension <= 384:
            return 'medium'
        elif 385 <= max_dimension <= 511:
            return 'large'
        elif max_dimension >= 512:
            return 'extra_large'
        else:
            return 'small'

class Blocker(GameObject):
    def __init__(self, image, rect, mask, original_image_path):
        super().__init__(image, rect, mask)
        self.original_image_path = original_image_path
        self.state = 0  # 0: Original, 1: Erstes Ausweichen, 2: Zerstört
        self.spawn_time = pygame.time.get_ticks()
        self.cars_that_triggered = []  # Liste von Autos, die bereits den Blocker ausgelöst haben

    def update_state(self, triggering_car=None, force_change=False):
        current_time = pygame.time.get_ticks()
        # 2-Sekunden-Sperre prüfen
        if not force_change and current_time - self.spawn_time < 2000:
            return  # Noch in der Sperrzeit, keine Änderung

        # Prüfen, ob das auslösende Auto bereits den Blocker verändert hat
        if triggering_car and triggering_car in self.cars_that_triggered:
            return  # Dieses Auto hat bereits den Blocker beeinflusst

        if triggering_car:
            self.cars_that_triggered.append(triggering_car)

        if self.state == 0:
            # Versuche, die 'b'-Version zu laden
            base_name = os.path.basename(self.original_image_path)
            directory = os.path.dirname(self.original_image_path)
            name, ext = os.path.splitext(base_name)
            new_image_path = os.path.join(directory, f"{name}b{ext}")
            if os.path.exists(new_image_path):
                new_image = load_image(new_image_path, use_scaled=False)
                if new_image:
                    self.image = new_image
                    self.mask = pygame.mask.from_surface(self.image)
                    self.state = 1
                    logging.info(f"Blocker at {self.rect.topleft} changed to state 1.")
                    # Spiele entsprechenden Sound
                    sound_path = f"sounds/{name}.wav"
                    sound = load_sound(sound_path)
                    if sound:
                        sound.play()
                else:
                    logging.info(f"Blocker 'b' image {new_image_path} failed to load.")
            else:
                logging.info(f"Blocker 'b' image {new_image_path} not found.")
        elif self.state == 1:
            # Blocker wird zerstört
            self.state = 2
            logging.info(f"Blocker at {self.rect.topleft} destroyed.")
            # Spiele entsprechenden Sound
            base_name = os.path.basename(self.original_image_path)
            name, ext = os.path.splitext(base_name)
            sound_path = f"sounds/{name}b.wav"
            sound = load_sound(sound_path)
            if sound:
                sound.play()
        # Wenn state == 2, wird der Blocker entfernt (behandeln wir außerhalb dieser Funktion)

class Explosion(GameObject):
    def __init__(self, image, rect, duration):
        super().__init__(image, rect, None)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration  # in milliseconds
        self.alpha = 255

    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            return False  # Explosion ist vorbei
        else:
            # Alpha-Wert reduzieren
            self.alpha = 255 - int((elapsed / self.duration) * 255)
            return True

class Bullet(GameObject):
    def __init__(self, image, rect, speed):
        super().__init__(image, rect, pygame.mask.from_surface(image))
        self.speed = speed

    def update(self):
        self.rect.y -= self.speed  # Bewegt sich nach oben
        if self.rect.bottom < 0:
            return False  # Außerhalb des Bildschirms
        return True

# Musik und Geräusche laden
def load_sound(path):
    if not os.path.exists(path):
        logging.warning(f"Audio file {path} not found.")
        return None
    try:
        sound = pygame.mixer.Sound(path)
        logging.info(f"Sound loaded: {path}")
        return sound
    except pygame.error as e:
        logging.error(f"Failed to load sound {path}: {e}")
        return None

def load_music(path):
    if not os.path.exists(path):
        logging.warning(f"Music file {path} not found.")
        return False
    try:
        pygame.mixer.music.load(path)
        logging.info(f"Music loaded: {path}")
        return True
    except pygame.error as e:
        logging.error(f"Failed to load music {path}: {e}")
        return False

# Pfade zu den Audiodateien
TITLE_MUSIC = "sounds/title_music.mp3"
GAME_MUSIC = "sounds/game_music.mp3"
COLLISION_SOUND = "sounds/collision_sound.wav"
DAMAGE_SOUND = "sounds/damage_sound.wav"
HEAL_SOUND = "sounds/heal_sound.wav"
SHOOT_SOUND = "sounds/shoot_sound.wav"

# Audio Warnungen
missing_audio_messages = []

# Titelmusik laden
if load_music(TITLE_MUSIC):
    pygame.mixer.music.play(-1)  # Endlosschleife
else:
    missing_audio_messages.append(f"Audiodatei {TITLE_MUSIC} fehlt.")
    logging.info(f"Title music {TITLE_MUSIC} missing.")

# Soundeffekte laden
collision_sound = load_sound(COLLISION_SOUND)
if collision_sound is None:
    missing_audio_messages.append(f"Audiodatei {COLLISION_SOUND} fehlt.")

damage_sound = load_sound(DAMAGE_SOUND)
if damage_sound is None:
    missing_audio_messages.append(f"Audiodatei {DAMAGE_SOUND} fehlt.")

heal_sound = load_sound(HEAL_SOUND)
if heal_sound is None:
    missing_audio_messages.append(f"Audiodatei {HEAL_SOUND} fehlt.")

shoot_sound = load_sound(SHOOT_SOUND)
if shoot_sound is None:
    missing_audio_messages.append(f"Audiodatei {SHOOT_SOUND} fehlt.")

# Variablen für den Zustand
game_running = True
game_active = False
damage = 0
initial_max_damage = 3  # Initialer Maximalwert für Schaden
max_damage = initial_max_damage
cars = []
blockers = []
explosions = []
bullets = []
player_car = None
bg_y = 0

# Neue Variablen für die Erhöhung der Autos über die Zeit
spawn_interval = 2000  # Start-Spawn-Intervall in Millisekunden
min_spawn_interval = 500  # Minimales Spawn-Intervall
spawn_interval_decrease = 100  # Verringerung des Spawn-Intervalls über die Zeit
last_spawn_time = pygame.time.get_ticks()
spawn_interval_decrease_time = 5000  # Alle 5 Sekunden das Spawn-Intervall verringern
last_spawn_interval_decrease_time = pygame.time.get_ticks()

max_cars_on_screen = 10  # Startwert für maximale Anzahl von Autos auf dem Bildschirm
max_cars_increase_interval = 5000  # Alle 5 Sekunden die maximale Anzahl erhöhen
last_max_cars_increase_time = pygame.time.get_ticks()
max_cars_increment = 2  # Anzahl der Autos, um die die maximale Anzahl erhöht wird

# Neue Variable für Anzahl der Autos pro Spawn
cars_per_spawn = 1  # Startwert für Anzahl der Autos pro Spawn
max_cars_per_spawn = 5  # Maximale Anzahl der Autos pro Spawn
cars_per_spawn_increase_interval = 5000  # Alle 5 Sekunden Anzahl erhöhen
last_cars_per_spawn_increase_time = pygame.time.get_ticks()

# Variablen für Schadensreduzierung
damage_reduction_interval = 60000  # Alle 60 Sekunden Schaden reduzieren
last_damage_reduction_time = pygame.time.get_ticks()

# Variablen für das große Auto
big_car_interval = 25000  # Alle 25 Sekunden
last_big_car_time = pygame.time.get_ticks()
big_car_active = False
big_car = None

# Variablen für den Massenspawn
mass_spawn_interval = 45000  # Alle 45 Sekunden
last_mass_spawn_time = pygame.time.get_ticks()
mass_spawn_active = False

# Variablen für Blocker
blocker_spawn_interval = 5000  # Alle 5 Sekunden
last_blocker_spawn_time = pygame.time.get_ticks()

# Variablen für Unverwundbarkeit nach Zerstörung des großen Autos
invincible = False
invincible_start_time = 0
invincible_duration = 5000  # 5 Sekunden
invincible_color = WHITE
invincible_blink = False

# Titelbild Variablen
title_image_index = 0
last_title_switch = pygame.time.get_ticks()
title_blend_time = 4000  # Zeit (in ms) zwischen Überblendungen

# Highscore-Variablen
high_scores = []
last_score = None
HIGH_SCORE_FILE = "high_scores.txt"

# Hintergrund-Farbwechsel
bg_color_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
bg_color_overlay.set_alpha(0)
current_color = [0, 0, 0]
target_color = [0, 0, 0]
color_change_interval = 30000  # Alle 30 Sekunden die Farbe wechseln
last_color_change_time = pygame.time.get_ticks()

# Spielende Explosion
game_over_explosion = False
game_over_time = 0

# Hervorhebung des Schadenszählers
damage_highlight_duration = 1000  # 1 Sekunde
damage_highlight_start = None

# Neue Variable, um anzuzeigen, wann das Spiel neu gestartet werden kann
ready_to_restart = True

# Funktion zum Laden der Highscores
def load_high_scores():
    global high_scores
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                time_str, date_str = line.strip().split(" | ")
                high_scores.append((int(time_str), date_str))
        logging.info("High scores loaded.")
    except FileNotFoundError:
        logging.info("High score file not found. Creating a new one.")
        high_scores = []

# Funktion zum Speichern der Highscores
def save_high_scores():
    global high_scores
    with open(HIGH_SCORE_FILE, "w") as f:
        for score, date_str in high_scores:
            f.write(f"{score} | {date_str}\n")
    logging.info("High scores saved.")

# Funktion zum Aktualisieren der Highscores
def update_high_scores(survival_time):
    global high_scores, last_score
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_score = (survival_time, date_str)
    high_scores.append(new_score)
    high_scores.sort(reverse=True, key=lambda x: x[0])  # Sortiere nach Überlebenszeit absteigend
    high_scores = high_scores[:5]  # Nur die Top 5 behalten
    last_score = new_score if new_score in high_scores else None
    save_high_scores()

# Funktion für den Hintergrund-Farbwechsel
def update_background_color():
    global current_color, target_color, last_color_change_time
    current_time = pygame.time.get_ticks()
    time_since_last_color_change = current_time - last_color_change_time

    # Wenn 30 Sekunden vergangen sind, neue Ziel-Farbe setzen
    if time_since_last_color_change >= color_change_interval:
        target_color = [random.randint(0, 255) for _ in range(3)]
        last_color_change_time = current_time
        logging.info(f"Changing background color to: {target_color}")

    # Sanfter Übergang zur Ziel-Farbe
    transition_speed = 1  # Je höher, desto schneller der Übergang
    for i in range(3):
        if current_color[i] < target_color[i]:
            current_color[i] = min(current_color[i] + transition_speed, target_color[i])
        elif current_color[i] > target_color[i]:
            current_color[i] = max(current_color[i] - transition_speed, target_color[i])

    bg_color_overlay.fill(current_color)
    bg_color_overlay.set_alpha(100)  # Transparenz einstellen

# Funktion zum Scrollen des Hintergrunds
def scroll_background(bg_y):
    if background_tile is None:
        logging.error("Background tile not loaded.")
        return bg_y  # Kein Scrollen möglich

    tile_width = background_tile.get_width()
    tile_height = background_tile.get_height()

    bg_y += 1  # Scrollgeschwindigkeit anpassen (positiv für Scrollen von unten nach oben)

    # Y-Position für das Scrollen berechnen
    y_offset = bg_y % tile_height

    # Hintergrund kacheln
    for y in range(-tile_height, SCREEN_HEIGHT + tile_height, tile_height):
        for x in range(0, SCREEN_WIDTH + tile_width, tile_width):
            screen.blit(background_tile, (x, y + y_offset))

    # Farbüberlagerung anwenden
    update_background_color()
    screen.blit(bg_color_overlay, (0, 0))

    return bg_y

# Funktion zum Spawnen neuer Autos
def spawn_car(cars, car_images, y_position=-100):
    size = random.choice(CAR_SIZES)
    car_image_path = random.choice(car_images)
    car_image = load_image(car_image_path, size=size)
    if car_image is None:
        logging.error(f"Failed to spawn car, image not loaded: {car_image_path}")
        return

    car_rect = car_image.get_rect(midtop=(random.randint(50, SCREEN_WIDTH - 50), y_position))

    # Maske erstellen
    car_mask = pygame.mask.from_surface(car_image)

    # Zufällige Geschwindigkeit der Autos
    car_speed = random.randint(3, 7)
    car = Car(car_image, car_rect, car_mask, car_speed)
    car.original_image = car_image
    car.rotated_images = car.pre_rotate_images()
    cars.append(car)
    logging.debug(f"Spawned car at position: {car_rect.topleft} with speed: {car_speed}")

# Funktion zum Spawnen neuer Blocker
def spawn_blocker(blockers, blocker_images, y_position=-100):
    blocker_image_path = random.choice(blocker_images)
    blocker_image = load_image(blocker_image_path, use_scaled=False)  # Originalgröße
    if blocker_image is None:
        logging.error(f"Failed to spawn blocker, image not loaded: {blocker_image_path}")
        return
    blocker_rect = blocker_image.get_rect(midtop=(random.randint(50, SCREEN_WIDTH - 50), y_position))
    blocker_mask = pygame.mask.from_surface(blocker_image)
    blocker = Blocker(blocker_image, blocker_rect, blocker_mask, blocker_image_path)
    blockers.append(blocker)
    logging.debug(f"Spawned blocker at position: {blocker_rect.topleft}")

# Funktion zum Steuern des Spieler-Autos
def handle_player_movement(keys, player_car, joystick):
    global SCREEN_WIDTH, SCREEN_HEIGHT
    move_x, move_y = 0, 0

    # Keyboard controls (arrow keys and WSAD)
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player_car.rect.left > 0:
        move_x = -5
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player_car.rect.right < SCREEN_WIDTH:
        move_x = 5
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and player_car.rect.top > 0:
        move_y = -5
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player_car.rect.bottom < SCREEN_HEIGHT:
        move_y = 5

    # Joystick controls
    if joystick:
        axis_x = joystick.get_axis(0)  # Left/Right
        axis_y = joystick.get_axis(1)  # Up/Down

        threshold = 0.1  # Deadzone threshold
        # Left/Right movement
        if abs(axis_x) > threshold:
            move_x = axis_x * 5  # Scale as needed
        # Up/Down movement
        if abs(axis_y) > threshold:
            move_y = axis_y * 5  # Scale as needed

    # Update player position
    player_car.rect.x += move_x
    player_car.rect.y += move_y

    # Ensure player stays within screen bounds
    if player_car.rect.left < 0:
        player_car.rect.left = 0
    if player_car.rect.right > SCREEN_WIDTH:
        player_car.rect.right = SCREEN_WIDTH
    if player_car.rect.top < 0:
        player_car.rect.top = 0
    if player_car.rect.bottom > SCREEN_HEIGHT:
        player_car.rect.bottom = SCREEN_HEIGHT

    # Aktualisiere den Zielwinkel basierend auf der Bewegung
    if move_x < 0:
        player_car.target_angle = 15  # Nach links drehen
    elif move_x > 0:
        player_car.target_angle = -15  # Nach rechts drehen
    else:
        player_car.target_angle = 0  # Geradeaus

    # Winkel aktualisieren
    player_car.update_angle()

# Funktion zum Starten des Spiels
def start_game():
    global player_car, cars, blockers, explosions, bullets, bg_y, damage
    global spawn_interval, last_spawn_time, last_spawn_interval_decrease_time
    global last_score, current_color, target_color, last_color_change_time
    global game_over_explosion, game_over_time, max_cars_on_screen
    global last_max_cars_increase_time, last_damage_reduction_time
    global cars_per_spawn, last_cars_per_spawn_increase_time
    global last_big_car_time, big_car_active, big_car
    global last_mass_spawn_time, mass_spawn_active, game_active
    global initial_max_damage, max_damage
    global damage_highlight_start
    global ready_to_restart
    global paused, pause_start_time
    global last_blocker_spawn_time
    global invincible, invincible_start_time, invincible_color, invincible_blink

    # Spieler Auto initialisieren
    player_car_image = load_image(PLAYER_CAR, size=PLAYER_CAR_SIZE, use_scaled=True)
    if player_car_image is None:
        logging.error("Failed to load player car image.")
        game_active = False
        return
    player_car_rect = player_car_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
    player_car_mask = pygame.mask.from_surface(player_car_image)
    player_car = Car(player_car_image, player_car_rect, player_car_mask, speed=0)
    player_car.original_image = player_car_image
    player_car.rotated_images = player_car.pre_rotate_images()

    # Autos und Explosionen zurücksetzen
    cars = []
    blockers = []
    explosions = []
    bullets = []
    big_car = None
    big_car_active = False
    mass_spawn_active = False
    invincible = False

    # Spielvariablen zurücksetzen
    damage = 0
    bg_y = 0
    spawn_interval = 2000  # Start-Spawn-Intervall
    last_spawn_time = pygame.time.get_ticks()
    last_spawn_interval_decrease_time = pygame.time.get_ticks()
    last_max_cars_increase_time = pygame.time.get_ticks()
    max_cars_on_screen = 10  # Startwert für maximale Anzahl von Autos
    last_damage_reduction_time = pygame.time.get_ticks()
    last_cars_per_spawn_increase_time = pygame.time.get_ticks()
    cars_per_spawn = 1  # Startwert für Anzahl der Autos pro Spawn
    last_big_car_time = pygame.time.get_ticks()
    last_mass_spawn_time = pygame.time.get_ticks()
    last_blocker_spawn_time = pygame.time.get_ticks()
    last_score = None
    damage_highlight_start = None  # Hervorhebung zurücksetzen

    # Maximalen Schaden setzen
    if cheat_funds:
        max_damage = 999
    else:
        max_damage = initial_max_damage

    # Hintergrundfarbe zurücksetzen
    current_color = [0, 0, 0]
    target_color = [random.randint(0, 255) for _ in range(3)]
    last_color_change_time = pygame.time.get_ticks()

    # Spielende Explosion zurücksetzen
    game_over_explosion = False
    game_over_time = 0

    # Pause zurücksetzen
    paused = False
    pause_start_time = 0

    # Spiel ist nicht bereit zum Neustart während es läuft
    ready_to_restart = False

    # Hintergrundmusik wechseln
    if load_music(GAME_MUSIC):
        pygame.mixer.music.play(-1)
    else:
        missing_audio_messages.append(f"Audiodatei {GAME_MUSIC} fehlt.")
        logging.info(f"Game music {GAME_MUSIC} missing.")

# Funktion zum Beenden des Spiels und Speichern der Ergebnisse
def end_game(survival_time):
    global game_active, damage, cars, blockers, bullets, game_over_explosion, game_over_time, big_car
    game_active = False
    damage = 0
    cars = []
    blockers = []
    bullets = []
    big_car = None
    update_high_scores(survival_time)
    game_over_explosion = True
    game_over_time = pygame.time.get_ticks()
    if damage_sound:
        damage_sound.play()
    logging.info(f"Game ended. Survival Time: {survival_time} seconds")

# Funktion zur Kollisionserkennung
def check_collision(player_car):
    global damage, big_car, damage_highlight_start, invincible, invincible_start_time
    global invincible_color, invincible_blink
    # Kollision mit Blockern
    for blocker in blockers[:]:
        offset = (blocker.rect.x - player_car.rect.x, blocker.rect.y - player_car.rect.y)
        collision_point = player_car.mask.overlap(blocker.mask, offset)
        if collision_point:
            logging.info(f"Collision detected with blocker at position: {blocker.rect.topleft}")
            # Explosion hinzufügen
            explosion_image = pygame.transform.scale(explosion_image_original, (blocker.rect.width, blocker.rect.height))
            explosion = Explosion(explosion_image, blocker.rect.copy(), 2000)  # Dauer: 2 Sekunden
            explosions.append(explosion)
            blockers.remove(blocker)  # Blocker entfernen
            damage += 1  # Schaden erhöhen
            if collision_sound:
                collision_sound.play()
            damage_highlight_start = pygame.time.get_ticks()  # Hervorhebung starten

    if invincible:
        return  # Keine weitere Kollision während Unverwundbarkeit

    # Kollision mit normalen Autos
    for car in cars[:]:  # Kopie der Liste erstellen
        offset = (car.rect.x - player_car.rect.x, car.rect.y - player_car.rect.y)
        collision_point = player_car.mask.overlap(car.mask, offset)
        if collision_point:
            logging.info(f"Collision detected with car at position: {car.rect.topleft}")
            # Explosion hinzufügen
            explosion_image = pygame.transform.scale(explosion_image_original, (car.rect.width, car.rect.height))
            explosion = Explosion(explosion_image, car.rect.copy(), 2000)  # Dauer: 2 Sekunden
            explosions.append(explosion)
            cars.remove(car)  # Auto aus der Liste entfernen

            # Überprüfen der Größe des Autos
            if car.size_category == 'medium':
                # Unverwundbarkeit aktivieren mit spezifischen Einstellungen
                invincible = True
                invincible_start_time = pygame.time.get_ticks()
                invincible_color = YELLOW
                invincible_blink = True
                invincible_duration = 5000  # 5 Sekunden
                logging.info("Player is now invincible (medium car) for 5 seconds.")
            elif car.size_category == 'large':
                # Unverwundbarkeit aktivieren mit spezifischen Einstellungen
                invincible = True
                invincible_start_time = pygame.time.get_ticks()
                invincible_color = ORANGE
                invincible_blink = True
                invincible_duration = 5000  # 5 Sekunden
                logging.info("Player is now invincible (large car) for 5 seconds.")
            else:
                damage += 1  # Schaden erhöhen
                if collision_sound:
                    collision_sound.play()
                damage_highlight_start = pygame.time.get_ticks()  # Hervorhebung starten

    # Kollision mit großem Auto
    if big_car:
        offset = (big_car.rect.x - player_car.rect.x, big_car.rect.y - player_car.rect.y)
        collision_point = player_car.mask.overlap(big_car.mask, offset)
        if collision_point:
            logging.info(f"Collision with big car at position: {big_car.rect.topleft}")
            # Explosion hinzufügen
            explosion_image = pygame.transform.scale(explosion_image_original, (big_car.rect.width, big_car.rect.height))
            explosion = Explosion(explosion_image, big_car.rect.copy(), 2000)  # Dauer: 2 Sekunden
            explosions.append(explosion)
            big_car = None  # Großes Auto entfernen
            damage += 2  # Mehr Schaden
            if collision_sound:
                collision_sound.play()
            damage_highlight_start = pygame.time.get_ticks()  # Hervorhebung starten

# Funktion zur Kollisionserkennung zwischen Schüssen und Autos
def check_bullet_collisions():
    global big_car, invincible, invincible_start_time, invincible_color, invincible_blink, invincible_duration
    for bullet in bullets[:]:
        for car in cars[:]:
            offset = (car.rect.x - bullet.rect.x, car.rect.y - bullet.rect.y)
            collision_point = bullet.mask.overlap(car.mask, offset)
            if collision_point:
                logging.info(f"Bullet hit car at position: {car.rect.topleft}")
                # Explosion hinzufügen
                explosion_image = pygame.transform.scale(explosion_image_original, (car.rect.width, car.rect.height))
                explosion = Explosion(explosion_image, car.rect.copy(), 2000)
                explosions.append(explosion)
                cars.remove(car)
                bullets.remove(bullet)
                if collision_sound:
                    collision_sound.play()

                # Überprüfen der Größe des Autos
                if car.size_category == 'medium':
                    # Unverwundbarkeit aktivieren mit spezifischen Einstellungen
                    invincible = True
                    invincible_start_time = pygame.time.get_ticks()
                    invincible_color = YELLOW
                    invincible_blink = True
                    invincible_duration = 5000  # 5 Sekunden
                    logging.info("Player is now invincible (medium car destroyed) for 5 seconds.")
                elif car.size_category == 'large':
                    # Unverwundbarkeit aktivieren mit spezifischen Einstellungen
                    invincible = True
                    invincible_start_time = pygame.time.get_ticks()
                    invincible_color = ORANGE
                    invincible_blink = True
                    invincible_duration = 5000  # 5 Sekunden
                    logging.info("Player is now invincible (large car destroyed) for 5 seconds.")
                break  # Keine weitere Prüfung nötig
        else:
            # Prüfung auf Kollision mit Blockern
            for blocker in blockers[:]:
                offset = (blocker.rect.x - bullet.rect.x, blocker.rect.y - bullet.rect.y)
                collision_point = bullet.mask.overlap(blocker.mask, offset)
                if collision_point:
                    logging.info(f"Bullet hit blocker at position: {blocker.rect.topleft}")
                    # Explosion hinzufügen
                    explosion_image = pygame.transform.scale(explosion_image_original, (blocker.rect.width, blocker.rect.height))
                    explosion = Explosion(explosion_image, blocker.rect.copy(), 2000)
                    explosions.append(explosion)
                    blocker.update_state(force_change=True)  # Zustand ändern
                    bullets.remove(bullet)
                    if collision_sound:
                        collision_sound.play()
                    break
            else:
                # Prüfung auf Kollision mit großem Auto
                if big_car:
                    offset = (big_car.rect.x - bullet.rect.x, big_car.rect.y - bullet.rect.y)
                    collision_point = bullet.mask.overlap(big_car.mask, offset)
                    if collision_point:
                        logging.info(f"Bullet hit big car at position: {big_car.rect.topleft}")
                        explosion_image = pygame.transform.scale(explosion_image_original, (big_car.rect.width, big_car.rect.height))
                        explosion = Explosion(explosion_image, big_car.rect.copy(), 2000)
                        explosions.append(explosion)
                        big_car = None
                        bullets.remove(bullet)
                        if collision_sound:
                            collision_sound.play()
                        # Aktiviere Unverwundbarkeit
                        invincible = True
                        invincible_start_time = pygame.time.get_ticks()
                        invincible_color = PURPLE
                        invincible_blink = False
                        invincible_duration = 5000  # 5 Sekunden
                        logging.info("Player is now invincible (big car destroyed) for 5 seconds.")
                        break

# Funktion zum Darstellen des Titelbildschirms
def display_title_screen():
    global title_image_index, last_title_switch, ready_to_restart
    current_time = pygame.time.get_ticks()

    # Setze ready_to_restart auf True, wenn wir im Titelbildschirm sind
    ready_to_restart = True

    # Zeit seit letztem Bildwechsel
    time_since_last_switch = current_time - last_title_switch

    # Bild wechseln, wenn die Zeit abgelaufen ist
    if time_since_last_switch >= title_blend_time:
        title_image_index = (title_image_index + 1) % len(TITLE_IMAGES)
        last_title_switch = current_time
        time_since_last_switch = 0

    # Alpha-Wert für Überblendung berechnen
    title_image_alpha = min(255, int(255 * time_since_last_switch / title_blend_time))

    # Hintergrundbild für den Titel zeichnen
    title_background_image = load_image(TITLE_BACKGROUND_IMAGE, size=(SCREEN_WIDTH, SCREEN_HEIGHT), use_scaled=True, maintain_aspect_ratio=False)
    if title_background_image is None:
        logging.error("Failed to load title background image.")
        return
    screen.blit(title_background_image, (0, 0))

    # Titelbild laden und skalieren (1:1 Seitenverhältnis)
    max_title_image_size = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.6  # 60% der kleineren Bildschirmdimension
    title_image = load_image(TITLE_IMAGES[title_image_index], size=(int(max_title_image_size), int(max_title_image_size)), use_scaled=True, maintain_aspect_ratio=True)
    if title_image is None:
        logging.error("Failed to load title image.")
        return
    title_image.set_alpha(title_image_alpha)

    # Titelbild zentriert blitten und um 100 Pixel nach unten verschieben
    title_image_rect = title_image.get_rect(center=(screen.get_width() // 2, screen.get_height() // 4 + 100))
    screen.blit(title_image, title_image_rect)

    # Logo anzeigen (Originalgröße)
    logo_image = load_image(LOGO_IMAGE, use_scaled=False)
    if logo_image is None:
        logging.error("Failed to load logo image.")
        return
    screen.blit(logo_image, (screen.get_width() // 2 - logo_image.get_width() // 2, 20))

    # Titeltext
    font = pygame.font.SysFont(None, 55)
    title_text = font.render("Press Space to Begin. Press ESC to Exit.", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT - 100))

    # Highscores anzeigen
    high_scores_y_offset = title_image_rect.bottom + 20  # 20 Pixel unterhalb des Titelbildes
    high_scores_y_offset = max(high_scores_y_offset - 50, 0)  # Position um 50 Pixel höher setzen, ohne negativ zu werden
    display_high_scores(high_scores_y_offset)

    # Fehlende Audiodateien anzeigen
    if missing_audio_messages:
        font_audio = pygame.font.SysFont(None, 30)
        y_offset = 10
        for message in missing_audio_messages:
            audio_text = font_audio.render(message, True, RED)
            screen.blit(audio_text, (10, y_offset))
            y_offset += 30

# Funktion zum Anzeigen der Highscores
def display_high_scores(y_offset):
    font = pygame.font.SysFont(None, 40)
    title = font.render("High Scores", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, y_offset))
    y_offset += 40

    for idx, (score, date_str) in enumerate(high_scores):
        if (score, date_str) == last_score:
            color = RED  # Hervorheben des letzten Scores
        else:
            color = WHITE
        score_text = font.render(f"{idx + 1}. {score}s - {date_str}", True, color)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, y_offset))
        y_offset += 30

# Hauptspiel-Schleife
load_high_scores()
CAR_IMAGES = load_car_images()
BLOCKER_IMAGES = load_blocker_images()
generate_scaled_images(CAR_IMAGES)

# Schussgrafik laden
bullet_image = load_image(BULLET_IMAGE, size=(10, 20), use_scaled=True)
if bullet_image is None:
    # Platzhaltergrafik erstellen
    bullet_image = pygame.Surface((10, 20), pygame.SRCALPHA)
    pygame.draw.circle(bullet_image, RED, (5, 10), 5)
    logging.info("Using placeholder bullet image.")

clock = pygame.time.Clock()
start_ticks = 0
elapsed_time = 0

while game_running:
    try:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_active:
                        # Zurück zum Titelbildschirm
                        logging.info("Returning to title menu.")
                        game_active = False
                        # Hintergrundmusik wechseln
                        if load_music(TITLE_MUSIC):
                            pygame.mixer.music.play(-1)
                        else:
                            missing_audio_messages.append(f"Audiodatei {TITLE_MUSIC} fehlt.")
                            logging.info(f"Title music {TITLE_MUSIC} missing.")
                    else:
                        # Spiel beenden
                        game_running = False
                        logging.info("Game exited via ESC key in title menu.")
                elif event.key == pygame.K_p and game_active:
                    paused = not paused
                    if paused:
                        # Spiel pausieren
                        pause_start_time = pygame.time.get_ticks()
                    else:
                        # Spiel fortsetzen
                        paused_duration = pygame.time.get_ticks() - pause_start_time
                        start_ticks += paused_duration
                        pause_start_time = 0
                elif not game_active and ready_to_restart:
                    if event.key == pygame.K_SPACE:
                        logging.info("Game started.")
                        game_active = True
                        start_ticks = pygame.time.get_ticks()
                        start_game()
                elif game_active:
                    if event.key == pygame.K_SPACE:
                        # Schuss abfeuern
                        bullet_rect = bullet_image.get_rect(center=(player_car.rect.centerx, player_car.rect.top))
                        bullet = Bullet(bullet_image, bullet_rect, speed=10)
                        bullets.append(bullet)
                        if shoot_sound:
                            shoot_sound.play()
                        logging.debug(f"Bullet fired from position: {bullet_rect.topleft}")
                        # Subtrahiere 3 Sekunden von der bisherigen Zeit
                        start_ticks += 3000  # Erhöhe start_ticks, um die Zeit zu reduzieren
                        # Überprüfe, ob die Zeit unter Null gefallen ist
                        elapsed_time = (current_time - start_ticks) // 1000
                        if elapsed_time < 0:
                            elapsed_time = 0
                            end_game(elapsed_time)
            if event.type == pygame.JOYBUTTONDOWN:
                if joystick:
                    if event.button == 0:  # Assuming button 0 is fire
                        if game_active:
                            # Schuss abfeuern
                            bullet_rect = bullet_image.get_rect(center=(player_car.rect.centerx, player_car.rect.top))
                            bullet = Bullet(bullet_image, bullet_rect, speed=10)
                            bullets.append(bullet)
                            if shoot_sound:
                                shoot_sound.play()
                            logging.debug(f"Bullet fired from position: {bullet_rect.topleft}")
                            # Subtrahiere 3 Sekunden von der bisherigen Zeit
                            start_ticks += 3000  # Erhöhe start_ticks, um die Zeit zu reduzieren
                            # Überprüfe, ob die Zeit unter Null gefallen ist
                            elapsed_time = (current_time - start_ticks) // 1000
                            if elapsed_time < 0:
                                elapsed_time = 0
                                end_game(elapsed_time)
                        elif not game_active and ready_to_restart:
                            logging.info("Game started via joystick.")
                            game_active = True
                            start_ticks = pygame.time.get_ticks()
                            start_game()

        # Berechne elapsed_time unabhängig vom Spielzustand
        if game_active or game_over_explosion:
            elapsed_time = (current_time - start_ticks) // 1000

        if game_active and not paused:
            # Hintergrund scrollen
            bg_y = scroll_background(bg_y)

            # Unverwundbarkeit prüfen
            if invincible:
                if current_time - invincible_start_time > invincible_duration:
                    invincible = False
                    logging.info("Player invincibility ended.")
                else:
                    # Zeichne blinkenden Kreis um das Spielerauto
                    if invincible_blink:
                        if (current_time // 250) % 2 == 0:
                            pygame.draw.circle(screen, invincible_color, player_car.rect.center, 80, 2)
                    else:
                        pygame.draw.circle(screen, invincible_color, player_car.rect.center, 80, 2)

            # Autos spawnen
            if current_time - last_spawn_time > spawn_interval:
                cars_needed = max_cars_on_screen - len(cars)
                cars_this_spawn = min(cars_per_spawn, cars_needed)
                for _ in range(cars_this_spawn):
                    spawn_car(cars, CAR_IMAGES)
                last_spawn_time = current_time

            # Spawn-Intervall verringern
            if current_time - last_spawn_interval_decrease_time > spawn_interval_decrease_time and spawn_interval > min_spawn_interval:
                spawn_interval = max(spawn_interval - spawn_interval_decrease, min_spawn_interval)
                last_spawn_interval_decrease_time = current_time
                logging.info(f"Spawn interval decreased to: {spawn_interval} ms")

            # Maximale Anzahl von Autos erhöhen
            if current_time - last_max_cars_increase_time > max_cars_increase_interval:
                max_cars_on_screen += max_cars_increment
                last_max_cars_increase_time = current_time
                logging.info(f"Max cars on screen increased to: {max_cars_on_screen}")

            # Anzahl der Autos pro Spawn erhöhen
            if current_time - last_cars_per_spawn_increase_time > cars_per_spawn_increase_interval and cars_per_spawn < max_cars_per_spawn:
                cars_per_spawn += 1
                last_cars_per_spawn_increase_time = current_time
                logging.info(f"Cars per spawn increased to: {cars_per_spawn}")

            # Blocker spawnen
            if current_time - last_blocker_spawn_time > blocker_spawn_interval:
                if BLOCKER_IMAGES:
                    spawn_blocker(blockers, BLOCKER_IMAGES)
                    last_blocker_spawn_time = current_time
                else:
                    logging.info("No blocker images available. Skipping blocker spawn.")

            # Schaden reduzieren
            if current_time - last_damage_reduction_time > damage_reduction_interval:
                if damage > 0:
                    damage -= 1
                    if heal_sound:
                        heal_sound.play()
                    logging.info(f"Damage reduced to: {damage}")
                    damage_highlight_start = current_time  # Hervorhebung starten
                last_damage_reduction_time = current_time

            # Großes Auto spawnen
            if current_time - last_big_car_time > big_car_interval and not big_car_active:
                big_car_image_path = random.choice(CAR_IMAGES)
                big_car_image = load_image(big_car_image_path, size=(200, 200), use_scaled=True)
                if big_car_image:
                    big_car_rect = big_car_image.get_rect(midtop=(random.randint(50, SCREEN_WIDTH - 50), -200))
                    big_car_mask = pygame.mask.from_surface(big_car_image)
                    big_car_speed = random.randint(3, 5)
                    big_car = Car(big_car_image, big_car_rect, big_car_mask, big_car_speed)
                    big_car.original_image = big_car_image
                    big_car.rotated_images = big_car.pre_rotate_images()
                    big_car.size_category = 'big'
                    big_car_active = True
                    logging.info("Big car spawned.")
                last_big_car_time = current_time

            # Großes Auto aktualisieren
            if big_car:
                big_car.rect.y += big_car.speed
                # Winkel zurücksetzen
                big_car.target_angle = 0
                big_car.update_angle()
                if big_car.rect.top > SCREEN_HEIGHT:
                    big_car = None
                    big_car_active = False
                else:
                    screen.blit(big_car.image, big_car.rect)

            # Massenspawn
            if current_time - last_mass_spawn_time > mass_spawn_interval and not mass_spawn_active:
                for _ in range(7):
                    spawn_car(cars, CAR_IMAGES)
                mass_spawn_active = True
                last_mass_spawn_time = current_time
                if not cheat_funds:
                    max_damage += 10  # Erhöhe die maximalen Schadenpunkte um 10
                logging.info(f"Mass spawn of 7 cars. Max damage increased to {max_damage}.")

            # Massenspawn zurücksetzen
            if mass_spawn_active and current_time - last_mass_spawn_time > spawn_interval:
                mass_spawn_active = False
                if not cheat_funds:
                    max_damage = initial_max_damage  # Setze die maximalen Schadenpunkte zurück
                    if damage > max_damage:
                        damage = max_damage  # Passe den aktuellen Schaden an
                logging.info(f"Mass spawn ended. Max damage reset to {max_damage}.")

            # Spielerbewegung
            keys = pygame.key.get_pressed()
            handle_player_movement(keys, player_car, joystick)

            # Spieler Auto zeichnen
            if player_car.image is None:
                logging.error("Failed to load player car image during game loop.")
                game_active = False  # Spiel stoppen
            else:
                screen.blit(player_car.image, player_car.rect)

            # Schüsse aktualisieren
            for bullet in bullets[:]:
                if not bullet.update():
                    bullets.remove(bullet)
                else:
                    screen.blit(bullet.image, bullet.rect)

            # Kollision zwischen Schüssen und Autos prüfen
            check_bullet_collisions()

            # Blocker aktualisieren
            for blocker in blockers[:]:
                blocker.rect.y += 1  # Bewegt sich mit der Geschwindigkeit des Hintergrunds
                if blocker.rect.top > SCREEN_HEIGHT:
                    blockers.remove(blocker)
                elif blocker.state == 2:
                    # Blocker zerstört, aus Liste entfernen
                    blockers.remove(blocker)
                else:
                    screen.blit(blocker.image, blocker.rect)

            # Autos aktualisieren
            for car in cars[:]:
                # Ausweichmanöver prüfen (inklusive großes Auto und Blocker)
                collision_detected = False
                for other_object in cars + blockers + ([big_car] if big_car else []):
                    if other_object == car or other_object is None:
                        continue
                    if isinstance(other_object, Blocker) and other_object.state == 2:
                        continue  # Ignoriere zerstörte Blocker
                    if abs(car.rect.y - other_object.rect.y) < 100 and car.rect.colliderect(other_object.rect):
                        # Ausweichen nach links oder rechts
                        if car.rect.x > other_object.rect.x:
                            car.rect.x += 5  # Nach rechts ausweichen
                            car.target_angle = -15  # Nach rechts drehen
                        else:
                            car.rect.x -= 5  # Nach links ausweichen
                            car.target_angle = 15  # Nach links drehen
                        collision_detected = True
                        # Bildschirmgrenzen prüfen
                        if car.rect.left < 0:
                            car.rect.left = 0
                        if car.rect.right > SCREEN_WIDTH:
                            car.rect.right = SCREEN_WIDTH
                        # Blocker-Status aktualisieren
                        if isinstance(other_object, Blocker):
                            other_object.update_state(triggering_car=car)
                        break  # Nur einmal ausweichen
                if not collision_detected:
                    # Prüfe, ob der Spieler unverwundbar ist
                    if invincible:
                        # Autos weichen dem Spielerauto aus
                        offset_x = player_car.rect.x - car.rect.x
                        if invincible_color == YELLOW:
                            displacement = 3  # Weniger Verdrängung
                        elif invincible_color == ORANGE:
                            displacement = 4  # Mittlere Verdrängung
                        elif invincible_color == PURPLE:
                            displacement = 5  # Stärkere Verdrängung
                        else:
                            displacement = 5  # Standard
                        if offset_x > 0:
                            car.rect.x -= displacement
                            car.target_angle = 15
                        else:
                            car.rect.x += displacement
                            car.target_angle = -15
                    else:
                        car.target_angle = 0  # Zurück zur geraden Ausrichtung

                # Bewegung nach unten
                car.rect.y += car.speed

                # Winkel aktualisieren
                car.update_angle()

                if car.rect.top > SCREEN_HEIGHT:
                    cars.remove(car)  # Entferne Auto, wenn es den Bildschirm verlässt
                else:
                    screen.blit(car.image, car.rect)

            # Zeit und Schaden anzeigen
            font = pygame.font.SysFont(None, 35)
            time_text = font.render(f"Time: {elapsed_time}s", True, BLACK)

            # Schadensanzeige hervorheben, wenn nötig
            if damage_highlight_start and current_time - damage_highlight_start < damage_highlight_duration:
                damage_color = (255, 255, 0)  # Gelb
            else:
                damage_color = RED

            damage_text = font.render(f"Damage: {damage}/{max_damage}", True, damage_color)
            screen.blit(time_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 40))
            screen.blit(damage_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70))

            # Fehlende Audiodateien anzeigen
            if missing_audio_messages:
                font_audio = pygame.font.SysFont(None, 30)
                y_offset = 10
                for message in missing_audio_messages:
                    audio_text = font_audio.render(message, True, RED)
                    screen.blit(audio_text, (10, y_offset))
                    y_offset += 30

            # Kollisionserkennung und Schaden prüfen
            check_collision(player_car)
            if damage >= max_damage:
                end_game(elapsed_time)  # Spiel beenden

            # Explosionen aktualisieren
            for explosion in explosions[:]:
                if not explosion.update():
                    explosions.remove(explosion)
                else:
                    explosion.image.set_alpha(explosion.alpha)
                    screen.blit(explosion.image, explosion.rect)

        elif game_active and paused:
            # Pausenbildschirm anzeigen
            font = pygame.font.SysFont(None, 100)
            pause_text = font.render("Paused", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                                     SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))

        elif game_over_explosion:
            # Explosion über den gesamten Bildschirm anzeigen
            explosion_image_fullscreen = pygame.transform.scale(explosion_image_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
            elapsed_explosion_time = pygame.time.get_ticks() - game_over_time
            if elapsed_explosion_time < 3000:
                alpha = 255 - int((elapsed_explosion_time / 3000) * 255)
                explosion_image_fullscreen.set_alpha(alpha)
                screen.blit(explosion_image_fullscreen, (0, 0))

                # Überlebenszeit anzeigen
                font = pygame.font.SysFont(None, 100)
                survival_time_text = font.render(f"Survived: {elapsed_time}s", True, WHITE)
                screen.blit(survival_time_text, (SCREEN_WIDTH // 2 - survival_time_text.get_width() // 2,
                                                 SCREEN_HEIGHT // 2 - survival_time_text.get_height() // 2))
            else:
                game_over_explosion = False
                # Hintergrundmusik wechseln
                if load_music(TITLE_MUSIC):
                    pygame.mixer.music.play(-1)
                else:
                    missing_audio_messages.append(f"Audiodatei {TITLE_MUSIC} fehlt.")
                    logging.info(f"Title music {TITLE_MUSIC} missing.")
        else:
            display_title_screen()

        pygame.display.flip()
        clock.tick(FPS)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        game_running = False

pygame.quit()
logging.info("Game exited.")

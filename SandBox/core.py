# SandBox/core.py — основной движок симуляции экосистемы
# CeTzyyy © 2026


__progect = 'Песочница на tkinter с NPC и простым AI'

import tkinter as tk
import math
import random
import time
from PIL import Image, ImageDraw, ImageTk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from SandBox.entities import Entity, Peaceful, Predator, Human, mix_colors
    from SandBox.objects import StaticObject, Plant
    from SandBox.player import Player, Camera


class SandBox:
    """Главный класс симуляции экосистемы.
    
    Управляет холстом, сущностями, коллизиями, камерой и игровым циклом.
    Мир центрирован: координаты от -width/2 до width/2.
    
    Attributes:
        _entities: список всех живых существ (Entity, Peaceful, Predator, Player)
        _objects: список статических объектов (Plant, StaticObject, Den)
        _camera: камера для панорамирования и зума
        _grid: SpatialGrid для быстрых коллизий
        _total_kills: счётчик убийств
        _total_deaths: счётчик смертей
    """
    
    def __init__(self, collision_enabled=True, world_height=5000, world_width=5000, show_borders=True):
        """Создать песочницу с холстом tkinter.
        
        Args:
            collision_enabled: включить коллизии между сущностями
            world_height: высота мира в пикселях
            world_width: ширина мира в пикселях
            show_borders: рисовать красную рамку границ мира
        """
        from SandBox.entities import Entity, Peaceful, Predator
        from SandBox.objects import StaticObject, Plant
        from SandBox.player import Player, Camera
            
        self._ground = tk.Tk()
        self._ground.title('SandBox')
        self._ground.state('zoomed')
        self._ground.config(bg="#E7E7E7")
        self._collision_enabled = collision_enabled
        
        # Привязка событий мыши
        self._ground.bind("<Motion>", self._on_mouse_move)
        self._ground.bind("<Double-Button-1>", self.on_double_click)
        self._ground.bind("<Button-3>", self.on_click)
        self._ground.bind("<ButtonPress-2>", self._on_camera_drag_start)
        self._ground.bind("<B2-Motion>", self._on_camera_drag)
        self._ground.bind("<ButtonRelease-2>", self._on_camera_drag_end)
        
        self._world_width = world_width  
        self._world_height = world_height
        self._world_offset_x = -world_width // 2  
        self._world_offset_y = -world_height // 2
        
        # FPS-счётчик
        self._fps_counter = 0
        self._fps_timer = time.time()
        self._last_fps = 0
        
        self._follow_target = None
        self._selected_entity = None
        
        # Холст и PIL-изображение для рендеринга
        self._canvas = tk.Canvas(self._ground, bg="white")
        self._canvas.pack(fill=tk.BOTH, expand=True)
        
        self._info_label = tk.Label(self._ground, text="Test", bg="yellow", fg="black", 
                                    font=("Courier", 10), justify="left", anchor="w")
        self._info_label.place(x=10, y=10)
        self._info_label.lift()
        
        self._grid = SpatialGrid(cell_size=100)
        self._camera = Camera()
        
        self._player = None
        self._entities = []
        self._objects = []
        
        self._total_kills = 0
        self._total_deaths = 0
        
        self._ground.update()
        
        self._show_borders = show_borders
        self._pil_image = Image.new("RGB", (self.width, self.height), "white")
        self._pil_draw = ImageDraw.Draw(self._pil_image)
        self._tk_image = ImageTk.PhotoImage(self._pil_image)
        self._canvas_image = self._canvas.create_image(0, 0, anchor="nw", image=self._tk_image)
    
    def __str__(self):
        return f"Проект: {__progect}"
    
    def __repr__(self):
        return f"Project('{__progect}')"
    
    def __call__(self, FPS=60):
        """Запустить симуляцию с указанным FPS.
        
        Args:
            FPS: кадров в секунду (по умолчанию 60)
        """
        self.update(FPS)
        self._ground.mainloop()
        
    @property
    def width(self):
        """Ширина холста в пикселях."""
        return self._canvas.winfo_width()

    @property
    def height(self):
        """Высота холста в пикселях."""
        return self._canvas.winfo_height()
        
    def create_player(self, color="#00FF00", speed=3):
        """Создать управляемого игрока-наблюдателя.
        
        Args:
            color: цвет в hex-формате
            speed: скорость перемещения
        """
        from SandBox.player import Player 
        self._player = Player(600, 375, color=color, speed=speed) 
        self.add_entity(self._player)
        
    def spawn_random_entities(self, count, *types, color=None, **kwargs):
        """Создать случайных существ указанных типов.
        
        Args:
            count: количество существ
            *types: классы существ (Peaceful, Predator, etc.)
            color: цвет (если None — используется цвет по умолчанию)
            **kwargs: параметры, передаваемые в конструктор существа
        """
        from SandBox.entities import Entity
        if not types:
            types = (Entity,)
        
        for i in range(count):
            entity_type = random.choice(types)
            x = random.randint(self._world_offset_x + 50, self._world_offset_x + self._world_width - 50)
            y = random.randint(self._world_offset_y + 50, self._world_offset_y + self._world_height - 50)
            
            if color:
                entity = entity_type(x, y, color=color, **kwargs)
            else:
                entity = entity_type(x, y, **kwargs)
            
            self._entities.append(entity)
            
    def configure_entities(self, entity_type, breeding_enabled=None, **params):
        """Массовая настройка параметров существ заданного типа.
        
        Args:
            entity_type: класс (Peaceful, Predator, etc.)
            breeding_enabled: True — разрешить размножение, False — запретить, None — не трогать
            **params: любые атрибуты для установки (breed_chance, chase_speed, etc.)
        """
        for e in self._entities:
            if isinstance(e, entity_type):
                for attr, value in params.items():
                    if hasattr(e, attr):
                        setattr(e, attr, value)
                
                if breeding_enabled is not None:
                    if breeding_enabled:
                        e.breed_cooldown = 0
                    else:
                        e.breed_cooldown = 999999
                        
    def spawn_random_objects(self, count, color="#AFAEAE", form='rectangle'):
        """Создать случайные статические объекты.
        
        Args:
            count: количество объектов
            color: цвет
            form: 'rectangle' или 'oval'
        """
        from SandBox.objects import StaticObject 
        for i in range(count):
            x = random.randint(self._world_offset_x + 50, self._world_offset_x + self._world_width - 50)
            y = random.randint(self._world_offset_y + 50, self._world_offset_y + self._world_height - 50)
            object = StaticObject(x, y, color, form)
            self._objects.append(object)
            
    def draw_all(self):
        """Отрисовать все объекты и существ на холсте.
        
        Порядок: нижний слой (растения) → существа → верхний слой (объекты с collision) → границы мира.
        """
        self._pil_draw.rectangle([0, 0, self.width, self.height], fill="white") 
        
        for o in self._objects:
            if o.layer == "lower":
                if o.size > 0:
                    o.draw(self._pil_draw, self._camera)
        
        for e in self._entities:
            e.draw(self._pil_draw, self._camera)
        
        for o in self._objects:
            if o.layer == "lift":
                o.draw(self._pil_draw, self._camera)
        
        if self._show_borders:
            left = self._camera.world_to_screen(self._world_offset_x, 0)[0]
            right = self._camera.world_to_screen(self._world_offset_x + self._world_width, 0)[0]
            top = self._camera.world_to_screen(0, self._world_offset_y)[1]
            bottom = self._camera.world_to_screen(0, self._world_offset_y + self._world_height)[1]
            self._pil_draw.rectangle([left, top, right, bottom], outline="red", width=3)
        
        self._tk_image = ImageTk.PhotoImage(self._pil_image)
        self._canvas.itemconfig(self._canvas_image, image=self._tk_image)
        
    def check_collision(self):
        """Проверить столкновения и разрешить их выталкиванием.
        
        Использует SpatialGrid для быстрого поиска соседей.
        Убегающие мирные (state='flee') не отталкиваются.
        """
        from SandBox.entities import Peaceful
        if self._collision_enabled:
            # Entity ↔ Entity
            self._grid.clear()
            for e in self._entities:
                self._grid.add(e)
            
            for entity in self._entities:
                if entity == self._player: 
                    continue
                if isinstance(entity, Peaceful) and getattr(entity, 'state', None) in ("flee", "rest"):
                    continue
                nearby = self._grid.get_nearby(entity)
                for other in nearby:
                    if other == self._player:
                        continue
                    if isinstance(other, Peaceful) and getattr(other, 'state', None) in ("flee", "rest"):
                        continue
                    if entity != other and entity.is_colliding_with(other):
                        dx = entity.pos.x - other.pos.x
                        dy = entity.pos.y - other.pos.y
                        dist = Vector(dx, dy).length()
                        overlap = (entity.size + other.size) - dist
                        
                        if dist > 0:
                            nx = dx / dist
                            ny = dy / dist
                            entity.pos.x += nx * overlap / 2
                            entity.pos.y += ny * overlap / 2
                            other.pos.x -= nx * overlap / 2
                            other.pos.y -= ny * overlap / 2

            # Entity ↔ Objects
            for entity in self._entities:
                if entity == self._player:
                    continue
                if isinstance(entity, Peaceful) and getattr(entity, 'state', None) in ("flee", "rest"):
                    continue
                for obj in self._objects:
                    if obj.layer == "lower":
                        continue
                    if not obj.collision:  
                        continue
                    if entity.is_colliding_with(obj):
                        dx = entity.pos.x - obj.pos.x
                        dy = entity.pos.y - obj.pos.y
                        dist = Vector(dx, dy).length()
                        overlap = (entity.size + obj.size) - dist
                        
                        if dist > 0:
                            nx = dx / dist
                            ny = dy / dist
                            entity.pos.x += nx * overlap
                            entity.pos.y += ny * overlap
                            
            # Мягкое отталкивание от границ мира
            margin = 50
            for entity in self._entities:
                left = self._world_offset_x + margin
                right = self._world_offset_x + self._world_width - margin
                top = self._world_offset_y + margin
                bottom = self._world_offset_y + self._world_height - margin
                
                if entity.pos.x < left:
                    entity.pos.x += (left - entity.pos.x) * 0.3
                elif entity.pos.x > right:
                    entity.pos.x += (right - entity.pos.x) * 0.3
                
                if entity.pos.y < top:
                    entity.pos.y += (top - entity.pos.y) * 0.3
                elif entity.pos.y > bottom:
                    entity.pos.y += (bottom - entity.pos.y) * 0.3
                    
    def spawn_plants(self, clusters=10, min_plants=10, max_plants=25, spread=100,
                    food_min=2, food_max=5, regrowth_min=0.003, regrowth_max=0.015,
                    bite_min=0.5, bite_max=1.5, bite_mult=0.8,
                    respawn_chance=0.0005, respawn_percent=0.3):
        """Засеять траву кучками (кластерами).
        
        Args:
            clusters: количество кучек
            min_plants, max_plants: границы количества растений в кучке
            spread: разброс от центра кучки в пикселях
            food_min, food_max: границы начальной еды
            regrowth_min, regrowth_max: границы скорости восстановления
            bite_min, bite_max: границы размера укуса
            bite_mult: множитель пищевой ценности
            respawn_chance: шанс возрождения съеденного растения за кадр
            respawn_percent: процент максимальной еды при возрождении
        """
        from SandBox.objects import Plant
        for _ in range(clusters):
            cx = random.randint(self._world_offset_x + 200, self._world_offset_x + self._world_width - 200)
            cy = random.randint(self._world_offset_y + 200, self._world_offset_y + self._world_height - 200)
            count = random.randint(min_plants, max_plants)
            
            for _ in range(count):
                x = cx + random.randint(-spread, spread)
                y = cy + random.randint(-spread, spread)
                plant = Plant(x, y,
                            food_min=food_min, food_max=food_max,
                            regrowth_min=regrowth_min, regrowth_max=regrowth_max,
                            bite_min=bite_min, bite_max=bite_max, bite_mult=bite_mult,
                            respawn_chance=respawn_chance, respawn_percent=respawn_percent)
                self._objects.append(plant)
                    
    def update(self, FPS=60):
        """Главный игровой цикл — выполняется каждый кадр.
        
        Порядок: отрисовка → поведение существ → коллизии → голод/здоровье → размножение → смерть.
        
        Args:
            FPS: кадров в секунду
        """
        from SandBox.entities import Entity, Peaceful, Predator, Human, mix_colors
        from SandBox.objects import Plant, Den
        delay = 1000 // FPS
        
        # FPS и статистика в заголовке окна
        self._fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self._fps_timer
        
        if elapsed >= 0.5: 
            self._last_fps = int(self._fps_counter / elapsed)
            predator_count = len([e for e in self._entities if isinstance(e, Predator)])
            peaceful_count = len([e for e in self._entities if isinstance(e, Peaceful)])
            self._ground.title(
                f'SandBox | FPS: {self._last_fps} | '
                f'Всего: {len(self._entities)} | Х: {predator_count} | М: {peaceful_count} | '
                f'Убито: {self._total_kills} | Умерло: {self._total_deaths}'
            )
            self._fps_counter = 0
            self._fps_timer = current_time
        
        # Инфо-панель по выбранному существу
        if self._selected_entity:
            if self._selected_entity in self._entities:
                self._update_info_label()
            else:
                self._selected_entity = None
                self._info_label.config(text="")
        
        self.draw_all()
        
        # Движение не-хищников и не-мирных (Player, будущие Human)
        for e in self._entities:
            if e != self._player and not isinstance(e, Predator) and not isinstance(e, Peaceful):
                if not isinstance(e, Human):
                    e.move_random(self._world_width, self._world_height)
        
        self.check_collision()
        
        if self._player:
            self._player.move_to_target()
            
        # =============================================
        # ХИЩНИКИ: поиск партнёра ИЛИ охота
        # =============================================
        victims_to_remove = []
        for e in self._entities:
            if isinstance(e, Predator):
                mate = e.find_mate(self._entities)
                if mate:
                    # Есть партнёр — двигаться к нему
                    e.state = "seek_mate"
                    e.target_mate = mate
                    dx = mate.pos.x - e.pos.x
                    dy = mate.pos.y - e.pos.y
                    dist = Vector(dx, dy).length()
                    if dist > 0:
                        speed = e.dna.speed * getattr(e, 'mate_speed', 0.8)
                        e.pos.x += (dx / dist) * speed
                        e.pos.y += (dy / dist) * speed
                    e.hunger -= getattr(e, 'mate_cost', 0.01)
                else:
                    # Нет партнёра — искать добычу
                    e.find_target(self._entities)
                    
                    # Цель или сам хищник в логове? — сбросить цель, уйти
                    if e.target:
                        in_den = False
                        for obj in self._objects:
                            if isinstance(obj, Den) and (obj.is_safe(e.target) or obj.is_safe(e)):
                                in_den = True
                                break
                        if in_den:
                            e.target = None
                            e.state = "patrol"
                            e.patrol_target = None
                            e.patrol_steps = 180
                            # Отойти от логова — только если ещё не отходил
                            if not getattr(e, '_fled_den', False):
                                angle = random.uniform(0, 2 * math.pi)
                                e.pos.x += math.cos(angle) * 40
                                e.pos.y += math.sin(angle) * 40
                                e._fled_den = True
                        else:
                            e._fled_den = False
                    
                    victim = e.chase_target(self._world_width, self._world_height)
                    if victim and victim in self._entities:
                        victims_to_remove.append((e, victim))
                    
        for predator, victim in victims_to_remove:
            if victim in self._entities:
                self._entities.remove(victim)
        self._total_kills += len(victims_to_remove)
        
        # =============================================
        # МИРНЫЕ: одна сила — flee/home ИЛИ mate ИЛИ graze ИЛИ wander
        # =============================================
        dead = []
        for e in self._entities:
            if isinstance(e, Peaceful):
                hunger_mod = 0.5 + (e.hunger / 100) * 0.5
                hp_mod = 0.6 + (e.hp / e.dna.hp) * 0.4
                
                threat, threat_dist = e.see_predator(self._entities)
                
                if threat:
                    # === ПРИОРИТЕТ 1: Угроза — бежать к логову или от хищника ===
                    
                    # Проверить, уже в безопасности?
                    already_safe = False
                    for obj in self._objects:
                        if isinstance(obj, Den) and obj.is_safe(e):
                            already_safe = True
                            break
                    
                    if already_safe:
                        # В логове — отдых, не паниковать
                        e.state = "rest"
                        e.flee_vx = 0
                        e.flee_vy = 0
                        e.target_mate = None
                    else:
                        # Не в логове — найти ближайшее и бежать к нему
                        home = e.want_to_go_home(self._objects)
                        
                        if home:
                            # Бежим к логову
                            dx = home.pos.x - e.pos.x
                            dy = home.pos.y - e.pos.y
                            dist = Vector(dx, dy).length()
                            if dist > 0:
                                speed = e.dna.speed * 1.5 * hunger_mod * hp_mod
                                e.pos.x += (dx / dist) * speed
                                e.pos.y += (dy / dist) * speed
                            e.hunger -= e.flee_cost_close
                            e.state = "flee"
                            e.target_mate = None
                            
                            # Добежали?
                            if dist < home.safe_radius:
                                e.state = "rest"
                                e.flee_vx = 0
                                e.flee_vy = 0
                        else:
                            # Нет логова поблизости — просто бежать от хищника
                            if threat_dist < 50:
                                speed_mult = e.flee_speed_close * hunger_mod * hp_mod
                                hunger_cost = e.flee_cost_close
                            elif threat_dist < 100:
                                speed_mult = e.flee_speed_mid * hunger_mod * hp_mod
                                hunger_cost = e.flee_cost_mid
                            else:
                                speed_mult = e.flee_speed_far * hunger_mod * hp_mod
                                hunger_cost = e.flee_cost_far
                            
                            dx = e.pos.x - threat.pos.x
                            dy = e.pos.y - threat.pos.y
                            if threat_dist > 0:
                                target_vx = (dx / threat_dist) * e.dna.speed * speed_mult
                                target_vy = (dy / threat_dist) * e.dna.speed * speed_mult
                                e.flee_vx += (target_vx - e.flee_vx) * 0.3
                                e.flee_vy += (target_vy - e.flee_vy) * 0.3
                                e.pos.x += e.flee_vx
                                e.pos.y += e.flee_vy
                            e.hunger -= hunger_cost
                            e.state = "flee"
                            e.target_mate = None
                else:
                    # === НЕТ УГРОЗЫ: приоритет 2 — партнёр, 3 — еда, 4 — wander ===
                    mate = e.find_mate(self._entities)
                    if mate:
                        e.state = "seek_mate"
                        e.target_mate = mate
                        dx = mate.pos.x - e.pos.x
                        dy = mate.pos.y - e.pos.y
                        dist = Vector(dx, dy).length()
                        if dist > 0:
                            speed = e.dna.speed * e.mate_speed * hunger_mod * hp_mod
                            e.pos.x += (dx / dist) * speed
                            e.pos.y += (dy / dist) * speed
                        e.hunger -= e.mate_cost
                    else:
                        # Ищем ближайшее растение
                        closest_plant = None
                        min_plant_dist = 100
                        
                        for obj in self._objects:
                            if isinstance(obj, Plant) and obj.food_value > 0:
                                dist = e.pos.distance_to(obj.pos)
                                if dist < min_plant_dist:
                                    min_plant_dist = dist
                                    closest_plant = obj
                        
                        if closest_plant:
                            dx = closest_plant.pos.x - e.pos.x
                            dy = closest_plant.pos.y - e.pos.y
                            dist = e.pos.distance_to(closest_plant.pos)
                            
                            if dist < e.size + closest_plant.size:
                                food = closest_plant.eat()
                                e.hunger = min(100, e.hunger + food)
                                e.state = "eat"
                            elif dist > 0:
                                speed = e.dna.speed * e.graze_speed * hunger_mod * hp_mod
                                e.pos.x += (dx / dist) * speed
                                e.pos.y += (dy / dist) * speed
                                e.state = "graze"
                            e.hunger -= e.graze_cost
                        else:
                            e.state = "wander"
                            e.move_random(self._world_width, self._world_height)
                            e.hunger -= e.base_metabolism * (e.dna.size ** 0.75)
        
        # =============================================
        # ЗДОРОВЬЕ ОТ ГОЛОДА
        # =============================================
        for e in self._entities:
            if isinstance(e, Peaceful):
                if e.hunger >= e.hp_regen_threshold:
                    e.hp = min(e.hp + e.hp_regen_rate, e.dna.hp)
                elif e.hunger <= e.hp_damage_threshold:
                    e.hp -= (e.hp_damage_threshold - e.hunger) * e.hp_damage_rate
                    if e.hp <= 0:
                        dead.append(e)
                        continue
                if e.hunger <= 0:
                    dead.append(e)
        
        for e in self._entities:
            if isinstance(e, Predator):
                if e.hunger >= getattr(e, 'hp_regen_threshold', 80):
                    e.hp = min(e.hp + getattr(e, 'hp_regen_rate', 0.05), e.dna.hp)
                elif e.hunger <= getattr(e, 'hp_damage_threshold', 20):
                    e.hp -= (getattr(e, 'hp_damage_threshold', 20) - e.hunger) * getattr(e, 'hp_damage_rate', 0.01)
                    if e.hp <= 0:
                        dead.append(e)
                        continue
                if e.hunger <= 0:
                    dead.append(e)
                    
                
        # TestEntity — смерть от голода или HP
        for e in self._entities:
            if isinstance(e, Human):
                e.update(self._objects, self._entities)

        self._total_deaths += len(dead)

        # =============================================
        # СМЕРТЬ: удобрение почвы
        # =============================================
        for e in dead:
            if e in self._entities:
                for _ in range(3):
                    x = e.pos.x + random.randint(-20, 20)
                    y = e.pos.y + random.randint(-20, 20)
                    plant = Plant(x, y)
                    plant.food_value = plant.max_food * 1.5
                    self._objects.append(plant)
                self._entities.remove(e)
                
        # =============================================
        # РОСТ, СТАРЕНИЕ, КУЛДАУНЫ
        # =============================================
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                if e.size < e.max_size:
                    e.size += e.growth_rate
                    if e.size > e.max_size:
                        e.size = e.max_size
                e.age += 1
                if e.breed_cooldown > 0:
                    e.breed_cooldown -= 1
        
        # =============================================
        # РАЗМНОЖЕНИЕ
        # =============================================
        new_borns = []
        for i in range(len(self._entities)):
            for j in range(i+1, len(self._entities)):
                e1, e2 = self._entities[i], self._entities[j]
                if isinstance(e1, Peaceful) and isinstance(e2, Peaceful):
                    if (e1.hunger >= e1.breed_hunger and e2.hunger >= e2.breed_hunger and
                        e1.hp >= e1.dna.hp * e1.breed_hp_threshold and e2.hp >= e2.dna.hp * e2.breed_hp_threshold and
                        e1.age >= e1.breeding_age and e2.age >= e2.breeding_age and
                        e1.breed_cooldown <= 0 and e2.breed_cooldown <= 0):
                        if e1.pos.distance_to(e2.pos) < 30:
                            if random.random() < e1.breed_chance:
                                child_dna = e1.dna.breed(e2.dna)
                                child = Peaceful((e1.pos.x + e2.pos.x) / 2, (e1.pos.y + e2.pos.y) / 2)
                                child.dna = child_dna
                                child.max_size = child_dna.size
                                child.size = child.max_size * 0.4
                                child.growth_rate = child.max_size / getattr(e1, 'growth_divider', 600)
                                child.speed = (-child_dna.speed, child_dna.speed)
                                child.color = mix_colors(e1.color, e2.color)
                                new_borns.append(child)
                                e1.hunger -= e1.breed_hunger * 0.5
                                e2.hunger -= e2.breed_hunger * 0.5
                                e1.breed_cooldown = int(e1.breed_cooldown_base + e1.dna.size * e1.breed_cooldown_per_size)
                                e2.breed_cooldown = int(e2.breed_cooldown_base + e2.dna.size * e2.breed_cooldown_per_size)
                                
                elif isinstance(e1, Predator) and isinstance(e2, Predator):
                    if (e1.hunger >= e1.breed_hunger and e2.hunger >= e2.breed_hunger and
                        e1.age >= e1.breeding_age and e2.age >= e2.breeding_age and
                        e1.breed_cooldown <= 0 and e2.breed_cooldown <= 0):
                        if e1.pos.distance_to(e2.pos) < 30:
                            if random.random() < e1.breed_chance:
                                child_dna = e1.dna.breed(e2.dna)
                                child = Predator((e1.pos.x + e2.pos.x) / 2, (e1.pos.y + e2.pos.y) / 2)
                                child.dna = child_dna
                                child.max_size = child_dna.size
                                child.size = child.max_size * 0.4
                                child.growth_rate = child.max_size / getattr(e1, 'growth_divider', 900)
                                child.speed = (-child_dna.speed, child_dna.speed)
                                child.color = mix_colors(e1.color, e2.color)
                                child.hunger = getattr(e1, 'child_hunger', 70)
                                new_borns.append(child)
                                e1.hunger -= e1.breed_hunger * 0.5
                                e2.hunger -= e2.breed_hunger * 0.5
                                e1.breed_cooldown = int(e1.breed_cooldown_base + e1.dna.size * e1.breed_cooldown_per_size)
                                e2.breed_cooldown = int(e2.breed_cooldown_base + e2.dna.size * e2.breed_cooldown_per_size)

        for child in new_borns:
            self._entities.append(child)
        
        # =============================================
        # КАМЕРА, ТРАВА, ИСТОЩЕНИЕ, ГРАНИЦЫ
        # =============================================
        if self._follow_target and self._follow_target in self._entities:
            self._camera.x = self._follow_target.pos.x - self.width / 2
            self._camera.y = self._follow_target.pos.y - self.height / 2
        
        for obj in self._objects:
            if isinstance(obj, Plant):
                obj.regrow()
        
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                if e.hunger < 30:
                    starvation_size = e.max_size * (0.5 + e.hunger / 60)
                    if starvation_size < e.size:
                        e.size = starvation_size
        
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                e.avoid_boundaries(self._world_offset_x, self._world_offset_y, 
                                self._world_width, self._world_height)
                e.add_random_deviation(0.2)
        
        # =============================================
        # АНТИ-ЗАСТРЕВАНИЕ
        # =============================================
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                # Мирные в логове — не трогать
                if isinstance(e, Peaceful) and e.state == "rest":
                    continue
                
                if not hasattr(e, 'stuck_frames'):
                    e.stuck_frames = 0
                    e.last_stuck_pos = Vector(e.pos.x, e.pos.y)
                
                dist = e.pos.distance_to(e.last_stuck_pos)
                
                if dist < 1:
                    e.stuck_frames += 1
                else:
                    e.stuck_frames = max(0, e.stuck_frames - 1)
                
                e.last_stuck_pos = Vector(e.pos.x, e.pos.y)
                
                # Застрял на 2+ секунды — мягкий толчок и сброс целей
                if e.stuck_frames > 120:
                    angle = random.uniform(0, 2 * math.pi)
                    e.pos.x += math.cos(angle) * 5
                    e.pos.y += math.sin(angle) * 5
                    e.state = "wander" if isinstance(e, Predator) else "graze"
                    e.target = None
                    e.target_mate = None
                    if hasattr(e, 'patrol_target'):
                        e.patrol_target = None
                        e.patrol_steps = 0
                    if hasattr(e, 'flee_vx'):
                        e.flee_vx = 0
                        e.flee_vy = 0
                    e.stuck_frames = 0
            
        
        self._ground.after(delay, lambda: self.update(FPS))
                
    def add_entity(self, entity):
        """Добавить существо в симуляцию."""
        self._entities.append(entity)
        
    def add_object(self, object):
        """Добавить статический объект в симуляцию."""
        self._objects.append(object)
        
    def spawn_den(self, x, y, size=40):
        """Создать логово (убежище для мирных).
        
        Args:
            x, y: координаты центра
            size: радиус логова
        """
        from SandBox.objects import Den
        den = Den(x, y, size=size)
        self._objects.append(den)
        
    def _on_mouse_move(self, event):
        """Обновить ховер на логовах при движении мыши"""
        from SandBox.objects import Den
        world_x, world_y = self._camera.screen_to_world(event.x, event.y)
        mouse_pos = Vector(world_x, world_y)
        for obj in self._objects:
            if isinstance(obj, Den):
                obj.update_hover(mouse_pos)
        for e in self._entities:
            e.update_hover(mouse_pos)
        
    def on_click(self, event):
        """ПКМ: показать информацию о существе под курсором."""
        clicked = None
        for e in self._entities:
            screen_x, screen_y = self._camera.world_to_screen(e.pos.x, e.pos.y)
            dist = math.sqrt((event.x - screen_x)**2 + (event.y - screen_y)**2)
            if dist < e.size + 5:
                clicked = e
                break
        
        self._selected_entity = clicked
        
        if clicked:
            self._selected_entity = clicked
            self._follow_target = clicked
            self._update_info_label()
        else:
            self._selected_entity = None
            self._follow_target = None
            self._info_label.config(text="")

    def _update_info_label(self):
        """Обновить инфо-панель: тип, размер, голод, HP, ДНК, возраст."""
        from SandBox.entities import Peaceful, Predator
        from SandBox.player import Player
        if not self._selected_entity:
            self._info_label.config(text="")
            return
        
        clicked = self._selected_entity
        info_lines = []
        
        if isinstance(clicked, Predator):
            info_lines.append("Type: Predator")
        elif isinstance(clicked, Peaceful):
            info_lines.append("Type: Peaceful")
        elif isinstance(clicked, Player):
            info_lines.append("Type: Player")
        else:
            info_lines.append("Type: Entity")
        
        info_lines.append(f"Size: {clicked.size:.1f}")
        info_lines.append(f"Speed: {clicked.dna.speed:.1f}")
        
        hunger = getattr(clicked, 'hunger', None)
        if hunger is not None:
            info_lines.append(f"Hunger: {hunger:.1f}")
        
        hp = getattr(clicked, 'hp', None)
        if hp is not None:
            info_lines.append(f"HP: {hp:.1f}")
        
        info_lines.append(f"DNA Size: {clicked.dna.size:.1f}")
        info_lines.append(f"Nutrition: {clicked.nutrition_value}")
        
        if hasattr(clicked, 'starvation_threshold'):
            info_lines.append(f"Starvation: {clicked.starvation_threshold:.1f}")
        
        if not isinstance(clicked, Peaceful):
            info_lines.append(f"Attack: {clicked.dna.attack:.1f}")
            info_lines.append(f"Courage: {clicked.dna.courage:.2f}")
        
        age = getattr(clicked, 'age', None)
        if age is not None:
            info_lines.append(f"Age: {age / 60:.1f}s")
        
        cooldown = getattr(clicked, 'breed_cooldown', None)
        if cooldown is not None and cooldown > 0:
            info_lines.append(f"Breed CD: {cooldown / 60:.1f}s")
        
        info_lines.append(f"Family: {clicked.dna.family_id}")
        
        self._info_label.config(text="\n".join(info_lines))
        
    def on_double_click(self, event):
        """Двойной клик: переместить игрока в точку."""
        if self._player:
            world_x, world_y = self._camera.screen_to_world(event.x, event.y)
            world_x = max(self._world_offset_x + 10, min(world_x, self._world_offset_x + self._world_width - 10))
            world_y = max(self._world_offset_y + 10, min(world_y, self._world_offset_y + self._world_height - 10))
            self._player.set_target(world_x, world_y)
            
    def _on_camera_drag_start(self, event):
        """Начало перетаскивания камеры (средняя кнопка мыши)."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _on_camera_drag(self, event):
        """Перетаскивание камеры."""
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self._camera.x -= dx / self._camera.zoom
        self._camera.y -= dy / self._camera.zoom
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _on_camera_drag_end(self, event):
        """Конец перетаскивания камеры."""
        pass


class Vector:
    """2D вектор для позиций, скорости и расстояний."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def distance_to(self, other):
        """Евклидово расстояние до другого вектора."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx**2 + dy**2)
        
    def __str__(self):
        return f"Vector({self.x}, {self.y})"
    
    def length(self):
        """Длина (модуль) вектора."""
        return math.sqrt(self.x ** 2 + self.y ** 2)


class SpatialGrid:
    """Пространственная сетка для быстрого поиска соседей (коллизии).
    
    Разбивает мир на клетки размером cell_size и хранит сущности в ячейках.
    """
    
    def __init__(self, cell_size=100):
        self.cell_size = cell_size
        self.grid = {}
    
    def clear(self):
        """Очистить сетку перед новым кадром."""
        self.grid.clear()
    
    def add(self, entity):
        """Добавить сущность в соответствующую ячейку."""
        col = int(entity.pos.x // self.cell_size)
        row = int(entity.pos.y // self.cell_size)
        key = (col, row)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)
    
    def get_nearby(self, entity):
        """Вернуть список сущностей в текущей и соседних ячейках."""
        col = int(entity.pos.x // self.cell_size)
        row = int(entity.pos.y // self.cell_size)
        nearby = []
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                key = (col + dc, row + dr)
                if key in self.grid:
                    nearby.extend(self.grid[key])
        return nearby


if __name__ == '__main__':
    try:
        game = SandBox()
        game()
    except KeyboardInterrupt:
        print('=== SandBox Was Closed ===')

project = 'Песочница на tkinter с NPC и простым AI'

# SandBox/core.py
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
    '''Песочница для размещения обьектов'''
    def __init__(self, collision_enabled=True, world_height=5000, world_width=5000, show_borders=True):
        """Создать песочницу с холстом"""
        
        from SandBox.entities import Entity, Peaceful, Predator
        from SandBox.objects import StaticObject, Plant
        from SandBox.player import Player, Camera
            
        self._ground = tk.Tk()
        self._ground.title('SandBox')
        self._ground.state('zoomed')
        self._ground.config(bg="#E7E7E7")
        self._collision_enabled = collision_enabled
        self._ground.bind("<Double-Button-1>", self.on_double_click)
        self._ground.bind("<Button-3>", self.on_click)
        self._ground.bind("<ButtonPress-2>", self._on_camera_drag_start)
        self._ground.bind("<B2-Motion>", self._on_camera_drag)
        self._ground.bind("<ButtonRelease-2>", self._on_camera_drag_end)
        
        self._world_width = world_width  
        self._world_height = world_height
        self._world_offset_x = -world_width // 2  
        self._world_offset_y = -world_height // 2
        
        self._fps_counter = 0
        self._fps_timer = time.time()
        self._last_fps = 0
        
        self._follow_target = None
        self._selected_entity = None
        
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
        return f"Проект: {project}"
    
    def __repr__(self):
        return f"Project('{project}')"
    
    def __call__(self, FPS=60):
        """Запуск песочницы"""
        self.update(FPS)
        self._ground.mainloop()
        
    @property
    def width(self):
        return self._canvas.winfo_width()

    @property
    def height(self):
        return self._canvas.winfo_height()
        
        
    def create_player(self, color="#00FF00", speed=3):
        from SandBox.player import Player 
        self._player = Player(600, 375, color=color, speed=speed) 
        self.add_entity(self._player)
        
        
    def spawn_random_entities(self, count, *types, color=None, **kwargs):
        """Создать случайных Entity указанных типов"""
        from SandBox.entities import Entity
        if not types:
            types = (Entity,)  # по умолчанию обычные Entity
        
        for i in range(count):
            entity_type = random.choice(types)  # случайный тип!
            x = random.randint(self._world_offset_x + 50, self._world_offset_x + self._world_width - 50)
            y = random.randint(self._world_offset_y + 50, self._world_offset_y + self._world_height - 50)
            
            if color:
                entity = entity_type(x, y, color=color, **kwargs)
            else:
                entity = entity_type(x, y, **kwargs)
            
            self._entities.append(entity)
                            
    def spawn_random_objects(self, count, color="#AFAEAE", form='rectangle'):
        """Создать случайных Object в количестве count"""
        from SandBox.objects import StaticObject 
        for i in range(count):
            x = random.randint(self._world_offset_x + 50, self._world_offset_x + self._world_width - 50)
            y = random.randint(self._world_offset_y + 50, self._world_offset_y + self._world_height - 50)
            object = StaticObject(x, y, color, form)
            self._objects.append(object)
            
    def draw_all(self):
        """Нарисовать всех Entity и Object на холсте"""
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
        """Проверить столкновения и не дать пройти сквозь"""
        from SandBox.entities import Peaceful
        if self._collision_enabled:
            # Entity ↔ Entity (через SpatialGrid)
            self._grid.clear()
            for e in self._entities:
                self._grid.add(e)
            
            for entity in self._entities:
                if entity == self._player: 
                    continue
                if isinstance(entity, Peaceful) and getattr(entity, 'state', None) == "flee":
                    continue  # убегающих не отталкивать!
                nearby = self._grid.get_nearby(entity)
                for other in nearby:
                    if other == self._player:
                        continue
                    if isinstance(other, Peaceful) and getattr(other, 'state', None) == "flee":
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
                if isinstance(entity, Peaceful) and getattr(entity, 'state', None) == "flee":
                    continue  # убегающих не отталкивать от стен!
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
                            
            # Закреп у границ мира с мягким отталкиванием
            margin = 50
            for entity in self._entities:
                left = self._world_offset_x + margin
                right = self._world_offset_x + self._world_width - margin
                top = self._world_offset_y + margin
                bottom = self._world_offset_y + self._world_height - margin
                
                # Мягкое отталкивание вместо жёсткого закрепа
                if entity.pos.x < left:
                    entity.pos.x += (left - entity.pos.x) * 0.3
                elif entity.pos.x > right:
                    entity.pos.x += (right - entity.pos.x) * 0.3
                
                if entity.pos.y < top:
                    entity.pos.y += (top - entity.pos.y) * 0.3
                elif entity.pos.y > bottom:
                    entity.pos.y += (bottom - entity.pos.y) * 0.3
                    
    def spawn_plants(self, clusters=10, min_plants=10, max_plants=25, spread=100):
        """Засеять траву"""
        from SandBox.objects import Plant
        for _ in range(clusters):
            # Центр кучки
            cx = random.randint(self._world_offset_x + 200, self._world_offset_x + self._world_width - 200)
            cy = random.randint(self._world_offset_y + 200, self._world_offset_y + self._world_height - 200)
            
            # Случайное количество растений в кучке
            count = random.randint(min_plants, max_plants)
            
            for _ in range(count):
                # Случайные координаты внутри кучки (процент от spread)
                x = cx + random.randint(-spread, spread)
                y = cy + random.randint(-spread, spread)
                plant = Plant(x, y)
                self._objects.append(plant)
                    
            
    def update(self, FPS=60):
        '''Игровой цикл, воспроизводится каждый кадр'''
        from SandBox.entities import Entity, Peaceful, Predator, mix_colors
        from SandBox.objects import Plant
        delay = 1000 // FPS
        
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
        
        # Обновлять инфо-панель каждый кадр
        if self._selected_entity:
            if self._selected_entity in self._entities:
                self._update_info_label()
            else:
                self._selected_entity = None
                self._info_label.config(text="")
        
        self.draw_all()
        for e in self._entities:
            if e != self._player and not isinstance(e, Predator) and not isinstance(e, Peaceful):
                e.move_random(self._world_width, self._world_height)
        
        self.check_collision()
        
        if self._player:
            self._player.move_to_target()
            
        # Хищники — охота или размножение
        victims_to_remove = []
        for e in self._entities:
            if isinstance(e, Predator):
                # Сначала ищем партнёра
                mate = e.find_mate(self._entities)
                if mate:
                    e.state = "seek_mate"
                    e.target_mate = mate
                    dx = mate.pos.x - e.pos.x
                    dy = mate.pos.y - e.pos.y
                    dist = Vector(dx, dy).length()
                    if dist > 0:
                        speed = e.dna.speed * 0.8
                        e.pos.x += (dx / dist) * speed
                        e.pos.y += (dy / dist) * speed
                    e.hunger -= 0.01  # Поиск партнёра дёшев
                else:
                    # Нет партнёра — охотимся
                    e.find_target(self._entities)
                    victim = e.chase_target(self._world_width, self._world_height)
                    if victim and victim in self._entities:
                        victims_to_remove.append((e, victim))
                    
        for predator, victim in victims_to_remove:
            if victim in self._entities:
                self._entities.remove(victim)
        self._total_kills += len(victims_to_remove)
        
        # Peaceful — поведение
        dead = []
        for e in self._entities:
            if isinstance(e, Peaceful):
                hunger_mod = 0.5 + (e.hunger / 100) * 0.5
                hp_mod = 0.6 + (e.hp / e.dna.hp) * 0.4
                
                threat, dist = e.see_predator(self._entities)
                
                if threat:
                    # Бегство — мирные медленнее хищников!
                    if dist < 50:
                        speed_mult = 1.2 * hunger_mod * hp_mod  # Было 2.0
                        hunger_cost = 0.08  # Паника затратна
                    elif dist < 100:
                        speed_mult = 1.0 * hunger_mod * hp_mod  # Было 1.5
                        hunger_cost = 0.05
                    else:
                        speed_mult = 0.8 * hunger_mod * hp_mod  # Было 1.2
                        hunger_cost = 0.03
                    
                    dx = e.pos.x - threat.pos.x
                    dy = e.pos.y - threat.pos.y
                    if dist > 0:
                        target_vx = (dx / dist) * e.dna.speed * speed_mult
                        target_vy = (dy / dist) * e.dna.speed * speed_mult
                        e.flee_vx += (target_vx - e.flee_vx) * 0.3
                        e.flee_vy += (target_vy - e.flee_vy) * 0.3
                        e.pos.x += e.flee_vx
                        e.pos.y += e.flee_vy
                    e.hunger -= hunger_cost
                    e.state = "flee"
                    e.target_mate = None
                else:
                    mate = e.find_mate(self._entities)
                    if mate:
                        e.state = "seek_mate"
                        e.target_mate = mate
                        dx = mate.pos.x - e.pos.x
                        dy = mate.pos.y - e.pos.y
                        dist = Vector(dx, dy).length()
                        if dist > 0:
                            speed = e.dna.speed * 0.7 * hunger_mod * hp_mod
                            e.pos.x += (dx / dist) * speed
                            e.pos.y += (dy / dist) * speed
                        e.hunger -= 0.02
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
                                speed = e.dna.speed * 0.3 * hunger_mod * hp_mod
                                e.pos.x += (dx / dist) * speed
                                e.pos.y += (dy / dist) * speed
                                e.state = "graze"
                            e.hunger -= 0.008
                        else:
                            e.state = "wander"
                            e.move_random(self._world_width, self._world_height)
                            # Базовый метаболизм зависит от размера
                            base_metabolism = 0.003 + (e.dna.size / 10) * 0.004
                            e.hunger -= base_metabolism
                
                # Голод влияет на здоровье
                if e.hunger > 80:
                    e.hp = min(e.hp + 0.05, e.dna.hp)
                elif e.hunger < 20:
                    e.hp -= (20 - e.hunger) * 0.01
                
                if e.hunger <= 0:
                    dead.append(e)
        
        for e in self._entities:
            if isinstance(e, Predator):
                # Голод влияет на здоровье хищников
                if e.hunger > 80:
                    e.hp = min(e.hp + 0.05, e.dna.hp)
                elif e.hunger < 20:
                    e.hp -= (20 - e.hunger) * 0.01
                
                if e.hunger <= 0:
                    dead.append(e)

        self._total_deaths += len(dead)

        for e in dead:
            
            if e in self._entities:
                # Удобрение почвы
                for _ in range(3):
                    x = e.pos.x + random.randint(-20, 20)
                    y = e.pos.y + random.randint(-20, 20)
                    plant = Plant(x, y)
                    plant.food_value = plant.max_food * 1.5
                    self._objects.append(plant)
                self._entities.remove(e)
                
        # Старение, рост и кулдауны
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                # Рост до максимального размера
                if e.size < e.max_size:
                    e.size += e.growth_rate
                    if e.size > e.max_size:
                        e.size = e.max_size
                
                e.age += 1
                if e.breed_cooldown > 0:
                    e.breed_cooldown -= 1
        
        # Размножение
        new_borns = []
        for i in range(len(self._entities)):
            for j in range(i+1, len(self._entities)):
                e1, e2 = self._entities[i], self._entities[j]
                if isinstance(e1, Peaceful) and isinstance(e2, Peaceful):
                    if (e1.hunger > 50 and e2.hunger > 50 and  # Было 70
                        e1.hp > e1.dna.hp * 0.5 and e2.hp > e2.dna.hp * 0.5 and  # Было 0.7
                        e1.age >= e1.breeding_age and e2.age >= e2.breeding_age and
                        e1.breed_cooldown <= 0 and e2.breed_cooldown <= 0):

                        if e1.pos.distance_to(e2.pos) < 30:
                            if random.random() < 0.1:
                                child_dna = e1.dna.breed(e2.dna)
                                child = Peaceful(
                                    (e1.pos.x + e2.pos.x) / 2,
                                    (e1.pos.y + e2.pos.y) / 2
                                )
                                child.dna = child_dna
                                child.max_size = child_dna.size
                                child.size = child.max_size * 0.4
                                child.growth_rate = child.max_size / 600
                                child.speed = (-child_dna.speed, child_dna.speed)
                                child.color = mix_colors(e1.color, e2.color)
                                new_borns.append(child)
                                e1.hunger -= 25
                                e2.hunger -= 25
                                e1.breed_cooldown = int(200 + e1.dna.size * 20)
                                e2.breed_cooldown = int(200 + e2.dna.size * 20)
                                
                elif isinstance(e1, Predator) and isinstance(e2, Predator):
                    if (e1.hunger > 75 and e2.hunger > 75 and
                        e1.age >= e1.breeding_age and e2.age >= e2.breeding_age and
                        e1.breed_cooldown <= 0 and e2.breed_cooldown <= 0):
                        if e1.pos.distance_to(e2.pos) < 30:
                            if random.random() < 0.006:
                                child_dna = e1.dna.breed(e2.dna)
                                child = Predator(
                                    (e1.pos.x + e2.pos.x) / 2,
                                    (e1.pos.y + e2.pos.y) / 2
                                )
                                child.dna = child_dna
                                child.max_size = child_dna.size
                                child.size = child.max_size * 0.4
                                child.growth_rate = child.max_size / 900
                                child.speed = (-child_dna.speed, child_dna.speed)
                                child.color = mix_colors(e1.color, e2.color)
                                child.hunger = 70
                                new_borns.append(child)
                                e1.hunger -= 35
                                e2.hunger -= 35
                                e1.breed_cooldown = int(400 + e1.dna.size * 30)
                                e2.breed_cooldown = int(400 + e2.dna.size * 30)

        for child in new_borns:
            self._entities.append(child)
        
        if self._follow_target and self._follow_target in self._entities:
            self._camera.x = self._follow_target.pos.x - self.width / 2
            self._camera.y = self._follow_target.pos.y - self.height / 2
        
        # Рост травы
        for obj in self._objects:
            if isinstance(obj, Plant):
                obj.regrow()
                
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                if e.hunger < 30:
                    # Истощение: временно уменьшаем размер
                    starvation_size = e.max_size * (0.5 + e.hunger / 60)
                    if starvation_size < e.size:  # Не даём истощению ускорить рост
                        e.size = starvation_size
                        
        for e in self._entities:
            if isinstance(e, (Peaceful, Predator)):
                e.avoid_boundaries(
                    self._world_offset_x, 
                    self._world_offset_y, 
                    self._world_width, 
                    self._world_height
                )
                # Лёгкое случайное отклонение чтобы не застревать
                e.add_random_deviation(0.2)
        
        self._ground.after(delay, lambda: self.update(FPS))
                
    def add_entity(self, entity):
        """Добавить Entity в песочницу"""
        self._entities.append(entity)
        
    def add_object(self, object):
        """Добавить Object в песочницу"""
        self._objects.append(object)
        
    def on_click(self, event):
        '''Показать инфо об Entity по правому клику'''

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
            self._follow_target = clicked  # ← следить за выбранным!
            self._update_info_label()
        else:
            self._selected_entity = None
            self._follow_target = None  # ← перестать следить
            self._info_label.config(text="")

    def _update_info_label(self):
        """Обновить инфо-панель для выбранного Entity"""
        from SandBox.entities import Peaceful, Predator
        from SandBox.player import Playe
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
        
        # Возраст и кулдаун в секундах
        age = getattr(clicked, 'age', None)
        if age is not None:
            info_lines.append(f"Age: {age / 60:.1f}s")
        
        cooldown = getattr(clicked, 'breed_cooldown', None)
        if cooldown is not None and cooldown > 0:
            info_lines.append(f"Breed CD: {cooldown / 60:.1f}s")
        
        # Семейный ID
        info_lines.append(f"Family: {clicked.dna.family_id}")
        
        self._info_label.config(text="\n".join(info_lines))
        
        
    def on_double_click(self, event):
        '''Установить позицию игрока по нажатию'''
        if self._player:
            world_x, world_y = self._camera.screen_to_world(event.x, event.y)
            world_x = max(self._world_offset_x + 10, min(world_x, self._world_offset_x + self._world_width - 10))
            world_y = max(self._world_offset_y + 10, min(world_y, self._world_offset_y + self._world_height - 10))
            self._player.set_target(world_x, world_y)

            
            
    def _on_camera_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _on_camera_drag(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self._camera.x -= dx / self._camera.zoom
        self._camera.y -= dy / self._camera.zoom
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _on_camera_drag_end(self, event):
        pass

    
        
        
class Vector:
    """2D вектор для позиций и движения"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def distance_to(self, other):
        """Расстояние до другого вектора"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx**2 + dy**2)
        
    def __str__(self):
        return f"Vector({self.x}, {self.y})"
    
    
    def length(self):
        """Вернуть длину вектора"""
        return math.sqrt(self.x ** 2 + self.y ** 2)

class SpatialGrid:
    """Разбивает мир на клетки для быстрых коллизий"""
    def __init__(self, cell_size=100):
        self.cell_size = cell_size
        self.grid = {}
    
    def clear(self):
        self.grid.clear()
    
    def add(self, entity):
        col = int(entity.pos.x // self.cell_size)
        row = int(entity.pos.y // self.cell_size)
        key = (col, row)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)
    
    def get_nearby(self, entity):
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
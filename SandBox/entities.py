# Copyright (c) 2026 CeTzyyy. All rights reserved.
# Licensed under SandBox Engine License. See LICENSE file in the project root for full license information.

"""
Модуль сущностей экосистемы SandBox Engine.
Содержит базовые классы Entity, DNA, хищников (Predator), мирных (Peaceful).
"""

import math
import random
from .core import Vector


class Entity:
    """Базовый класс для всех живых объектов в песочнице.
    
    Имеет позицию (Vector), ДНК, цвет и умеет рисовать себя на Canvas.
    От этого класса наследуются Peaceful, Predator и Player.
    
    Attributes:
        pos (Vector): позиция в мировых координатах
        dna (DNA): генетический код существа
        size (float): текущий размер (растёт с возрастом)
        color (str): hex-цвет для отрисовки
        form (str): 'oval' или 'rectangle'
        static (bool): если True — не двигается
    """
    
    def __init__(self, x, y, color="#00FF1E", static=False, form='oval', boundary_check=False, dna=None):
        """Создать Entity.
        
        Args:
            x (float): начальная позиция X
            y (float): начальная позиция Y
            color (str): hex-цвет
            static (bool): неподвижный объект
            form (str): 'oval' или 'rectangle'
            boundary_check (bool): проверять границы мира
            dna (DNA|None): генетический код (если None — создаётся новый)
        """
        self.dna = dna if dna is not None else DNA()
        self.pos = Vector(x, y)
        self.speed = (-self.dna.speed, self.dna.speed)
        self.size = self.dna.size
        self.nutrition_value = self.dna.nutrition_value
        self.color = color
        self.static = static
        self.form = form
        self.boundary_check = boundary_check
        self.vx = 0
        self.vy = 0
        self.timer = random.randint(30, 60)
        self.hovered = False

    def __str__(self):
        return f"Entity at {self.pos}"

    def __repr__(self):
        return f"Entity({self.pos.x}, {self.pos.y}, '{self.color}')"
    
    def update_hover(self, mouse_world_pos):
        if mouse_world_pos:
            dist = self.pos.distance_to(mouse_world_pos)
            self.hovered = dist < self.size + 5
        else:
            self.hovered = False


    def draw(self, pil_draw, camera=None):
        """Отрисовать Entity на холсте.
        
        Args:
            pil_draw (ImageDraw): объект для рисования
            camera (Camera|None): камера для преобразования координат
        """
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y
            
        if self.hovered:
            pil_draw.ellipse([x - self.size - 2, y - self.size - 2, x + self.size + 2, y + self.size + 2], 
                            outline="yellow", width=2)

        if self.form == 'oval':
            pil_draw.ellipse([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)
        elif self.form == 'rectangle':
            pil_draw.rectangle([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)
            
        if getattr(self, 'hovered', False):
            pil_draw.ellipse([x - self.size - 2, y - self.size - 2, x + self.size + 2, y + self.size + 2], 
                            outline="yellow", width=2)
            
            hp = int(getattr(self, 'hp', 0)) if hasattr(self, 'hp') else '?'
            hunger = int(getattr(self, 'hunger', 0)) if hasattr(self, 'hunger') else '?'
            text = f"HP:{hp} Hung:{hunger}"
            pil_draw.text((x + self.size + 5, y - 10), text, fill="black")
            
    def move_to(self, x, y):
        """Телепортировать Entity в указанную точку.
        
        Args:
            x (float): новая позиция X
            y (float): новая позиция Y
        """
        self.pos.x = x
        self.pos.y = y

    def move_random(self, world_width, world_height):
        """Случайное патрулирование с учётом голода и здоровья.
        Используется для Entity, не являющихся Peaceful или Predator.
        
        Args:
            world_width (int): ширина мира
            world_height (int): высота мира
        """
        if hasattr(self, 'hunger'):
            self.hunger -= self.wander_cost

        if hasattr(self, 'hunger') and hasattr(self, 'hp'):
            hunger_mod = 0.5 + (self.hunger / 100) * 0.5
            hp_mod = 0.6 + (self.hp / self.dna.hp) * 0.4
            speed_mult = hunger_mod * hp_mod
        else:
            speed_mult = 1.0

        if not hasattr(self, 'wander_target') or self.wander_target is None or self.pos.distance_to(self.wander_target) < 30:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(50, 150)
            self.wander_target = Vector(
                self.pos.x + math.cos(angle) * distance,
                self.pos.y + math.sin(angle) * distance
            )

        if self.wander_target:
            dx = self.wander_target.x - self.pos.x
            dy = self.wander_target.y - self.pos.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                speed = self.dna.speed * speed_mult
                self.pos.x += (dx / dist) * speed
                self.pos.y += (dy / dist) * speed

    def avoid_boundaries(self, world_offset_x, world_offset_y, world_width, world_height):
        """Oтталкивание от границ мира.
        Ecли cилa тoлчкa бoльшaя — cбpacываeт цeль пaтpyля/блyждaния.
        
        Args:
            world_offset_x (int): левая граница мира
            world_offset_y (int): верхняя граница мира
            world_width (int): ширина мира
            world_height (int): высота мира
        """
        margin = 80
        left = world_offset_x + margin
        right = world_offset_x + world_width - margin
        top = world_offset_y + margin
        bottom = world_offset_y + world_height - margin

        force_x = 0
        force_y = 0

        if self.pos.x < left:
            force_x = (left - self.pos.x) * 0.4
        elif self.pos.x > right:
            force_x = (right - self.pos.x) * 0.4

        if self.pos.y < top:
            force_y = (top - self.pos.y) * 0.4
        elif self.pos.y > bottom:
            force_y = (bottom - self.pos.y) * 0.4

        self.pos.x += force_x
        self.pos.y += force_y

        if abs(force_x) > 3 or abs(force_y) > 3:
            if hasattr(self, 'wander_target'):
                self.wander_target = None
            if hasattr(self, 'patrol_target'):
                self.patrol_target = None

    def add_random_deviation(self, strength=0.3):
        """Добавить случайное смещение для реалистичности движения.
        
        Args:
            strength (float): максимальная величина смещения в пикселях
        """
        self.pos.x += random.uniform(-strength, strength)
        self.pos.y += random.uniform(-strength, strength)

    def is_colliding_with(self, other):
        """Проверить столкновение с другим объектом.
        
        Args:
            other: другой Entity или StaticObject
            
        Returns:
            bool: True если объекты перекрываются
        """
        return self.pos.distance_to(other.pos) < self.size + other.size

    def death(self):
        """Заглушка смерти. Переопределяется в наследниках."""
        pass


class Predator(Entity):
    """Хищник. Охотится на Peaceful, патрулирует территорию, размножается.
    
    Имеет память мест охоты, умный патруль с длинными перегонами,
    зрение зависящее от голода, и приоритеты: еда > размножение > патруль.
    
    Attributes:
        state (str): 'hunt', 'patrol', 'seek_mate', 'wander'
        memory (list): список [x, y, ценность] мест успешной охоты
        target (Peaceful|None): текущая цель охоты
        target_mate (Predator|None): текущий партнёр для размножения
    """
    
    def __init__(self, x, y, color="#FF4500",
                 breed_chance=0.006, breeding_age=400, child_size_percent=0.4,
                 growth_divider=900, start_hunger_min=85, start_hunger_max=100,
                 child_hunger=70, hunt_threshold=85,
                 chase_speed=2.5, patrol_speed=0.8,
                 vision=200, vision_hungry=350,
                 base_cost=0.008, cost_per_size=0.008,
                 hunt_cost=0.02, hunt_cost_per_size=0.01,
                 patrol_cost=0.005, patrol_cost_per_size=0.005,
                 breed_hunger=75, breed_cooldown_base=400, breed_cooldown_per_size=30,
                 memory_size=5, memory_decay=0.05, memory_chance=0.35):
        """Создать хищника.
        
        Args:
            x, y (float): начальная позиция
            color (str): hex-цвет
            breed_chance (float): шанс размножения за кадр (0..1)
            breeding_age (int): возраст зрелости в кадрах
            child_size_percent (float): начальный размер ребёнка от max_size
            growth_divider (float): делитель для скорости роста
            start_hunger_min, start_hunger_max (float): диапазон стартового голода
            child_hunger (float): голод новорождённого
            hunt_threshold (float): порог голода для начала охоты
            chase_speed (float): множитель скорости погони
            patrol_speed (float): множитель скорости патруля
            vision (float): дальность зрения сытого
            vision_hungry (float): дальность зрения голодного
            base_cost (float): базовый расход голода (метаболизм)
            cost_per_size (float): добавка к метаболизму за размер
            hunt_cost (float): расход голода при охоте
            hunt_cost_per_size (float): добавка к стоимости охоты за размер
            patrol_cost (float): расход голода при патруле
            patrol_cost_per_size (float): добавка к стоимости патруля за размер
            breed_hunger (float): минимальный голод для спаривания
            breed_cooldown_base (int): базовый кулдаун после родов
            breed_cooldown_per_size (float): добавка к кулдауну за размер
            memory_size (int): сколько мест охоты помнить
            memory_decay (float): затухание ценности воспоминания за кадр
            memory_chance (float): шанс пойти к воспоминанию при патруле
        """
        dna = DNA()
        super().__init__(x, y, color=color, dna=dna)

        self.hunger = random.uniform(start_hunger_min, start_hunger_max)
        self.starvation_threshold = self.dna.starvation_threshold
        self.hp = self.dna.hp
        self.state = "wander"
        self.target = None
        self.patrol_target = None
        self.target_mate = None

        self.memory = []
        self.memory_size = memory_size
        self.memory_decay = memory_decay
        self.memory_chance = memory_chance

        self.new_patrol_target()

        self.breed_chance = breed_chance
        self.breeding_age = breeding_age
        self.breed_cooldown = 0
        self.breed_hunger = breed_hunger
        self.breed_cooldown_base = breed_cooldown_base
        self.breed_cooldown_per_size = breed_cooldown_per_size
        self.child_hunger = child_hunger

        self.hunt_threshold = hunt_threshold
        self.chase_speed = chase_speed
        self.patrol_speed = patrol_speed
        self.vision = vision
        self.vision_hungry = vision_hungry

        self.base_cost = base_cost
        self.cost_per_size = cost_per_size
        self.hunt_cost = hunt_cost
        self.hunt_cost_per_size = hunt_cost_per_size
        self.patrol_cost = patrol_cost
        self.patrol_cost_per_size = patrol_cost_per_size

        self.max_size = self.dna.size
        self.size = self.max_size * child_size_percent
        self.growth_rate = self.max_size / growth_divider
        self.growth_divider = growth_divider

        self.age = 0
        self.stuck_timer = 0
        self.last_pos = Vector(x, y)

    def new_patrol_target(self, world_width=2000, world_height=2000):
        """Выбрать новую цель для патруля.
        С шансом memory_chance идёт к запомненному месту охоты.
        Иначе выбирает случайное направление на 400-800 пикселей и держит его 3-5 секунд.
        
        Args:
            world_width (int): ширина мира
            world_height (int): высота мира
        """
        if self.memory and random.random() < self.memory_chance:
            best = max(self.memory, key=lambda m: m[2])
            self.patrol_target = Vector(best[0], best[1])
            self.patrol_steps = random.randint(120, 240)
            return

        if not hasattr(self, 'patrol_steps') or self.patrol_steps <= 0:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(400, 800)
            self.patrol_target = Vector(
                self.pos.x + math.cos(angle) * distance,
                self.pos.y + math.sin(angle) * distance
            )
            self.patrol_steps = random.randint(180, 300)

    def find_target(self, all_entities):
        """Найти ближайшую жертву среди Peaceful.
        Учитывает зрение (зависит от голода), ослабленность жертвы (HP, голод).
        Если hunger > hunt_threshold — не охотится.
        
        Args:
            all_entities (list): список всех Entity в мире
        """
        metabolism = self.base_cost * (self.dna.size ** 0.75)
        self.hunger -= metabolism

        for mem in self.memory:
            mem[2] -= self.memory_decay
        self.memory = [m for m in self.memory if m[2] > 0]

        if self.hunger > self.hunt_threshold:
            self.target = None
            self.state = "patrol"
            return

        closest_prey = None
        min_dist = float('inf')
        vision_range = self.vision_hungry if self.hunger < 30 else self.vision

        for e in all_entities:
            if isinstance(e, Peaceful) or type(e).__name__ == 'Human':
                weakness_score = (e.dna.hp - e.hp) + (e.hunger < 30) * 50
                dist = self.pos.distance_to(e.pos)

                if dist < vision_range:
                    effective_dist = dist - weakness_score * 2
                    if effective_dist < min_dist:
                        min_dist = effective_dist
                        closest_prey = e

        if closest_prey:
            self.target = closest_prey
            self.state = "hunt"
        else:
            self.target = None
            self.state = "patrol"
        
    def chase_target(self, world_width=1200, world_height=750, all_entities=None):
        """Преследовать цель (охота) или патрулировать территорию.
        
        В режиме охоты (state='hunt'):
            - Двигается к цели с chase_speed
            - При контакте атакует, НО если мирных рядом 5+ — они дают отпор
            - При убийстве запоминает место в memory
        
        В режиме патруля (state='patrol'):
            - Двигается к patrol_target длинными перегонами (600-1000px)
            - С шансом memory_chance идёт к запомненному месту охоты
            - Меняет направление каждые 5-8 секунд (300-500 кадров)
            - При застревании >60 кадров принудительно меняет цель
        
        Args:
            world_width, world_height: размеры мира (не используются, оставлены для совместимости)
            all_entities: список всех Entity для проверки fight_back (мирные дают отпор)
        
        Returns:
            Entity или None: убитая жертва (если удалось убить), иначе None
        """
        hunger_mod = 0.6 + (self.hunger / 100) * 0.4
        hp_mod = 0.5 + (self.hp / self.dna.hp) * 0.5
        
        if not hasattr(self, 'stuck_timer'):
            self.stuck_timer = 0
            self.last_pos = Vector(self.pos.x, self.pos.y)
        if not hasattr(self, 'patrol_steps'):
            self.patrol_steps = 0
        
        if self.pos.distance_to(self.last_pos) < 2:
            self.stuck_timer += 1
        else:
            self.stuck_timer = 0
        self.last_pos = Vector(self.pos.x, self.pos.y)
        
        if self.state == "hunt" and self.target and type(self.target).__name__ in ("Peaceful", "Human"):
            hunt_cost = self.hunt_cost + (self.dna.size / 10) * self.hunt_cost_per_size
            self.hunger -= hunt_cost
            
            if self.stuck_timer > 20:
                self.pos.x += random.uniform(-5, 5)
                self.pos.y += random.uniform(-5, 5)
                self.stuck_timer = 0
            
            victim = self.target
            dx = victim.pos.x - self.pos.x
            dy = victim.pos.y - self.pos.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < self.size + victim.size:
                counter_damage = 0
                if all_entities and hasattr(victim, 'fight_back'):
                    counter_damage = victim.fight_back(self, all_entities)
                
                if counter_damage > 0:
                    self.hp -= counter_damage
                    if dist > 0:
                        self.pos.x -= (dx / dist) * 15
                        self.pos.y -= (dy / dist) * 15
                    self.target = None
                    self.state = "patrol"
                    self.patrol_steps = 0
                    return None
                
                damage_multiplier = 1.0 + (self.hunger < 20) * 0.5
                if type(victim).__name__ == 'Human':
                    damage_multiplier *= 2.0
                damage = self.dna.attack * damage_multiplier
                victim.hp -= damage
                
                if victim.hp <= 0:
                    self.hunger = min(100, self.hunger + victim.nutrition_value * 0.8)
                    self.memory.append([victim.pos.x, victim.pos.y, 100.0])
                    if len(self.memory) > self.memory_size:
                        self.memory.pop(0)
                    self.target = None
                    self.state = "patrol"
                    self.patrol_steps = 0
                    return victim
            else:
                if dist > 0:
                    chase_speed = self.dna.speed * self.chase_speed * hunger_mod * hp_mod
                    self.pos.x += (dx / dist) * chase_speed
                    self.pos.y += (dy / dist) * chase_speed
            return None
        
        else:
            patrol_cost = self.patrol_cost + (self.dna.size / 10) * self.patrol_cost_per_size
            self.hunger -= patrol_cost
            
            self.patrol_steps -= 1
            
            if self.stuck_timer > 60:
                self.patrol_steps = 0
                self.stuck_timer = 0
            
            if not self.patrol_target or self.patrol_steps <= 0:
                if self.memory and random.random() < self.memory_chance:
                    best = max(self.memory, key=lambda m: m[2])
                    self.patrol_target = Vector(best[0], best[1])
                else:
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(600, 1000)
                    self.patrol_target = Vector(
                        self.pos.x + math.cos(angle) * distance,
                        self.pos.y + math.sin(angle) * distance
                    )
                self.patrol_steps = random.randint(300, 500)
            
            dx = self.patrol_target.x - self.pos.x
            dy = self.patrol_target.y - self.pos.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < 40:
                self.patrol_steps = 0
            elif dist > 0:
                patrol_speed = self.dna.speed * self.patrol_speed * hunger_mod * hp_mod
                self.pos.x += (dx / dist) * patrol_speed
                self.pos.y += (dy / dist) * patrol_speed
            return None

    def find_mate(self, all_entities):
        """Найти партнёра для размножения среди других хищников.
        
        При низкой популяции радиус поиска увеличивается («брачный зов»):
        - 1-2 хищника → вся карта (2000px)
        - 3-4 → 1000px
        - 5-6 → 500px
        - 7+ → 300px (стандарт)
        
        Args:
            all_entities (list): список всех Entity
            
        Returns:
            Predator|None: ближайший подходящий партнёр
        """
        if self.hunger < self.breed_hunger:
            return None
        if self.age < self.breeding_age:
            return None
        if self.breed_cooldown > 0:
            return None
        
        population = len([e for e in all_entities if isinstance(e, Predator)])
        
        if population <= 2:
            search_radius = 2000 
        elif population <= 4:
            search_radius = 1000
        elif population <= 6:
            search_radius = 500
        else:
            search_radius = 300
        
        closest = None
        min_dist = search_radius
        
        for e in all_entities:
            if isinstance(e, Predator) and e != self:
                if e.dna.family_id == self.dna.family_id:
                    continue
                if e.hunger >= self.breed_hunger and e.age >= e.breeding_age and e.breed_cooldown <= 0:
                    dist = self.pos.distance_to(e.pos)
                    if dist < min_dist:
                        
                        min_dist = dist
                        closest = e
        return closest


class Peaceful(Entity):
    """Мирное травоядное. Пасётся, убегает от хищников, размножается.
    
    Имеет зрение для обнаружения хищников, многоуровневое бегство,
    поиск партнёра и логова для укрытия.
    
    Attributes:
        state (str): 'graze', 'flee', 'seek_mate', 'eat', 'wander'
        flee_vx, flee_vy (float): инерция бегства
        target_mate (Peaceful|None): партнёр для размножения
    """
    
    def __init__(self, x, y, color="#8FBC8F",
                 breed_chance=0.005, breeding_age=200, child_size_percent=0.4,
                 growth_divider=600, start_hunger_min=50, start_hunger_max=100,
                 flee_speed_close=0.9, flee_speed_mid=0.75, flee_speed_far=0.6,
                 graze_speed=0.3, mate_speed=0.7, wander_speed=0.5,
                 vision_base=150, vision_per_size=5,
                 base_metabolism=0.003, metabolism_per_size=0.004,
                 flee_cost_close=0.08, flee_cost_mid=0.05, flee_cost_far=0.03,
                 mate_cost=0.02, graze_cost=0.008, wander_cost=0.005,
                 breed_hunger=70, breed_hp_threshold=0.7, breed_cooldown_base=200, breed_cooldown_per_size=20,
                 hp_regen_rate=0.05, hp_regen_threshold=80, hp_damage_threshold=20, hp_damage_rate=0.01):
        """Создать мирное существо.
        
        Args:
            x, y (float): начальная позиция
            color (str): hex-цвет
            breed_chance (float): шанс размножения за кадр
            breeding_age (int): возраст зрелости в кадрах
            child_size_percent (float): начальный размер ребёнка
            growth_divider (float): делитель скорости роста
            start_hunger_min, start_hunger_max (float): диапазон стартового голода
            flee_speed_close, _mid, _far (float): множители скорости бегства
            graze_speed (float): множитель скорости при поиске еды
            mate_speed (float): множитель скорости при поиске партнёра
            wander_speed (float): множитель скорости блуждания
            vision_base (float): базовая дальность зрения
            vision_per_size (float): добавка к зрению за размер хищника
            base_metabolism (float): базовый расход голода
            metabolism_per_size (float): добавка к метаболизму за размер
            flee_cost_close, _mid, _far (float): расход голода при бегстве
            mate_cost (float): расход голода при поиске партнёра
            graze_cost (float): расход голода при поиске еды
            wander_cost (float): расход голода при блуждании
            breed_hunger (float): минимальный голод для спаривания
            breed_hp_threshold (float): минимальный % HP для спаривания
            breed_cooldown_base (int): базовый кулдаун после родов
            breed_cooldown_per_size (float): добавка к кулдауну за размер
            hp_regen_rate (float): регенерация HP за кадр
            hp_regen_threshold (float): порог голода для регенерации
            hp_damage_threshold (float): порог голода для урона
            hp_damage_rate (float): урон HP за кадр при голоде
        """
        dna = DNA()
        super().__init__(x, y, color=color, dna=dna)

        self.hunger = random.uniform(start_hunger_min, start_hunger_max)
        self.hp = self.dna.hp
        self.state = "graze"
        self.target_mate = None
        self.flee_target = None
        self.wander_target = None
        self.flee_vx = 0
        self.flee_vy = 0

        self.breed_chance = breed_chance
        self.breeding_age = breeding_age
        self.breed_cooldown = 0
        self.breed_hunger = breed_hunger
        self.breed_hp_threshold = breed_hp_threshold
        self.breed_cooldown_base = breed_cooldown_base
        self.breed_cooldown_per_size = breed_cooldown_per_size

        self.flee_speed_close = flee_speed_close
        self.flee_speed_mid = flee_speed_mid
        self.flee_speed_far = flee_speed_far
        self.graze_speed = graze_speed
        self.mate_speed = mate_speed
        self.wander_speed = wander_speed

        self.vision_base = vision_base
        self.vision_per_size = vision_per_size

        self.base_metabolism = base_metabolism
        self.metabolism_per_size = metabolism_per_size
        self.flee_cost_close = flee_cost_close
        self.flee_cost_mid = flee_cost_mid
        self.flee_cost_far = flee_cost_far
        self.mate_cost = mate_cost
        self.graze_cost = graze_cost
        self.wander_cost = wander_cost

        self.hp_regen_rate = hp_regen_rate
        self.hp_regen_threshold = hp_regen_threshold
        self.hp_damage_threshold = hp_damage_threshold
        self.hp_damage_rate = hp_damage_rate

        self.max_size = self.dna.size
        self.size = self.max_size * child_size_percent
        self.growth_rate = self.max_size / growth_divider

        self.age = 0
        
    def fight_back(self, predator, all_allies):
        """Мирные атакуют хищника группой если их больше 5 рядом.
        
        Args:
            predator: хищник которого атакуют
            all_allies: список всех мирных поблизости
        
        Returns:
            float: урон хищнику
        """
        nearby_allies = 0
        for ally in all_allies:
            if ally != self and self.pos.distance_to(ally.pos) < 80:
                nearby_allies += 1
        if nearby_allies >= 5:
            damage = nearby_allies * random.uniform(0.3, 0.8)
            return damage
        return 0

    def move_random(self, world_width, world_height):
        """Блуждание по территории.
        
        Args:
            world_width (int): ширина мира
            world_height (int): высота мира
        """
        self.hunger -= self.wander_cost

        if not self.wander_target or self.pos.distance_to(self.wander_target) < 30:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(50, 150)
            self.wander_target = Vector(
                self.pos.x + math.cos(angle) * distance,
                self.pos.y + math.sin(angle) * distance
            )

        if self.wander_target:
            dx = self.wander_target.x - self.pos.x
            dy = self.wander_target.y - self.pos.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                self.pos.x += (dx / dist) * self.dna.speed * self.wander_speed
                self.pos.y += (dy / dist) * self.dna.speed * self.wander_speed

    def see_predator(self, all_entities):
        """Обнаружить ближайшего хищника.
        
        Args:
            all_entities (list): список всех Entity
            
        Returns:
            tuple: (Predator|None, float|None) — хищник и расстояние до него
        """
        for e in all_entities:
            if isinstance(e, (Predator, Human)):
                dist = self.pos.distance_to(e.pos)
                detection_range = self.vision_base + e.size * self.vision_per_size
                if dist < detection_range:
                    return e, dist
        return None, None

    def find_mate(self, all_entities):
        if self.hunger < self.breed_hunger:
            return None
        if self.age < self.breeding_age:
            return None
        if self.breed_cooldown > 0:
            return None

        closest = None
        min_dist = self.vision_base
        for e in all_entities:
            if isinstance(e, Peaceful) and e != self:
                if e.dna.family_id == self.dna.family_id:
                    continue
                if e.dna.family_id in self.dna.parents:
                    continue
                if self.dna.family_id in e.dna.parents:
                    continue
                if (e.hunger >= self.breed_hunger and 
                    e.age >= e.breeding_age and 
                    e.breed_cooldown <= 0):
                    dist = self.pos.distance_to(e.pos)
                    if dist < min_dist:
                        min_dist = dist
                        closest = e
        return closest

    def want_to_go_home(self, dens):
        """Найти ближайшее логово (Den) для укрытия.
        
        Вызывается когда мирной голоден (<30) или в состоянии бегства.
        
        Args:
            dens (list): список всех объектов мира
            
        Returns:
            Den|None: ближайшее логово в радиусе 200 пикселей
        """
        from SandBox.objects import Den
        if self.hunger < 30 or self.state == "flee":
            closest = None
            min_dist = 200
            for den in dens:
                if not isinstance(den, Den):
                    continue
                dist = self.pos.distance_to(den.pos)
                if dist < min_dist:
                    min_dist = dist
                    closest = den
            return closest
        return None


class Human(Entity):
    """Человек с обучаемым мозгом, характером и отношениями."""
    def __init__(self, x, y, color="#460864"):
        from tests.brain import TestAgent as HumanBrain
        dna = DNA(size=7, speed=2.5, attack=3, hp=60, courage=0.6)
        super().__init__(x, y, color=color, dna=dna)
        self.brain_agent = HumanBrain(x, y)
        self.state = "learn"
        self.hunger = self.brain_agent.hunger
        self.hp = self.brain_agent.hp
        self.size = self.brain_agent.size
        self.last_state = None
        self.last_action = None
        self.inventory = self.brain_agent.inventory
        self.relationships = self.brain_agent.relationships
        self.personality = self.brain_agent.personality
    
    def update(self, world_objects, world_entities):
        if self.hp <= 0 or self.hunger <= 0:
            self.brain_agent.brain.save("brain_memory.json")
            return
        
        if self.hp < self.brain_agent.hp:
            self.brain_agent.hp = self.hp
        
        state = self.brain_agent.get_state(world_objects, world_entities)
        action = self.brain_agent.decide(world_objects, world_entities)
        reward = self.brain_agent.do_action(action, world_objects, world_entities)
        next_state = self.brain_agent.get_state(world_objects, world_entities)
        
        if self.last_state is not None:
            self.brain_agent.brain.learn(self.last_state, self.last_action, reward, state)
        
        self.last_state = state
        self.last_action = action
        
        self.pos.x = self.brain_agent.pos.x
        self.pos.y = self.brain_agent.pos.y
        self.hunger = self.brain_agent.hunger
        self.hp = self.brain_agent.hp
        self.size = self.brain_agent.size
        self.inventory = self.brain_agent.inventory
        self.relationships = self.brain_agent.relationships
    
    def draw(self, pil_draw, camera=None):
        """Отрисовка Human как фиолетового прямоугольника."""
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y
        pil_draw.rectangle(
            [x - self.size, y - self.size, x + self.size, y + self.size],
            fill="#460864"
        )


class DNA:
    """Генетический код существа.
    
    Определяет размер, скорость, атаку, здоровье, питательность и другие
    наследуемые характеристики. Поддерживает скрещивание с гауссовыми мутациями
    и запрет инцеста через family_id.
    
    Формулы основаны на аллометрии (Клайбер, степень 3/4) и популяционной генетике.
    
    Attributes:
        size (float): размер тела (4-12)
        speed (float): скорость (0.5-4.5)
        attack (float): сила атаки
        hp (int): здоровье
        nutrition_value (float): питательность при поедании
        starvation_threshold (float): порог голода для урона
        courage (float): смелость (0.1-0.9)
        family_id (int): идентификатор семьи (запрет инцеста)
    """
    
    _next_family_id = 0

    def __init__(self, speed=None, size=None, attack=None, hp=None, 
                 nutrition_value=None, starvation_threshold=None, family_id=None,
                 courage=None):
        self.size = size if size is not None else random.uniform(4, 10)

        if speed is not None:
            self.speed = speed 
        else:
            self.speed = 1.5 + 0.5 * (self.size ** 0.333)
            self.speed = max(0.5, min(4.5, self.speed))

        self.nutrition_value = nutrition_value if nutrition_value is not None else 3 * (self.size ** 0.75)
        self.starvation_threshold = starvation_threshold if starvation_threshold is not None else max(15, min(40, 10 + self.size * 2))
        self.courage = courage if courage is not None else min(0.9, 0.4 + self.size * 0.03)
        self.attack = attack if attack is not None else 1.5 + self.size * 0.4
        self.attack = max(0.5, self.attack)
        self.hp = hp if hp is not None else 15 + self.size * 3
        self.hp = max(5, int(self.hp))
        self.family_id = family_id if family_id is not None else DNA._next_family_id
        DNA._next_family_id += 1
        self.parents = [] 

    def breed(self, other):
        child = DNA()
        child.size = (self.size + other.size) / 2 + random.gauss(0, 0.8)
        child.size = max(3, min(12, child.size))
        child.speed = (self.speed + other.speed) / 2 + random.gauss(0, 0.3)
        child.speed = max(0.5, min(4.5, child.speed))
        child.courage = (self.courage + other.courage) / 2 + random.gauss(0, 0.08)
        child.courage = max(0.1, min(0.9, child.courage))
        child.attack = (self.attack + other.attack) / 2 + random.gauss(0, 0.3)
        child.attack = max(0.5, child.attack)
        child.hp = int((self.hp + other.hp) / 2 + random.randint(-3, 3))
        child.hp = max(5, child.hp)
        child.nutrition_value = 3 * (child.size ** 0.75)
        child.starvation_threshold = max(15, min(40, 10 + child.size * 2))
        child.family_id = self.family_id
        child.parents = [self.family_id, other.family_id]
        return child
    


def mix_colors(c1, c2):
    """Смешать два hex-цвета с небольшой случайной вариацией.
    
    Используется для определения цвета детёныша по цветам родителей.
    
    Args:
        c1 (str): hex-цвет первого родителя (#RRGGBB)
        c2 (str): hex-цвет второго родителя (#RRGGBB)
        
    Returns:
        str: hex-цвет ребёнка
    """
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = max(0, min(255, (r1 + r2) // 2 + random.randint(-20, 20)))
    g = max(0, min(255, (g1 + g2) // 2 + random.randint(-20, 20)))
    b = max(0, min(255, (b1 + b2) // 2 + random.randint(-20, 20)))
    return f"#{r:02x}{g:02x}{b:02x}"

import math
import random
from .core import Vector

class Entity:
    """Базовый класс для объектов в песочнице.
    
    Имеет позицию (Vector), цвет и умеет рисовать себя на Canvas.
    """
    def __init__(self, x, y, color="#00FF1E", static=False, form='oval', boundary_check=False, dna=None):
        self.dna = dna if dna is not None else DNA()
        
        self.pos = Vector(x, y)
        self.speed = (-self.dna.speed, self.dna.speed)  # из DNA!
        self.size = self.dna.size  # из DNA!
        self.nutrition_value = self.dna.nutrition_value  # из DNA!
        self.color = color
        self.static = static
        self.form = form
        self.boundary_check = boundary_check
        self.vx = 0
        self.vy = 0
        self.timer = random.randint(30, 60)
    
    def __str__(self):
        return f"Entity at {self.pos}"
    
    def __repr__(self):
        return f"Entity({self.pos.x}, {self.pos.y}, '{self.color}')"
    


    def draw(self, pil_draw, camera=None):
        """Нарисовать Entity на холсте в виде круга"""
            
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y
    
        if self.form == 'oval':
            pil_draw.ellipse([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)
        elif self.form == 'rectangle':
            pil_draw.rectangle([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)
            
    

    def move_to(self, x, y):
        """Переместить Entity в точку (x, y)"""
        self.pos.x = x
        self.pos.y = y
        
    def move_random(self, world_width, world_height):
        """Патрулирование с учётом состояния"""
        if hasattr(self, 'hunger'):
            self.hunger -= 0.005
        
        # Модификатор скорости от голода и здоровья
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
                speed = self.dna.speed * 0.5 * speed_mult
                self.pos.x += (dx / dist) * speed
                self.pos.y += (dy / dist) * speed
                
    def avoid_boundaries(self, world_offset_x, world_offset_y, world_width, world_height):
        """Отталкивание от границ мира"""
        margin = 50  # За сколько пикселей начинать уворачиваться
        
        left = world_offset_x + margin
        right = world_offset_x + world_width - margin
        top = world_offset_y + margin
        bottom = world_offset_y + world_height - margin
        
        force_x = 0
        force_y = 0
        
        if self.pos.x < left:
            force_x = (left - self.pos.x) * 0.1
        elif self.pos.x > right:
            force_x = (right - self.pos.x) * 0.1
        
        if self.pos.y < top:
            force_y = (top - self.pos.y) * 0.1
        elif self.pos.y > bottom:
            force_y = (bottom - self.pos.y) * 0.1
        
        self.pos.x += force_x
        self.pos.y += force_y
        
    def add_random_deviation(self, strength=0.3):
        """Случайное отклонение для реалистичного движения"""
        self.pos.x += random.uniform(-strength, strength)
        self.pos.y += random.uniform(-strength, strength)
            
                
    def is_colliding_with(self, other):
        '''Возвращает True если столкнулся с other'''
        return self.pos.distance_to(other.pos) < self.size + other.size
    
    def death(self):
        """Умереть и оставить след"""
        pass
    
    
class Predator(Entity):
    def __init__(self, x, y, color="#FF4500",
                 breed_chance=0.006, breeding_age=400, child_size_percent=0.4,
                 growth_divider=900, start_hunger_min=85, start_hunger_max=100,
                 child_hunger=70, hunt_threshold=85,
                 chase_speed=1.3, patrol_speed=0.6,
                 vision=200, vision_hungry=350,
                 base_cost=0.01, cost_per_size=0.01,
                 hunt_cost=0.02, hunt_cost_per_size=0.01,
                 patrol_cost=0.005, patrol_cost_per_size=0.005,
                 breed_hunger=75, breed_cooldown_base=400, breed_cooldown_per_size=30):
        
        dna = DNA()
        super().__init__(x, y, color=color, dna=dna)
        
        self.hunger = random.uniform(start_hunger_min, start_hunger_max)
        self.starvation_threshold = self.dna.starvation_threshold
        self.hp = self.dna.hp
        self.state = "wander"
        self.target = None
        self.patrol_target = None
        self.target_mate = None
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
        
        self.age = 0
        self.stuck_timer = 0
        self.last_pos = Vector(x, y)
        
    def new_patrol_target(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(100, 300)
        self.patrol_target = Vector(
            self.pos.x + math.cos(angle) * distance,
            self.pos.y + math.sin(angle) * distance
        )

    def find_target(self, all_entities):
        base_cost = 0.01 + (self.dna.size / 10) * 0.01
        self.hunger -= base_cost
        
        if self.hunger > 85:
            self.target = None
            self.state = "patrol"
            return
        
        closest_prey = None
        min_dist = float('inf')
        
        for e in all_entities:
            if isinstance(e, Peaceful):
                weakness_score = (e.dna.hp - e.hp) + (e.hunger < 30) * 50
                dist = self.pos.distance_to(e.pos)
                vision_range = 350 if self.hunger < 30 else 200
                
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

    def chase_target(self, world_width=1200, world_height=750):
        hunger_mod = 0.6 + (self.hunger / 100) * 0.4
        hp_mod = 0.5 + (self.hp / self.dna.hp) * 0.5
        
        # Детект застревания
        if not hasattr(self, 'stuck_timer'):
            self.stuck_timer = 0
            self.last_pos = Vector(self.pos.x, self.pos.y)
        
        if self.pos.distance_to(self.last_pos) < 2:
            self.stuck_timer += 1
        else:
            self.stuck_timer = 0
        self.last_pos = Vector(self.pos.x, self.pos.y)
        
        if self.state == "hunt" and self.target and isinstance(self.target, Peaceful):
            hunt_cost = 0.02 + (self.dna.size / 10) * 0.01
            self.hunger -= hunt_cost
            
            # Если застрял — уклоняйся
            if self.stuck_timer > 20:
                self.pos.x += random.uniform(-5, 5)
                self.pos.y += random.uniform(-5, 5)
                self.stuck_timer = 0
            
            victim = self.target
            dx = victim.pos.x - self.pos.x
            dy = victim.pos.y - self.pos.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < self.size + victim.size:
                damage_multiplier = 1.0 + (self.hunger < 20) * 0.5
                damage = self.dna.attack * damage_multiplier
                victim.hp -= damage
                
                if victim.hp <= 0:
                    self.hunger = min(100, self.hunger + victim.nutrition_value * 0.8)
                    self.target = None
                    self.state = "patrol"
                    return victim
            else:
                if dist > 0:
                    chase_speed = self.dna.speed * 1.3 * hunger_mod * hp_mod
                    self.pos.x += (dx / dist) * chase_speed
                    self.pos.y += (dy / dist) * chase_speed
            return None
        else:
            patrol_cost = 0.005 + (self.dna.size / 10) * 0.005
            self.hunger -= patrol_cost
            
            # Если застрял при патруле — новая цель
            if self.stuck_timer > 30:
                self.new_patrol_target()
                self.stuck_timer = 0
            
            if not self.patrol_target:
                self.new_patrol_target()
            else:
                dx = self.patrol_target.x - self.pos.x
                dy = self.patrol_target.y - self.pos.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 30:
                    self.new_patrol_target()
                elif dist > 0:
                    patrol_speed = self.dna.speed * 0.6 * hunger_mod * hp_mod
                    self.pos.x += (dx / dist) * patrol_speed
                    self.pos.y += (dy / dist) * patrol_speed
            return None
        
    def find_mate(self, all_entities):
        """Хищники ищут партнёра когда сыты"""
        if self.hunger < 80:
            return None
        
        if self.age < self.breeding_age:
            return None
        
        if self.breed_cooldown > 0:
            return None
        
        closest = None
        min_dist = 300  # Хищники видят партнёра дальше
        
        for e in all_entities:
            if isinstance(e, Predator) and e != self:
                if e.dna.family_id == self.dna.family_id:
                    continue
                
                if e.hunger > 80 and e.age >= e.breeding_age and e.breed_cooldown <= 0:
                    dist = self.pos.distance_to(e.pos)
                    if dist < min_dist:
                        min_dist = dist
                        closest = e
        return closest


class Peaceful(Entity):
    def __init__(self, x, y, color="#8FBC8F",
                 breed_chance=0.005, breeding_age=200, child_size_percent=0.4,
                 growth_divider=600, start_hunger_min=50, start_hunger_max=100,
                 flee_speed_close=1.2, flee_speed_mid=1.0, flee_speed_far=0.8,
                 graze_speed=0.3, mate_speed=0.7, wander_speed=0.5,
                 vision_base=150, vision_per_size=5,
                 base_metabolism=0.003, metabolism_per_size=0.004,
                 flee_cost_close=0.08, flee_cost_mid=0.05, flee_cost_far=0.03,
                 mate_cost=0.02, graze_cost=0.008, wander_cost=0.005,
                 breed_hunger=70, breed_hp_threshold=0.7, breed_cooldown_base=200, breed_cooldown_per_size=20,
                 hp_regen_rate=0.05, hp_regen_threshold=80, hp_damage_threshold=20, hp_damage_rate=0.01):
        
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
    
    def move_random(self, world_width, world_height):
        """Патрулирование территории"""
        self.hunger -= 0.005
        
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
                self.pos.x += (dx / dist) * self.dna.speed * 0.5
                self.pos.y += (dy / dist) * self.dna.speed * 0.5

    def see_predator(self, all_entities):
        """Обнаружение хищников поблизости"""
        for e in all_entities:
            if isinstance(e, (Predator, Human)):
                dist = self.pos.distance_to(e.pos)
                detection_range = 150 + e.size * 5
                if dist < detection_range:
                    return e, dist
        return None, None

    def find_mate(self, all_entities):
        if self.hunger < 60:
            return None
        
        if self.age < self.breeding_age:
            return None
        
        if self.breed_cooldown > 0:
            return None
        
        closest = None
        min_dist = 150
        for e in all_entities:
            if isinstance(e, Peaceful) and e != self:
                if e.dna.family_id == self.dna.family_id:
                    continue
                
                if e.hunger > 60 and e.age >= e.breeding_age and e.breed_cooldown <= 0:
                    dist = self.pos.distance_to(e.pos)
                    if dist < min_dist:
                        min_dist = dist
                        closest = e
        return closest
            
class Human(Entity):
    '''Будет добавлен позже'''
    pass

class DNA:
    _next_family_id = 0
    
    def __init__(self, speed=None, size=None, attack=None, hp=None, 
                 nutrition_value=None, starvation_threshold=None, family_id=None,
                 courage=None):
        
        # Размер — базовая характеристика
        self.size = size if size is not None else random.uniform(4, 10)
        
        if speed is not None:
            self.speed = speed 
        else:
            self.speed = 3.5 * (8 / self.size)
            self.speed = max(0.5, min(4.5, self.speed))
        
        # Питательность: если не указана, зависит от размера
        self.nutrition_value = nutrition_value if nutrition_value is not None else self.size * 3
        
        # Порог голода: если не указан, зависит от размера
        self.starvation_threshold = starvation_threshold if starvation_threshold is not None else max(20, 80 - self.size * 1.5)
        
        # Смелость: если не указана, зависит от размера
        self.courage = courage if courage is not None else min(0.9, 0.4 + self.size * 0.03)
        
        # Атака: если не указана, зависит от размера
        self.attack = attack if attack is not None else 1.5 + self.size * 0.4
        self.attack = max(0.5, self.attack)
        
        # Здоровье: если не указано, зависит от размера
        self.hp = hp if hp is not None else 15 + self.size * 3
        self.hp = max(5, int(self.hp))
        
        # Семейный ID
        self.family_id = family_id if family_id is not None else DNA._next_family_id
        DNA._next_family_id += 1
    
    def breed(self, other):
        """Смешать ДНК родителей с мутацией"""
        child = DNA()
        child.size = (self.size + other.size) / 2 + random.uniform(-1, 1)
        child.size = max(3, min(12, child.size))
        
        child.speed = (self.speed + other.speed) / 2 + random.uniform(-0.5, 0.5)
        child.speed = max(0.5, min(4.5, child.speed))
        
        child.courage = (self.courage + other.courage) / 2 + random.uniform(-0.1, 0.1)
        child.courage = min(0.9, max(0.1, child.courage))
        
        child.attack = (self.attack + other.attack) / 2 + random.uniform(-0.5, 0.5)
        child.attack = max(0.5, child.attack)
        
        child.hp = (self.hp + other.hp) / 2 + random.randint(-5, 5)
        child.hp = max(5, child.hp)
        
        child.nutrition_value = child.size * 3
        child.starvation_threshold = max(20, 80 - child.size * 1.5)
        
        child.family_id = DNA._next_family_id
        DNA._next_family_id += 1
        
        return child
    
def mix_colors(c1, c2):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = max(0, min(255, (r1 + r2) // 2 + random.randint(-20, 20)))
    g = max(0, min(255, (g1 + g2) // 2 + random.randint(-20, 20)))
    b = max(0, min(255, (b1 + b2) // 2 + random.randint(-20, 20)))
    return f"#{r:02x}{g:02x}{b:02x}"
    
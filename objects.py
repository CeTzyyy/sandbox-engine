import math
import random
from .core import Vector

class StaticObject:
    """Класс для всех статичных объектов в песочнице.
    
    Имеет позицию (Vector), цвет и умеет рисовать себя на Canvas.
    """
    def __init__(self, x, y, color="#AFAEAE", form='rectangle', size=8, collision=True, layer='lower'):
        self.pos = Vector(x, y)
        self.color = color
        self.form = form
        self.size = size
        self.collision = collision
        self.layer = layer
        
    
    def __str__(self):
        return f"Object at {self.pos}"
    
    def __repr__(self):
        return f"Object({self.pos.x}, {self.pos.y}, '{self.color}')"
    
    
    def draw(self, pil_draw, camera=None):
        """Нарисовать Object на холсте в виде указанной формы"""
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y
        
        if self.form == 'rectangle':
            pil_draw.rectangle([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)
        elif self.form == 'oval':
            pil_draw.ellipse([x - self.size, y - self.size, x + self.size, y + self.size], fill=self.color)

    def move_to(self, x, y):
        """Переместить Object в точку (x, y)"""
        self.pos.x = x
        self.pos.y = y
        
class Plant(StaticObject):
    def __init__(self, x, y,
                 food_min=2, food_max=5,
                 regrowth_min=0.003, regrowth_max=0.015,
                 bite_min=0.5, bite_max=1.5, bite_mult=1.5,
                 respawn_chance=0.0005, respawn_percent=0.3):
        
        self.food_value = random.uniform(food_min, food_max)
        super().__init__(x, y, color="#228B22", form='oval', size=3, layer="lower", collision=False)
        self.max_food = self.food_value
        self.regrowth_rate = random.uniform(regrowth_min, regrowth_max)
        self.max_size = 3
        self.bite_min = bite_min
        self.bite_max = bite_max
        self.bite_mult = bite_mult
        self.respawn_chance = respawn_chance
        self.respawn_percent = respawn_percent

    def eat(self):
        if self.food_value > 0:
            bite_size = max(0.5, min(1.5, self.food_value))
            self.food_value -= bite_size
            if self.food_value <= 0:
                self.size = 0
            else:
                self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))
            return bite_size * 1.5
        return 0

    def regrow(self):
        if self.food_value < self.max_food:
            self.food_value += self.regrowth_rate
            if self.food_value > 0:
                self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))
        elif self.size == 0 and random.random() < 0.0005:
            self.food_value = self.max_food * 0.3
            self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))
            
            
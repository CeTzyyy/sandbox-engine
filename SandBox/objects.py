import math
import random
from .core import Vector


class StaticObject:
    """Базовый класс для всех статичных объектов мира (камни, стены, декорации).
    
    Поддерживает две формы (oval/rectangle), слои (lower/lift) и коллизии.
    Объекты слоя 'lower' рисуются ПОД сущностями, слоя 'lift' — НАД.
    
    Attributes:
        pos (Vector): позиция в мировых координатах
        color (str): цвет в hex-формате (#RRGGBB)
        form (str): 'oval' или 'rectangle'
        size (float): радиус/половина стороны для отрисовки и коллизий
        collision (bool): участвует ли в коллизиях с Entity
        layer (str): 'lower' (под сущностями) или 'lift' (над сущностями)
    """
    
    def __init__(self, x, y, color="#AFAEAE", form='rectangle', size=8, collision=True, layer='lower'):
        """Создать статичный объект.
        
        Args:
            x, y: мировые координаты центра
            color: цвет в hex-формате
            form: 'oval' (круг/эллипс) или 'rectangle' (квадрат)
            size: размер (радиус для oval, половина стороны для rectangle)
            collision: если True — Entity не могут пройти сквозь
            layer: 'lower' — рисуется под Entity, 'lift' — над Entity
        """
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
        """Отрисовать объект на PIL-изображении с учётом камеры.
        
        Args:
            pil_draw: ImageDraw.Draw объект для рисования
            camera: объект Camera для преобразования мировых координат в экранные
        """
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y

        if self.form == 'rectangle':
            pil_draw.rectangle(
                [x - self.size, y - self.size, x + self.size, y + self.size],
                fill=self.color
            )
        elif self.form == 'oval':
            pil_draw.ellipse(
                [x - self.size, y - self.size, x + self.size, y + self.size],
                fill=self.color
            )

    def move_to(self, x, y):
        """Переместить объект в указанную мировую точку.
        
        Args:
            x, y: новые мировые координаты
        """
        self.pos.x = x
        self.pos.y = y


class Plant(StaticObject):
    """Съедобное растение. Растёт со временем, поедается мирными, удобряется трупами.
    
    Параметры роста и питательности настраиваются индивидуально при создании.
    Мёртвые растения (size=0) могут возродиться с шансом respawn_chance каждый кадр.
    
    Attributes:
        food_value (float): текущая питательность (0 = съедено под корень)
        max_food (float): максимальная питательность при полном росте
        regrowth_rate (float): скорость восстановления за кадр
        bite_min, bite_max (float): границы размера укуса
        bite_mult (float): множитель конверсии растение → голод (усвояемость)
        respawn_chance (float): шанс возрождения мёртвого растения за кадр
        respawn_percent (float): процент от max_food при возрождении
    """
    
    def __init__(self, x, y,
                 food_min=2, food_max=5,
                 regrowth_min=0.003, regrowth_max=0.015,
                 bite_min=0.5, bite_max=1.5, bite_mult=0.8,
                 respawn_chance=0.0005, respawn_percent=0.3):
        """Создать растение со случайными параметрами в заданных диапазонах.
        
        Args:
            x, y: мировые координаты
            food_min, food_max: диапазон начальной питательности (выбирается случайно)
            regrowth_min, regrowth_max: диапазон скорости восстановления
            bite_min, bite_max: мин/макс размер укуса (ограничивает eat())
            bite_mult: множитель питательности укуса (0.8 = 80% усвояемость)
            respawn_chance: вероятность возрождения за кадр (0.0005 ≈ раз в 33 сек при 60 FPS)
            respawn_percent: доля от max_food при возрождении (0.3 = 30%)
        """
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
        """Откусить от растения. Возвращает количество восстановленного голода.
        
        Размер укуса ограничен bite_min/bite_max и не может превысить оставшуюся еду.
        Возвращаемая ценность = bite_size * bite_mult (учёт усвояемости).
        При полном съедении size становится 0 (растение не отрисовывается).
        
        Returns:
            float: количество голода, которое восполнит этот укус
        """
        if self.food_value > 0:
            bite_size = max(self.bite_min, min(self.bite_max, self.food_value))
            self.food_value -= bite_size
            if self.food_value <= 0:
                self.size = 0
            else:
                self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))
            return bite_size * self.bite_mult
        return 0

    def regrow(self):
        """Восстановление растения за один кадр.
        
        Если растение не полностью выросло — добавляет regrowth_rate к food_value.
        Если растение мертво (size=0) — с шансом respawn_chance возрождается
        с food_value = max_food * respawn_percent.
        """
        if self.food_value < self.max_food:
            self.food_value += self.regrowth_rate
            if self.food_value > 0:
                self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))
        elif self.size == 0 and random.random() < self.respawn_chance:
            self.food_value = self.max_food * self.respawn_percent
            self.size = max(1, int(self.max_size * (self.food_value / self.max_food)))


class Den(StaticObject):
    """Логово/убежище для мирных существ.
    
    Мирные внутри safe_radius считаются в безопасности — хищники их не атакуют.
    Отрисовывается полупрозрачным, при наведении мыши становится ярче.
    
    Attributes:
        safe_radius (float): радиус безопасности (80px)
        alpha (int): прозрачность (0-255), 100 = полупрозрачное, 200 = при наведении
        hovered (bool): флаг наведения курсора
    """
    
    def __init__(self, x, y, size=40, color="#8B7355"):
        """Создать логово.
        
        Args:
            x, y: мировые координаты центра
            size: визуальный размер (радиус отрисовки)
            color: цвет логова (hex, используется как базовый)
        """
        super().__init__(x, y, color=color, form='oval', size=size, collision=False, layer='lift')
        self.safe_radius = 80
        self.base_color = color
        self.alpha = 100  # обычная полупрозрачность
        self.hovered = False

    def is_safe(self, entity):
        """Проверить, находится ли сущность внутри безопасной зоны логова.
        
        Returns:
            bool: True если в пределах safe_radius
        """
        return self.pos.distance_to(entity.pos) < self.safe_radius
    
    def update_hover(self, mouse_world_pos):
        """Обновить состояние наведения мыши.
        
        Args:
            mouse_world_pos: Vector или None — мировые координаты курсора
        """
        if mouse_world_pos:
            dist = self.pos.distance_to(mouse_world_pos)
            self.hovered = dist < self.size + 15
        else:
            self.hovered = False
    
    def draw(self, pil_draw, camera=None):
        """Отрисовать полупрозрачное логово. Ярче при наведении."""
        if camera:
            x, y = camera.world_to_screen(self.pos.x, self.pos.y)
        else:
            x, y = self.pos.x, self.pos.y
        
        alpha = 100 if self.hovered else 1020
        
        # Конвертируем hex в RGB
        r = int(self.base_color[1:3], 16)
        g = int(self.base_color[3:5], 16)
        b = int(self.base_color[5:7], 16)
        
        # Рисуем через overlay с альфа-каналом
        from PIL import Image as PILImage, ImageDraw as PILImageDraw
        
        size_px = int(self.size * 2)
        overlay = PILImage.new('RGBA', (size_px, size_px), (0, 0, 0, 0))
        overlay_draw = PILImageDraw.Draw(overlay)
        overlay_draw.ellipse([0, 0, size_px, size_px], fill=(r, g, b, alpha))
        
        # Вставляем на основной PIL-рисунок
        pil_draw._image.paste(overlay, (int(x - self.size), int(y - self.size)), overlay)
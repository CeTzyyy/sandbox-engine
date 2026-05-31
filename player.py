from .entities import Entity, DNA
from .core import Vector

class Player(Entity):
    def __init__(self, x, y, color="#2BFF00", speed=2):
        dna = DNA(speed=speed, size=10, nutrition_value=0, starvation_threshold=100)
        super().__init__(x, y, color=color, dna=dna)
        self.target = None
        self.speed_value = speed
        
    def set_target(self, x, y):
        '''Установить цель для передвижения'''
        self.target = Vector(x, y)
        
    def move_to_target(self, all_objects=None):
        '''Двигатся к цели'''
        if self.target:
            dx = self.target.x - self.pos.x
            dy = self.target.y - self.pos.y
            dist = Vector(dx, dy).length()
            
            if dist < 5:
                self.target = None
            else:
                self.pos.x += (dx / dist) * self.speed_value
                self.pos.y += (dy / dist) * self.speed_value
            
class Camera:
    def __init__(self, x: float = 0, y: float = 0, zoom: float = 1.0):
        self.x = x
        self.y = y
        self.zoom = zoom
        
    def world_to_screen(self, world_x, world_y):
        screen_x = (world_x - self.x) * self.zoom
        screen_y = (world_y - self.y) * self.zoom
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        world_x = screen_x / self.zoom + self.x
        world_y = screen_y / self.zoom + self.y
        return world_x, world_y
    
    
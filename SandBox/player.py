from .entities import Entity, DNA
from .core import Vector


class Player(Entity):
    """Управляемый игроком (или наблюдателем) персонаж.
    
    Не имеет голода, не умирает, не размножается. Используется для
    перемещения камеры и наблюдения за экосистемой.
    Передвигается по двойному клику в нужную точку мира.
    
    Attributes:
        target (Vector|None): точка назначения, к которой движется игрок
        speed_value (float): скорость перемещения в пикселях за кадр
    """
    
    def __init__(self, x, y, color="#2BFF00", speed=2):
        """Создать игрока-наблюдателя.
        
        Args:
            x, y: начальные мировые координаты
            color: цвет маркера игрока (hex)
            speed: скорость движения к цели (пикселей/кадр)
        """
        dna = DNA(speed=speed, size=10, nutrition_value=0, starvation_threshold=100)
        super().__init__(x, y, color=color, dna=dna)
        self.target = None
        self.speed_value = speed

    def set_target(self, x, y):
        """Установить точку назначения для движения.
        
        Вызывается по двойному клику — игрок начинает двигаться к указанным
        мировым координатам со скоростью speed_value.
        
        Args:
            x, y: мировые координаты цели
        """
        self.target = Vector(x, y)

    def move_to_target(self, all_objects=None):
        """Двигаться к установленной цели на один шаг.
        
        Вызывается каждый кадр из SandBox.update(). Если расстояние до цели
        меньше 5 пикселей — цель считается достигнутой и сбрасывается.
        
        Args:
            all_objects: не используется, оставлен для совместимости
        """
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
    """Камера для преобразования мировых координат в экранные и обратно.
    
    Поддерживает смещение (панорамирование) и зум (приближение/отдаление).
    Используется всеми объектами при отрисовке через world_to_screen().
    
    Attributes:
        x, y (float): смещение камеры (мировые координаты левого верхнего угла экрана)
        zoom (float): коэффициент приближения (1.0 = 100%, 2.0 = 200%)
    """
    
    def __init__(self, x: float = 0, y: float = 0, zoom: float = 1.0):
        """Создать камеру.
        
        Args:
            x, y: начальное смещение (0,0 = центр мира в левом верхнем углу экрана)
            zoom: коэффициент зума (>1 = приближение, <1 = отдаление)
        """
        self.x = x
        self.y = y
        self.zoom = zoom

    def world_to_screen(self, world_x, world_y):
        """Преобразовать мировые координаты в экранные.
        
        Формула: screen = (world - camera_offset) * zoom
        
        Args:
            world_x, world_y: координаты в мире
            
        Returns:
            tuple(float, float): экранные координаты для отрисовки
        """
        screen_x = (world_x - self.x) * self.zoom
        screen_y = (world_y - self.y) * self.zoom
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Преобразовать экранные координаты (клик мыши) в мировые.
        
        Формула: world = screen / zoom + camera_offset
        
        Args:
            screen_x, screen_y: координаты на экране (пиксели)
            
        Returns:
            tuple(float, float): мировые координаты
        """
        world_x = screen_x / self.zoom + self.x
        world_y = screen_y / self.zoom + self.y
        return world_x, world_y

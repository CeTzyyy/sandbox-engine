# main_simple.py — базовая симуляция
from SandBox import SandBox, Peaceful, Predator
import random

game = SandBox(world_height=2000, world_width=2000)

# Логова
game.spawn_den(-600, -600)
game.spawn_den(600, -600)
game.spawn_den(-600, 600)
game.spawn_den(600, 600)
game.spawn_den(0, 0, size=60)

# Трава
game.spawn_plants(clusters=12, min_plants=15, max_plants=30, spread=100)

# Мирные
game.spawn_random_entities(25, Peaceful)
game.spawn_random_entities(10, Peaceful,
    flee_speed_close=1.5, vision_base=180, breed_chance=0.008, breeding_age=180)

# Хищники — компактный спавн в центре
for _ in range(6):
    x = random.randint(-200, 200)
    y = random.randint(-200, 200)
    predator = Predator(x, y, chase_speed=2.0, breed_chance=0.015,
                        breeding_age=250, vision=300, hunt_threshold=80,
                        base_cost=0.005)
    game.add_entity(predator)

game.create_player(color="#00FF00", speed=3)
game(60)

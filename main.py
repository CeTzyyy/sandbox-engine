# main.py — полный тест всех возможностей
from SandBox import SandBox, Peaceful, Predator, Plant, Entity, DNA, mix_colors
import random

# Создаём мир с настройками
game = SandBox(
    world_height=2000,
    world_width=2000,
    show_borders=True
)

game.create_player(speed=1)

# Растения с кастомными настройками
game.spawn_plants(clusters=15, min_plants=25, max_plants=45, spread=120)

# Кастомное растение вручную
custom_plant = Plant(
    100, 100,
    food_min=5, food_max=10,
    regrowth_min=0.01, regrowth_max=0.03,
    bite_mult=2.0
)
game.add_object(custom_plant)

# Мирные с дефолтными настройками
game.spawn_random_entities(20, Peaceful)

# Мирные с кастомными настройками
game.spawn_random_entities(10, Peaceful,
    breed_chance=0.01,
    breeding_age=150,
    child_size_percent=0.5,
    growth_divider=500,
    start_hunger_min=60, start_hunger_max=100,
    flee_speed_close=1.5, flee_speed_mid=1.2, flee_speed_far=1.0,
    graze_speed=0.4, mate_speed=0.8, wander_speed=0.6,
    vision_base=200,
    base_metabolism=0.002,
    breed_hunger=65,
    hp_regen_threshold=75
)

# Мирные с другими настройками
game.spawn_random_entities(10, Peaceful,
    breed_chance=0.003,
    breeding_age=300,
    growth_divider=800,
    start_hunger_min=40, start_hunger_max=80,
    flee_speed_close=0.8, flee_speed_mid=0.6, flee_speed_far=0.4,
    graze_speed=0.2, mate_speed=0.5, wander_speed=0.3,
    vision_base=100,
    base_metabolism=0.005,
    breed_hunger=80
)

# Хищники с дефолтными настройками
game.spawn_random_entities(3, Predator)

# Хищники с кастомными настройками
game.spawn_random_entities(3, Predator,
    breed_chance=0.01,
    breeding_age=300,
    child_size_percent=0.5,
    growth_divider=800,
    start_hunger_min=90, start_hunger_max=100,
    child_hunger=80,
    hunt_threshold=80,
    chase_speed=1.5, patrol_speed=0.7,
    vision=250, vision_hungry=400,
    base_cost=0.008, cost_per_size=0.008,
    hunt_cost=0.015, hunt_cost_per_size=0.008,
    patrol_cost=0.003, patrol_cost_per_size=0.003,
    breed_hunger=70
)

# Хищники-слабаки
game.spawn_random_entities(2, Predator,
    breed_chance=0.002,
    breeding_age=500,
    growth_divider=1200,
    start_hunger_min=70, start_hunger_max=85,
    child_hunger=50,
    hunt_threshold=90,
    chase_speed=0.9, patrol_speed=0.4,
    vision=150, vision_hungry=250,
    hunt_cost=0.03,
    patrol_cost=0.008
)

# Создаём игрока
game.create_player(color="#00FF00", speed=3)

# Создаём существо вручную через DNA
custom_dna = DNA(size=7, speed=3, attack=4, hp=30)
custom_entity = Entity(500, 500, color="#FF00FF", dna=custom_dna)
game.add_entity(custom_entity)

# Тест mix_colors
color1 = "#FF0000"
color2 = "#0000FF"
mixed = mix_colors(color1, color2)
print(f"Смешанный цвет: {mixed}")

# Тест Vector
from SandBox.core import Vector
v1 = Vector(100, 200)
v2 = Vector(300, 400)
print(f"Расстояние между {v1} и {v2}: {v1.distance_to(v2):.1f}")
print(f"Длина {v1}: {v1.length():.1f}")

# Тест DNA
test_dna = DNA()
print(f"Случайная ДНК: size={test_dna.size:.1f}, speed={test_dna.speed:.1f}, attack={test_dna.attack:.1f}, hp={test_dna.hp}")

test_dna2 = DNA(size=8)
print(f"ДНК с размером 8: size={test_dna2.size}, speed={test_dna2.speed:.1f}, attack={test_dna2.attack:.1f}, hp={test_dna2.hp}")

child_dna = test_dna.breed(test_dna2)
print(f"Ребёнок: size={child_dna.size:.1f}, speed={child_dna.speed:.1f}, family={child_dna.family_id}")

# Тест камеры
print(f"Камера: zoom={game._camera.zoom}")
screen_x, screen_y = game._camera.world_to_screen(500, 500)
print(f"Мировые (500,500) -> экранные ({screen_x:.0f}, {screen_y:.0f})")
world_x, world_y = game._camera.screen_to_world(screen_x, screen_y)
print(f"Обратно: ({world_x:.0f}, {world_y:.0f})")

print("\n=== Запуск симуляции ===")
print(f"Всего растений: {len(game._objects)}")
print(f"Всего существ: {len(game._entities)}")
print(f"Мирных: {len([e for e in game._entities if isinstance(e, Peaceful)])}")
print(f"Хищников: {len([e for e in game._entities if isinstance(e, Predator)])}")

game()
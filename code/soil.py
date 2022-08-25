from random import choice
from typing import Callable
import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type: str, groups: list[pygame.sprite.Group] | pygame.sprite.Group, soil: pygame.sprite.Sprite, check_watered: Callable) -> None:
        super().__init__(groups)

        # setup
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}/')
        self.soil = soil
        self.check_watered = check_watered

        # plant growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvastable = False

        # sprite
        self.image = self.frames[self.age]
        self.y_offset = PLANT_Y_OFFSET[plant_type]
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']
    
    def grow(self) -> None:
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height*0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvastable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites: pygame.sprite.Group) -> None:
        self.FARMABLE = 'F'
        self.SOIL_PATCH = 'X'
        self.WATERED = 'W'
        self.PLANT = 'P'

        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfaces = import_folder_dict('../graphics/soil/')
        self.water_surfaces = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

        # sounds
        self.hoe_sound = pygame.mixer.Sound('../audio/hoe.wav')
        self.hoe_sound.set_volume(0.1)

        self.plant_sound = pygame.mixer.Sound('../audio/plant.wav')
        self.plant_sound.set_volume(0.2)

    def create_soil_grid(self) -> None:
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append(self.FARMABLE)
    
    def create_hit_rects(self):
        self.hit_rects: list[pygame.Rect] = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if self.FARMABLE in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point) -> None:
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()

                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if self.FARMABLE in self.grid[y][x]:
                    self.grid[y][x].append(self.SOIL_PATCH)
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()
    
    def water(self, point) -> None:
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(point):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append(self.WATERED)

                pos = soil_sprite.rect.topleft
                surf = choice(self.water_surfaces)
                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])
    
    def water_all(self) -> None:
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if self.SOIL_PATCH in cell and self.WATERED not in cell:
                    cell.append(self.WATERED)
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile((x, y), choice(self.water_surfaces), [self.all_sprites, self.water_sprites])

    def remove_water(self) -> None:
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()
        
        # clean up the grid
        for row in self.grid:
            for cell in row:
                if self.WATERED in cell:
                    cell.remove(self.WATERED)
    
    def check_watered(self, pos: tuple[int, int]) -> None:
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        return self.WATERED in cell

    def plant_seed(self, pos: tuple[int, int], seed: str) -> None:
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(pos):
                self.plant_sound.play()
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE

                if self.PLANT not in self.grid[y][x]:
                    self.grid[y][x].append(self.PLANT)
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)
    
    def update_plants(self) -> None:
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self) -> None:
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if self.SOIL_PATCH in cell:
                    # tile options
                    t = self.SOIL_PATCH in self.grid[index_row-1][index_col]
                    b = self.SOIL_PATCH in self.grid[index_row+1][index_col]
                    r = self.SOIL_PATCH in row[index_col+1]
                    l = self.SOIL_PATCH in row[index_col-1]

                    tile_type = 'o'

                    # all sides
                    if all((t, b, l, r)): tile_type = 'x'
                    
                    # horizontal tiles only
                    if l and not any((t, r, b)): tile_type = 'r'
                    if r and not any((t, l, b)): tile_type = 'l'
                    if r and l and not any((t, b)): tile_type = 'lr'

                    # vertical tiles only
                    if t and not any((r, l, b)): tile_type = 'b'
                    if b and not any((r, l, t)): tile_type = 't'
                    if b and t and not any((r, l)): tile_type = 'tb'

                    # corners
                    if l and b and not any((t, r)): tile_type = 'tr'
                    if r and b and not any((t, l)): tile_type = 'tl'
                    if l and t and not any((b, r)): tile_type = 'br'
                    if r and t and not any((b, l)): tile_type = 'bl'

                    # T shapes
                    if all((t, b, r)) and not l: tile_type = 'tbr'
                    if all((t, b, l)) and not r: tile_type = 'tbl'
                    if all((l, r, t)) and not b: tile_type = 'lrb'
                    if all((l, r, b)) and not t: tile_type = 'lrt'

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE), 
                        surf=self.soil_surfaces[tile_type], 
                        groups=[self.all_sprites, self.soil_sprites]
                    )

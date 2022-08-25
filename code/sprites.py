from random import randint, choice
from typing import Callable
import pygame
from settings import *
from timer_ import Timer

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group, z:int = LAYERS['main']) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width*0.2, -self.rect.height*0.75)

class Interaction(Generic):
    def __init__(self, pos: tuple[int, int], size: tuple[int, int], groups: list[pygame.sprite.Group] | pygame.sprite.Group, name: str) -> None:
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name

class Water(Generic):
    def __init__(self, pos: tuple[int, int], frames: list[pygame.Surface], groups: pygame.sprite.Group, z: int = LAYERS['main']) -> None:
        # animation setup
        self.frames = frames
        self.frame_index = 0

        # sprite setup
        super().__init__(
            pos=pos, 
            surf=self.frames[self.frame_index],
            groups=groups,
            z=LAYERS['water']
        )
    
    def animate(self, dt: float) -> None:
        self.frame_index += 5*dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
    
    def update(self, dt: float):
        self.animate(dt)

class WildFlower(Generic):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group) -> None:
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height*0.9)

class Particle(Generic):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group, z: int = LAYERS['main'], duration: int = 200) -> None:
        super().__init__(pos, surf, groups, z)

        self.start_time = pygame.time.get_ticks()
        self.duration = duration

        # white surface
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0, 0, 0))
        self.image = new_surf

    def update(self, dt: float) -> None:
        current_time = pygame.time.get_ticks()
        if (current_time - self.start_time) > self.duration:
            self.kill()

class Tree(Generic):
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface, groups: list[pygame.sprite.Group] | pygame.sprite.Group, name: str, player_add: Callable[[str, int], None]) -> None:
        super().__init__(pos, surf, groups)

        # tree attributes
        self.health = 5
        self.is_alive = True
        self.stump_surf = pygame.image.load(f'../graphics/stumps/{"small" if name == "Small" else "large"}.png')
        self.invul_timer = Timer(200)
        self.name = name

        # apples
        self.apple_surf = pygame.image.load('../graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

        self.player_add = player_add

        # sound
        self.axe_sound = pygame.mixer.Sound('../audio/axe.mp3')
        
    
    def damage(self):
        # damaging the tree
        self.health -= 1

        # play sound
        self.axe_sound.play()

        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            Particle(
                pos=random_apple.rect.topleft,
                surf=random_apple.image,
                groups=self.groups()[0],
                z=LAYERS['fruit']
            )
            self.player_add('apple')
            random_apple.kill()
        
    def check_death(self):
        if self.health <= 0:
            Particle(
                pos=self.rect.topleft,
                surf=self.image,
                groups=self.groups()[0],
                z=LAYERS['fruit'],
                duration=300
            )
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height*0.6)
            self.is_alive = False
            if self.name == 'Small':
                self.player_add('wood', 1)
            else:
                self.player_add('wood', 2)
    
    def create_fruit(self) -> None:
        for pos in self.apple_pos:
            if randint(0, 10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Generic((x, y), self.apple_surf, [self.apple_sprites, self.groups()[0]], LAYERS['fruit'])
    
    def update(self, dt: float) -> None:
        if self.is_alive:
            self.check_death()
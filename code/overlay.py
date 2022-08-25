import pygame
from settings import *
from player import Player

class Overlay:
    def __init__(self, player: Player) -> None:
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = player

        # imports
        overlay_path = '../graphics/overlay/'
        self.tools_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools}
        self.seeds_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in player.seeds}
    
    def display(self) -> None:
        # tool
        tool_surface = self.tools_surf[self.player.selected_tool]
        tool_rect = tool_surface.get_rect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surface, tool_rect)

        # seed
        seed_surface = self.seeds_surf[self.player.selected_seed]
        seed_rect = seed_surface.get_rect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surface, seed_rect)

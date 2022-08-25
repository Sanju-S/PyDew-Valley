from os import walk
import pygame

def import_folder(path: str) -> list[pygame.Surface]:
    surface_list = []

    for _, _, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surface = pygame.image.load(full_path).convert_alpha()
            surface_list.append(image_surface)

    return surface_list

def import_folder_dict(path: str) -> dict[str, pygame.Surface]:
    surface_dict = {}
    for _, _, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surface = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split('.')[0]] = image_surface
    return surface_dict
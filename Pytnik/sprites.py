import math
import random

import pygame
import os
import config

import itertools


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(
                config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(
            0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x,
                                            coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]


class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        unvisited = [i for i in range(1, len(coin_distance))]

        path = list()

        current = 0
        while unvisited:
            minimal = math.inf
            index = -1

            for node in unvisited:
                value = coin_distance[current][node]

                if value < minimal:
                    minimal = value
                    index = node

            current = index
            unvisited.remove(index)
            path.append(index)

        return [0] + path + [0]


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        minimal = math.inf

        for perm in itertools.permutations([i for i in range(1, len(coin_distance))]):
            perm = list(perm) + [0]

            current = 0
            cost = 0

            for node in perm:
                cost += coin_distance[current][node]
                current = node

            if cost < minimal:
                path = perm
                minimal = cost

        return [0] + path


class Node:
    def __init__(self, id, val, unvisited, parent=None, h=0):
        self.id = id

        self.val = val
        self.h = h

        self.unvisited = unvisited
        self.parent = parent


class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        next = [current := Node(0, 0, [i for i in range(1, len(coin_distance))])]

        while current.id != 0 or current.unvisited:
            next.remove(current)

            if not current.unvisited:
                current.unvisited = [0]

            for i in current.unvisited:
                next.append(Node(i, current.val + coin_distance[current.id][i], current.unvisited, current))

            current = min(next, key=lambda d: (d.val, len(d.unvisited), d.id))
            current.unvisited = [x for x in current.unvisited if x != current.id]

        path = list()
        while current:
            path.append(current.id)
            current = current.parent

        return path


class Micko(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def mst(self, coin_distance, unvisited):
        unvisited = unvisited.copy()

        cost = 0
        visited = [0]

        while unvisited:
            minimum = math.inf

            for i in visited:
                for j in unvisited:
                    if minimum > coin_distance[i][j]:
                        minimum = coin_distance[i][j]
                        removal = j

            cost += minimum
            unvisited.remove(removal)
            visited.append(removal)

        return cost

    def get_agent_path(self, coin_distance):
        next = [current := Node(0, 0, [i for i in range(1, len(coin_distance))])]

        while current.id != 0 or current.unvisited:
            next.remove(current)

            h = self.mst(coin_distance, current.unvisited)

            if not current.unvisited:
                current.unvisited = [0]

            for i in current.unvisited:
                next.append(Node(i, current.val + coin_distance[current.id][i], current.unvisited, current, h))

            current = min(next, key=lambda d: (d.val + d.h, len(d.unvisited), d.id))
            current.unvisited = [x for x in current.unvisited if x != current.id]

        path = list()
        while current:
            path.append(current.id)
            current = current.parent

        return path

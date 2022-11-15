import pygame
import socket
import sys
import time
import threading
import random
import math
import os
import logging
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, FadeTransition

Window.clearcolor = (100, 100, 255, 1)

from pygame.locals import *

'''
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Battleships")
pygame.mouse.set_visible(1)
clock = pygame.time.Clock()
'''
logger = logging.getLogger('battleships')


class tile():
    def __init__(self, x, y, type_):
        self.x = x
        self.y = y
        self.type = type_

    def draw(self, screen):
        assert isinstance(screen, pygame.Surface)
        if self.type == "shipPart":
            pygame.draw.rect(screen, (0, 0, 0), (self.x, self.y, 20, 20))
        elif self.type == "shipPartHit":
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, 20, 20))
        elif self.type == "Water":
            pygame.draw.rect(screen, (0, 0, 255), (self.x, self.y, 20, 20))
        elif self.type == "WaterHit":
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, 20, 20))
        elif self.type == "Land":
            pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, 20, 20))
        elif self.type == "LandHit":
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, 20, 20))
        else:
            logger.error("Unknown tile type: %s" % self.type)
            sys.exit()
            return
        logger.info("Drawing tile at %s,%s" % (self.x, self.y))

    def __str__(self):
        return "Tile at %s,%s" % (self.x, self.y)


class tileGroup():
    def __init__(self, tiles=None):
        if tiles == None:
            self.tiles = []
        else:
            self.tiles = tiles

    def addTile(self, tile):
        self.tiles.append(tile)

    def draw(self, screen):
        for tile in self.tiles:
            tile.draw(screen)

    def getTile(self, x, y):
        for tile in self.tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def getTileByType(self, type_):
        temp = []
        for tile in self.tiles:
            if tile.type == type_:
                temp.append(tile)
        if len(temp) > 0:
            return temp
        return None

    def __str__(self):
        temp = ''
        for t in self.tiles:
            temp = temp + " | " + str(t)
        return temp


class player():
    def __init__(self, name, isHost=False):
        self.name = name
        self.ships = []
        self.shipsHit = []
        self.shots = []
        self.shotsHit = []
        self.shotsMissed = []
        self.shipsLeft = 0
        self.shipsHitLeft = 0
        self.shotsLeft = 0
        self.shotsHitLeft = 0
        self.shotsMissedLeft = 0
        self.ships = tileGroup()
        self.shipsHit = tileGroup()
        self.shots = tileGroup()
        self.shotsHit = tileGroup()
        self.shotsMissed = tileGroup()

        self.s = socket.socket()
        self.host = socket.gethostname()

        self.port = 65053
        self.isHost = isHost
        if isHost:
            self.s.bind((self.host, self.port))


    def connect(self):
        self.s.connect((self.host, self.port))
        print(f"Connected to host: {self.host}, {self.port}")
        logger.info("Connected to server")

    def hostGame(self):
        self.getConnection()

    def getConnection(self, timeout=5):
        print("Waiting for connection...")
        try:
            self.s.listen(timeout)
            self.c, self.addr = self.s.accept()
        except Exception as e:
            print(f"Connection timed out: {e}")
            return
        print("Got connection from", str(self.addr))
        logger.info("Got connection from %s" % str(self.addr))

    def addShip(self, x, y):
        self.ships.addTile(tile(x, y, "shipPart"))
        self.shipsLeft += 1

    def addShipHit(self, x, y):
        self.shipsHit.addTile(tile(x, y, "shipPartHit"))
        self.shipsHitLeft += 1
        self.shipsLeft -= 1

    def addShot(self, x, y):
        self.shots.addTile(tile(x, y, "Water"))
        self.shotsLeft += 1

    def addShotHit(self, x, y):
        self.shotsHit.addTile(tile(x, y, "WaterHit"))

    def sendData(self, data):
        print(f"Sending data: {data} as {data.encode()}")
        if not self.isHost:
            self.s.send(data.encode())
        else:
            self.c.send(data.encode())


    def sendMove(self, x, y):
        self.s.send((str(x) + " " + str(y)).encode())
        logger.info("Sent move: %s %s" % (x, y))

    def getMove(self):
        logger.info("Waiting for move...")
        return self.s.recv(1024).decode()

    def checkHit(self):
        for ship in self.ships.tiles:
            for shot in self.shots.tiles:
                if ship.x == shot.x and ship.y == shot.y:
                    self.addShipHit(ship.x, ship.y)
                    self.addShotHit(shot.x, shot.y)
                    return True
        return False

    def draw(self, screen):
        self.ships.draw(screen)
        self.shipsHit.draw(screen)
        self.shots.draw(screen)
        self.shotsHit.draw(screen)
        self.shotsMissed.draw(screen)
        pygame.display.flip()

    def renderLobby(self, screen, host=False):

        assert isinstance(screen, pygame.Surface)
        if host:
            screen.fill((255, 255, 255))
            font = pygame.font.SysFont("monospace", 15)
            label = font.render("Waiting for opponent...", 1, (0, 0, 0))
            screen.blit(label, (10, 10))
            pygame.display.flip()
        else:
            screen.fill((255, 255, 255))
            font = pygame.font.SysFont("monospace", 15)
            label = font.render("Connecting...", 1, (0, 0, 0))
            screen.blit(label, (10, 10))
            pygame.display.flip()

    def receiveData(self):
        if not self.isHost:
            return self.s.recv(1024).decode()
        else:
            return self.c.recv(1024).decode()

    def renderSelection(self, screen):
        assert isinstance(screen, pygame.Surface)
        screen.fill((255, 255, 255))
        while True:
            self.drawGrid(640, 480, screen)

            font = pygame.font.SysFont("monospace", 30)
            label = font.render("Select your ships", 15, (255, 0, 0))
            screen.blit(label, (10, 10))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and len(self.ships.tiles) < 5:
                    isThere = False
                    x, y = pygame.mouse.get_pos()
                    x = int(x / 20) * 20
                    y = int(y / 20) * 20
                    for i in range(0, 20):
                        if self.ships.getTile(x + i, y + i) != None:
                            isThere = True
                    if not isThere:
                        self.addShip(x, y)
                        self.draw(screen)
                        print("there is no ship at %s,%s" % (x, y))
                    else:
                        print("there is a ship at %s,%s" % (x, y))
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(self.ships.tiles) == 5:
                        self.sendData("ready")
                        while self.receiveData() != "ready":
                            label = font.render("""Select your ships | Waiting for other player""", 1, (0, 0, 0))
                            screen.blit(label, (10, 10))
                            pygame.display.flip()
                            time.sleep(0.5)

                        return

                    else:
                        label = font.render("""Select your ships | You need 5 ships""", 1, (255, 0, 0))
                        screen.blit(label, (10, 10))
                        pygame.display.flip()


    def drawGrid(self, WINDOW_WIDTH, WINDOW_HEIGHT, SCREEN):
        blockSize = 20 #Set the size of the grid block
        for x in range(0, WINDOW_WIDTH, blockSize):
            for y in range(0, WINDOW_HEIGHT, blockSize):
                rect = pygame.Rect(x, y, blockSize, blockSize)
                pygame.draw.rect(SCREEN, (0, 0, 0), rect, 1)
        pygame.display.flip()
def host():
    try:
        global screen
        global clock
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Battleships")
        pygame.mouse.set_visible(1)
        clock = pygame.time.Clock()
    except Exception as e:
        logger.error("Failed to init pygame: %s" % e)
        sys.exit()

    global p
    p = player(str(random.randint(0, 1000)), True)
    p.renderLobby(screen, host=True)

    try:
        p.hostGame()

    except Exception as e:
        logger.error("Failed to host: %s. Are you connected to the internet?" % e)
        sys.exit()

    print(f'Hosted game as "{p.name}" on {p.host}')

    p.renderSelection(screen)

    mainLoop()


def connect():
    try:
        global clock
        global screen
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Battleships")
        pygame.mouse.set_visible(1)
        clock = pygame.time.Clock()
    except Exception as e:
        logger.error("Failed to init pygame: %s" % e)
        sys.exit()

    global p
    p = player(str(random.randint(0, 1000)))
    p.connect()

    try:
        p.renderLobby(screen, host=False)
    except Exception as e:
        logger.error("Failed to connect to server: %s. Are there any servers hosting?" % e)
        sys.exit()
    print("Connected to server as %s" % p.name)

    p.renderSelection(screen)

    mainLoop()

def mainLoop():
    while True:
        p.drawGrid(640, 480, screen)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((255, 255, 255))

        clock.tick(60)


class mainMenu(Screen):
    def __init__(self, **kwargs):
        super(mainMenu, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.layout.add_widget(Label(text="Battleships"))
        self.layout.add_widget(Button(text="Host Game", on_press=self.hostGame))
        self.layout.add_widget(Button(text="Join Game", on_press=self.joinGame))
        self.layout.add_widget(Button(text="Quit", on_press=self.quitGame))

        self.add_widget(self.layout)

    def hostGame(self, *args):
        logger.info("Hosting game")
        host()

    def joinGame(self, *args):
        logger.info("Joining game")
        connect()

    def quitGame(self, *args):
        logger.info("Quitting game")
        sys.exit()


class app(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())

        self.sm.add_widget(mainMenu(name="mainMenu"))
        return self.sm


if __name__ == "__main__":
    app().run()
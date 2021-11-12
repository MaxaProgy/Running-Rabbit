import sys
import os
import sqlite3
from random import choice, randrange

from PyQt5.Qt import QWidget, QApplication, QIcon, QDesktopWidget, QPushButton, QTimer, QFileDialog, QTableWidget
from PyQt5.Qt import Qt, QLabel, QFont, QLineEdit, QPixmap, QMessageBox, QColor, QPainter
from PyQt5.Qt import QTableWidgetItem
from PyQt5 import QtCore, QtMultimedia
from math import fabs

PIC = 7


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class Map:
    def __init__(self, file):
        f = open(file, encoding="utf8")
        with f:
            old_map = f.readlines()
        f.close()
        self._row = len(old_map)
        self._col = len(old_map[0]) - 1
        self._sp_elem_map = []
        self._stairs_game_end = []
        game.enemies = []
        for j in range(self._row):
            self._sp_elem_map.append([])
            for i in range(self._col):
                elem = None
                if int(old_map[j][i]) == 0:
                    elem = Empty()
                elif int(old_map[j][i]) == 1:
                    elem = Brick()
                elif int(old_map[j][i]) == 2:
                    if j != 0:
                        elem = Stairs()
                    else:
                        elem = Empty()
                        self._stairs_game_end.append([i, j])
                elif int(old_map[j][i]) == 3:
                    elem = Bush()
                elif int(old_map[j][i]) == 4:
                    elem = Portal(i, j)
                elif int(old_map[j][i]) == 5:
                    elem = Empty()
                    game.hero = Hero()
                    game.hero.set_xy(i, j)
                elif int(old_map[j][i]) == 6:
                    elem = Empty()
                    game.enemies.append(Enemy())
                    game.enemies[-1].set_xy(i, j)
                    game.enemies[-1].set_start_xy(i, j)
                self._sp_elem_map[j].append(elem)

    def get_col(self):
        return self._col

    def get_row(self):
        return self._row

    def get_elem_xy(self, x, y):
        return self._sp_elem_map[y][x]

    def set_elem_xy(self, x, y, elem):
        self._sp_elem_map[y][x] = elem


class ElemMap:
    def __init__(self):
        self._transparency = False
        self._pic = None

    def get_transparency(self):
        return self._transparency

    def get_pic(self):
        return self._pic


class Empty(ElemMap):
    def __init__(self):
        super().__init__()
        self._transparency = True
        self._pic = QPixmap(resource_path("PIC/0_0.png"))


class Brick(ElemMap):
    def __init__(self):
        super().__init__()
        self._live_brick = 0
        self._transparency = False
        self._pic = []
        self._pos_show_pic = 0
        for i in range(6):
            self._pic.append(QPixmap(resource_path("PIC/1_" + str(i) + ".png")))

        self.timer_brick = QTimer()
        self.timer_brick.timeout.connect(self.updateValues)

    def dig(self):
        self._live_brick = 6
        self._transparency = True
        self.timer_brick.start(1500)
        self.updateValues()

    def updateValues(self):
        self._live_brick -= 1
        self._pos_show_pic = self._live_brick
        if self._live_brick == 0:
            self._transparency = False
            self.timer_brick.stop()
            if type(game.map.get_elem_xy(int(game.hero.get_x()), int(round(game.hero.get_y())))) == Brick:
                game.you_lose()
            for enemy in game.enemies:
                if type(game.map.get_elem_xy(int(enemy.get_x()), int(round(enemy.get_y())))) == Brick:
                    enemy.set_xy(enemy.get_start_x(), enemy.get_start_y())

    def get_pic(self):
        return self._pic[self._pos_show_pic]


class Stairs(ElemMap):
    def __init__(self):
        super().__init__()
        self._transparency = True
        self._pic = QPixmap(resource_path("PIC/2_0.png"))


class Bush(ElemMap):
    def __init__(self):
        super().__init__()
        self._transparency = True
        self._pic = []
        for i in range(2):
            self._pic.append(QPixmap(resource_path("PIC/3_" + str(i) + ".png")))
        self._pos_show_pic = randrange(0, 1)
        self.timer_bush = QTimer()
        self.timer_bush.timeout.connect(self.updateValues)
        self.timer_bush.start(500)

    def get_pic(self):
        return self._pic[self._pos_show_pic]

    def updateValues(self):
        self._pos_show_pic += 1
        if self._pos_show_pic == 2:
            self._pos_show_pic = 0


class Portal(ElemMap):
    def __init__(self, x, y):
        super().__init__()
        self._transparency = True
        self._pic = QPixmap(resource_path("PIC/4_0.png"))
        self._x = x
        self._y = y

    def get_xy(self):
        return self._x, self._y


class People:
    def __init__(self):
        self._x = 0
        self._y = 0
        self._pic = None
        self._step = 0.2
        self._flag_freeze_kb = False
        self._flag_portal = True
        self._STOP = ""
        self._LEFT = "l"
        self._RIGHT = "r"
        self._UP = "u"
        self._DOWN = "d"
        self._transparency = False
        self._pic = dict()

        for do in (self._STOP, self._LEFT, self._RIGHT, self._UP, self._DOWN):
            self._pic[do] = [QPixmap(resource_path("PIC/" + self._number_pic + do + '_' + str(i) + ".png"))
                             for i in range(5)]

        self._pos_show_pic = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateValues)

        self._what_doing_now = self._STOP

    def get_x(self):
        return self._x

    def set_x(self, x):
        self._x = x

    def get_y(self):
        return self._y

    def set_y(self, y):
        self._y = y

    def get_xy(self):
        return self._x, self._y

    def set_xy(self, x, y):
        self._x = x
        self._y = y

    def get_pic(self):
        return self._pic[self._what_doing_now][self._pos_show_pic]

    def updateValues(self):
        self._x = round(self._x, 1)
        self._y = round(self._y, 1)

        if self._y != game.map.get_row() - 1 and \
                type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y - 2 * self._step)) + 1)) \
                in [Zerro, One, Empty, Bush, Brick, Portal] \
                and type(game.map.get_elem_xy(int(round(self._x)),
                                              int(round(self._y)))) != Stairs and \
                game.map.get_elem_xy(int(round(self._x)),
                                     int(round(self._y - 2 * self._step)) + 1)._transparency:
            self._flag_freeze_kb = True
            self._y += self._step

            if int(self._x) == 0:
                if round(self._x, 1) == 2 * self._step:
                    self._x -= self._step
            elif round(self._x % int(self._x), 1) == 2 * self._step:
                self._x -= self._step

            if int(self._x) == 0:
                if round(self._x, 1) == round(3 * self._step, 1):
                    self._x += self._step
            elif round(self._x % int(self._x), 1) == round(3 * self._step, 1):
                self._x += self._step

            self._what_doing_now = self._STOP
            self._pos_show_pic += 1
            if self._pos_show_pic == 5:
                self._pos_show_pic = 0
        else:
            self._flag_freeze_kb = False
            self._pos_show_pic += 1
            if self._pos_show_pic == 5:
                self._pos_show_pic = 0

            self.auto_go()
            if self._what_doing_now == self._RIGHT:
                self._previous_action = self._what_doing_now
                if self._x != game.map.get_col() - 4 * self._step and (
                        (game.map.get_elem_xy(int(round(self._x + 2 * self._step)),
                                              int(round(self._y))).get_transparency() and
                         (round(int(self._y), 1) == round(self._y, 1))) or
                        (self._y == game.map.get_row() - 1 or game.map.get_elem_xy(int(self._x - self._step) + 1,
                                                                                   int(
                                                                                       self._y) + 1).get_transparency()) and
                        game.map.get_elem_xy(int(round(self._x - 3 * self._step)) + 1,
                                             int(self._y)).get_transparency()):
                    self._x += self._step

            elif self._what_doing_now == self._LEFT:
                self._previous_action = self._what_doing_now

                if self._x != -self._step and ((round(int(self._y), 1) == round(self._y, 1) and
                                                game.map.get_elem_xy(int(round(self._x - 2 * self._step)),
                                                                     int(round(self._y))).get_transparency()) or
                                               (round(int(self._y), 1) != round(self._y, 1) and
                                                game.map.get_elem_xy(int(round(self._x + 3 * self._step)) - 1,
                                                                     int(self._y) + 1).get_transparency() and
                                                game.map.get_elem_xy(int(round(self._x + 3 * self._step)) - 1,
                                                                     int(self._y)).get_transparency())):
                    self._x -= self._step

            elif self._what_doing_now == self._DOWN:
                if self._y != game.map.get_row() - 1 and (
                        (game.map.get_elem_xy(int(round(self._x)), int(self._y) + 1).get_transparency() and
                         (type(game.map.get_elem_xy(int(round(self._x, )), int(round(self._y)))) == Stairs or
                          type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y + self._step))))
                          in [Bush, Empty])) or
                        (type(game.map.get_elem_xy(int(round(self._x)), int(self._y) + 1)) == Stairs and
                         type(game.map.get_elem_xy(int(round(self._x)), int(self._y + self._step)))
                         in [Zerro, One, Empty, Bush])):
                    self._x = round(self._x)
                    self._y += self._step

            elif self._what_doing_now == self._UP:
                if self._y != 0 and (
                        (game.map.get_elem_xy(int(round(self._x)), int(self._y - self._step)).get_transparency() and
                         type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y)))) == Stairs) or
                        type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y - self._step, 1))))
                        in [Zerro, One, Empty, Bush]):
                    self._x = round(self._x)
                    self._y -= self._step

            if type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y)))) == Portal:
                if self._flag_portal:
                    sp_portal = []
                    for i in range(game.map.get_col()):
                        for j in range(game.map.get_row()):
                            if game.map.get_elem_xy(i, j) != \
                                    game.map.get_elem_xy(int(round(self._x)), int(round(self._y))) \
                                    and type(game.map.get_elem_xy(i, j)) == Portal:
                                sp_portal.append(game.map.get_elem_xy(i, j))
                    x, y = choice(sp_portal).get_xy()
                    self.set_xy(x, y)
                    self._flag_portal = False
            else:
                self._flag_portal = True

            self.get_zerro_and_one()

    def get_zerro_and_one(self):
        pass

    def auto_go(self):
        pass

    def go_left(self):
        if not self._flag_freeze_kb:
            if self._what_doing_now != self._LEFT:
                self._pos_show_pic = 0
            self._what_doing_now = self._LEFT

    def go_right(self):
        if not self._flag_freeze_kb:
            if self._what_doing_now != self._RIGHT:
                self._pos_show_pic = 0
            self._what_doing_now = self._RIGHT

    def go_up(self):
        if not self._flag_freeze_kb:
            if self._what_doing_now != self._UP:
                self._pos_show_pic = 0
            self._what_doing_now = self._UP

    def go_down(self):
        if not self._flag_freeze_kb:
            if self._what_doing_now != self._DOWN:
                self._pos_show_pic = 0
            self._what_doing_now = self._DOWN

    def stop(self):
        self._what_doing_now = self._STOP


class Hero(People):
    def __init__(self):
        self._number_pic = "5"
        super().__init__()
        self._previous_action = self._STOP
        self._lifes = 3

    def get_lifes(self):
        return self._lifes

    def set_lifes(self, life):
        self._lifes = life

    def get_zerro_and_one(self):
        if type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y)))) in [Zerro, One]:
            game.map.set_elem_xy(int(round(self._x)), int(round(self._y)), Empty())
            game.set_score(game.get_score() + 5)
            flag = False
            for i in range(game.map.get_col()):
                for j in range(game.map.get_row()):
                    if type(game.map.get_elem_xy(i, j)) in [Zerro, One]:
                        flag = True
            if not flag:
                for elem in game.map._stairs_game_end:
                    game.map.set_elem_xy(elem[0], elem[1], Stairs())
        if type(game.map.get_elem_xy(int(round(self._x)), int(round(self._y)))) == Stairs and round(self._y) == 0:
            game.player.pause()
            game.hero.timer.stop()
            for enemy in game.enemies:
                enemy.timer.stop()
            game.timer_game.stop()
            buttonReply = QMessageBox.question(game, 'ВЫ ВЫИГРАЛИ', "Перейти на следующий уровень?",
                                               QMessageBox.Yes | QMessageBox.Close, QMessageBox.Yes)
            if buttonReply == QMessageBox.Yes:
                game.set_score(game.get_score())
                game.file_number += 1
                game.reload_game()
                game.timer_game.start(200)
            else:
                game.show_menu()

    def go_dig(self):
        if self._previous_action == self._LEFT:
            if type(game.map.get_elem_xy(int(round(self._x)) - 1, int(round(self._y)))) == Empty and \
                    type(game.map.get_elem_xy(int(round(self._x)) - 1, int(round(self._y)) + 1)) == Brick:
                game.map.get_elem_xy(int(round(self._x)) - 1, int(round(self._y)) + 1).dig()
        elif self._previous_action == self._RIGHT:
            if type(game.map.get_elem_xy(int(round(self._x)) + 1, int(round(self._y)))) == Empty and \
                    type(game.map.get_elem_xy(int(round(self._x)) + 1, int(round(self._y)) + 1)) == Brick:
                game.map.get_elem_xy(int(round(self._x)) + 1, int(round(self._y)) + 1).dig()


class Enemy(People):
    def __init__(self):
        self._number_pic = "6"
        super().__init__()
        self._start_x = 0
        self._start_y = 0

    def set_start_xy(self, x, y):
        self._start_x = x
        self._start_y = y

    def get_start_x(self):
        return self._start_x

    def get_start_y(self):
        return self._start_y

    def create_labirint(self):
        self._labirint = [[1 for i in range(game.map.get_col())] for j in range(game.map.get_row())]
        for i in range(game.map.get_row()):
            for j in range(game.map.get_col()):
                if type(game.map.get_elem_xy(j, i)) in [Empty, Bush, Stairs, Portal]:
                    if i == game.map.get_row() - 1:
                        self._labirint[i][j] = 0
                        continue
                    if type(game.map.get_elem_xy(j, i + 1)) in [Brick, Stairs] or \
                            (type(game.map.get_elem_xy(j, i)) == Stairs \
                             and type(game.map.get_elem_xy(j, i + 1)) in [Empty, Bush, Portal]):
                        self._labirint[i][j] = 0
                    if type(game.map.get_elem_xy(j, i + 1)) in [Stairs, Brick]:
                        if j != game.map.get_col() - 1:
                            if type(game.map.get_elem_xy(j, i)) in [Stairs, Empty] \
                                    and type(game.map.get_elem_xy(j + 1, i)) in [Empty, Bush, Portal]:
                                self._labirint[i][j + 1] = 0
                                t = 1
                                while i + t != game.map.get_row() - 1 \
                                        and type(game.map.get_elem_xy(j + 1, i + t)) in [Empty, Bush]:
                                    self._labirint[i + t][j + 1] = 0
                                    t += 1
                    if type(game.map.get_elem_xy(j, i + 1)) in [Stairs, Brick]:
                        if j != 0:
                            if type(game.map.get_elem_xy(j, i)) in [Stairs, Empty] \
                                    and type(game.map.get_elem_xy(j - 1, i)) in [Empty, Bush, Portal]:
                                self._labirint[i][j - 1] = 0
                                t = 1
                                while i + t != game.map.get_row() - 1 and j != game.map.get_col() \
                                        and type(game.map.get_elem_xy(j - 1, i + t)) in [Empty, Bush]:
                                    self._labirint[i + t][j - 1] = 0
                                    t += 1
                    if type(game.map.get_elem_xy(j, i)) == Stairs:
                        t = 1
                        while type(game.map.get_elem_xy(j, i + t)) in [Empty, Bush]:
                            self._labirint[i + t][j] = 0
                            t += 1

    def auto_go(self):
        def searсh_path(data, start, end, shortpath={}, full_path={}, count=0):
            x, y = start
            full_path[(x, y)] = count
            if x == end[0] and y == end[1]:
                return shortpath
            walks = [(-1, 0), (0, 1), (1, 0), (0, -1)]

            for walk_X, walk_Y in walks:
                if 0 <= x + walk_X < len(data) and 0 <= y + walk_Y < len(data[0]):
                    if data[x + walk_X][y + walk_Y] == 0:
                        check = full_path.get((x + walk_X, y + walk_Y), 0)
                        if check != 0 and check > count:
                            full_path[(x + walk_X, y + walk_Y)] = count
                            shortpath[(x + walk_X, y + walk_Y)] = (x, y)
                            searсh_path(data, (x + walk_X, y + walk_Y), end, shortpath, full_path, count + 1)
                        else:
                            if (x + walk_X, y + walk_Y) not in full_path.keys():
                                shortpath[(x + walk_X, y + walk_Y)] = (x, y)
                                searсh_path(data, (x + walk_X, y + walk_Y), end, shortpath, full_path, count + 1)
            return shortpath

        def short_path(data, start, end, path=[]):
            if len(path) == 0:
                path.append(end)
            path.append(data[end])
            if data[end] == start:
                return path
            else:
                short_path(data, start, data[end], path)
            return path

        def where_to_go(data, start1, end1):
            start = (int(round(start1[1])), int(round(start1[0])))
            end = (int(round(end1[1])), int(round(end1[0])))
            if start == end:
                short = [(start1[1], start1[0]), (end1[1], end1[0])]
                if start1 == end1:
                    return ""
            else:
                p = searсh_path(self._labirint, start, end, {}, {}, 0)

                short = short_path(p, start, end, [])
                short.reverse()

            move = (round(short[1][1] - short[0][1], 1), round(short[1][0] - short[0][0], 1))
            if (move[0] != 0 and move[1] != 0) or \
                    (fabs(start1[0] - end1[0]) <= self._step and
                     fabs(start1[1] - end1[1]) <= self._step):
                return ""
            dict_move = {(-0.2, 0): "l", (-0.4, 0): "l", (-0.6, 0): "l", (-0.8, 0): "l", (-1, 0): "l",
                         (0, 0.2): "d", (0, 0.4): "d", (0, 0.6): "d", (0, 0.8): "d", (0, 1): "d",
                         (0.2, 0): "r", (0.4, 0): "r", (0.6, 0): "r", (0.8, 0): "r", (1, 0): "r",
                         (0, -0.2): "u", (0, -0.4): "u", (0, -0.6): "u", (0, -0.8): "u", (0, -1): "u"}
            if dict_move[move] in ["u", "d"]:
                if round(int(round(start1[0])) - start1[0], 1) > 0:
                    return "r"
                elif round(int(round(start1[0])) - start1[0], 1) < 0:
                    return "l"

            if dict_move[move] in ["l", "r"]:
                if round(int(round(start1[1])) - start1[1], 1) > 0:
                    return "d"
                elif round(int(round(start1[1])) - start1[1], 1) < 0:
                    return "u"

            return dict_move[move]

        game.hero.set_x(round(game.hero.get_x(), 1))
        game.hero.set_y(round(game.hero.get_y(), 1))
        self._what_doing_now = where_to_go(self._labirint, (self._x, self._y), game.hero.get_xy())

        if self._what_doing_now == self._STOP:
            game.you_lose()


class Digits():
    def __init__(self):
        self._x = 0
        self._y = 0
        self._pic = []
        self._transparency = True
        self._pos_show_pic = randrange(0, 3)

        self.timer_digits = QTimer()
        self.timer_digits.timeout.connect(self.updateValues)
        self.timer_digits.start(500)

    def get_xy(self):
        return self._x, self._y

    def set_xy(self, x, y):
        self._x = x
        self._y = y

    def get_transparency(self):
        return self._transparency

    def updateValues(self):
        self._pos_show_pic += 1
        if self._pos_show_pic == 4:
            self._pos_show_pic = 0

    def get_pic(self):
        return self._pic[self._pos_show_pic]


class Zerro(Digits):
    def __init__(self):
        super().__init__()
        for i in range(4):
            self._pic.append(QPixmap(resource_path("PIC/zerro" + str(i) + ".png")))


class One(Digits):
    def __init__(self):
        super().__init__()
        for i in range(4):
            self._pic.append(QPixmap(resource_path("PIC/one" + str(i) + ".png")))


class EditMap(QWidget):  # класс для создания карты
    def __init__(self):
        self._sp_map = []
        self._elem_map = []
        self._activ_pic = 0
        self._mouse_x = 0
        self._mouse_y = 0
        self._flag_1 = False
        self._flag_2 = True
        self._col = 14
        self._row = 14
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)  #
        self.setMouseTracking(True)  # отслеживаем положение мыши
        self.resize(200, 100)  # задаем размер окна с параметрами размеров карты
        self.center()  # отцентровываем окно относительно экрана

        self.setWindowTitle('Редактор карты')

        self.input_col = QLineEdit(str(self._col), self)  # создаем строку для ввода x
        self.input_col.resize(50, 25)  # задаем размер строки для ввода x
        self.input_col.move(30, 0)  # задаем положение строки для ввода x в окне с параметрами размеров карты

        self.input_row = QLineEdit(str(self._row), self)  # создаем строку для ввода y
        self.input_row.resize(50, 25)  # задаем размер строки для ввода y
        self.input_row.move(120, 0)  # задаем положение строки для ввода y в окне с параметрами размеров карты

        self.button_new_map = QPushButton("СОЗДАТЬ КАРТУ", self)  # создаем кнопку "СОЗДАТЬ КАРТУ"
        self.button_new_map.resize(140, 50)  # задаем размер кнопки "СОЗДАТЬ КАРТУ"
        self.button_new_map.move(30, 50)  # задаем положение кнопки "СОЗДАТЬ КАРТУ" в окне с параметрами размеров карты
        self.button_new_map.clicked.connect(self.new_map)  # ждем событие от кнопки "СОЗДАТЬ КАРТУ"

        self.button_create = QPushButton("СОЗДАТЬ", self)  # создаем кнопку "СОЗДАТЬ"
        self.button_create.resize(70, 30)  # задаем размер кнопки "СОЗДАТЬ"
        self.button_create.setVisible(False)  # прячем кнопку "СОЗДАТЬ"
        self.button_create.clicked.connect(self.create_map)  # ждем событие от кнопки "СОЗДАТЬ"

        self.button_open = QPushButton("ОТКРЫТЬ", self)  # создаем  кнопку "ОТКРЫТЬ"
        self.button_open.resize(70, 30)  # задаем размер кнопки "ОТКРЫТЬ"
        self.button_open.setVisible(False)  # прячем кнопку "ОТКРЫТЬ"
        self.button_open.clicked.connect(self.open_map)  # ждем событие от кнопки "ОТКРЫТЬ"

        self.button_save = QPushButton('СОХРАНИТЬ', self)  # создаем кнопку "СОХРАНИТЬ"
        self.button_save.resize(70, 30)  # задаем размер кнопки "СОХРАНИТЬ"
        self.button_save.setVisible(False)  # прячем кнопку "СОХРАНИТЬ"
        self.button_save.clicked.connect(self.save_map)  # ждем событие от кнопки "СОХРАНИТЬ"

        self.button_back = QPushButton("НАЗАД", self)  # создаем кнопку "НАЗАД"
        self.button_back.resize(70, 30)  # задаем размер кнопки "НАЗАД"
        self.button_back.setVisible(False)  # прячем кнопку "НАЗАД"
        self.button_back.clicked.connect(self.close)  # ждем событие от кнопки "НАЗАД"

        self.timer_edit_map = QTimer()
        self.timer_edit_map.timeout.connect(self.updateValues)
        self.timer_edit_map.start(200)

    def new_map(self):  # метод класса Edit_Map, новая карта
        if (not self.input_col.text().isdigit() or not self.input_row.text().isdigit()) or \
                (int(self.input_col.text()) < 14 or int(self.input_row.text()) < 14):
            # проверяем значения x, y. Если не числа, то выводим окно ошибки
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")  # текст окна msg
            msg.setWindowTitle("Error")  # название окна msg
            msg.exec_()
            return

        self._col = int(self.input_col.text())  # запоминаем новое значение x
        self._row = int(self.input_row.text())  # запоминаем новое значение y
        self._sp_map = [[0 for i in range(self._col)] for j in range(self._row)]  # создаем список 0 по размерам x, y

        self.input_col.setVisible(False)  # прячем строку для ввода x
        self.input_row.setVisible(False)  # прячем строку для ввода y
        self.button_new_map.setVisible(False)  # прячем кнопку "СОЗДАТЬ КАРТУ"

        edit_map.move_button()  # Расширяем окно и меняем положение кнопок "ОТКРЫТЬ", "НАЗАД", "СОЗДАТЬ", "СОХРАНИТЬ"

        self.button_back.setVisible(True)  # показываем кнопку "НАЗАД"
        self.button_save.setVisible(True)  # показываем кнопку "СОХРАНИТЬ"
        self.button_open.setVisible(True)  # показываем кнопку "ОТКРЫТЬ"
        self.button_create.setVisible(True)  # показываем кнопку "СОЗДАТЬ"
        self.center()  # отцентровываем окно относительно экрана

        for i in range(PIC):  # записываем в elem_map изображения из которых будет состоять карта
            self._elem_map.append(QPixmap())
            self._elem_map[i].load(resource_path("PIC/" + str(i) + "_0.png"))
        self._flag_1 = True

    def center(self):  # функция отцентровывает окно относительно окна
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def paintEvent(self, event):
        if self._flag_1:
            qp = QPainter()
            qp.begin(self)

            qp.setBrush(QColor(255, 237, 0))  # задаем желтый цвет для рамки выбора
            qp.drawRect(self._col * 40 + 15, self._activ_pic * 50, 50, 50)  # задаем положение и размер рамки выбора

            for i in range(self._col):
                for j in range(self._row):
                    qp.setBrush(QColor(50, 50, 50))
                    qp.drawRect(i * 40, j * 40, 40, 40)
                    qp.drawPixmap(i * 40, j * 40, self._elem_map[self._sp_map[j][i]])  # рисуем картинками из elem_map

            for i in range(PIC):
                qp.drawPixmap(self._col * 40 + 20, i * 50 + 5, self._elem_map[i])

            if self._mouse_x < self._col * 40 and self._mouse_y < self._row * 40:
                qp.drawPixmap(self._mouse_x - 30, self._mouse_y - 30, self._elem_map[self._activ_pic])
            qp.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._mouse_x < self._col * 40 and self._mouse_y < self._row * 40:
                self._sp_map[self._mouse_y // 40][self._mouse_x // 40] = self._activ_pic
            for i in range(PIC):
                if self._col * 40 + 20 < self._mouse_x < self._col * 40 + 80 and \
                        i * 50 + 5 < self._mouse_y < i * 50 + 65:
                    self._activ_pic = i
                    break

    def mouseMoveEvent(self, event):
        self._mouse_x = event.x()
        self._mouse_y = event.y()

    def create_map(self):
        self.button_create.setVisible(False)
        self.button_open.setVisible(False)
        self.button_save.setVisible(False)
        self.button_back.setVisible(False)
        self._flag_1 = False
        self.input_col.setVisible(True)
        self.input_row.setVisible(True)
        self.button_new_map.setVisible(True)
        self.resize(200, 100)
        self.center()

    def save_map(self):
        stroka = ''
        for j in range(self._row):
            for i in range(self._col):
                stroka += str(self._sp_map[j][i])
            stroka += '\n'
        file_save_map = QFileDialog.getSaveFileName(self, filter='*.map')[0]
        if file_save_map != '':
            f = open(file_save_map, 'w', encoding="utf8")
            with f:
                f.write(stroka[:-1])
                self._flag_2 = False
            f.close()

    def open_map(self):
        file_save_map = QFileDialog.getOpenFileName(self, filter='*.map')[0]
        f = open(file_save_map, encoding="utf8")
        with f:
            old_map = f.readlines()
        f.close()
        self._row = len(old_map)
        self._col = len(old_map[0]) - 1
        self._sp_map = []
        for j in range(self._row):
            self._sp_map.append([])
            for i in range(self._col):
                self._sp_map[j].append(int(old_map[j][i]))
        edit_map.move_button()
        self.center()

    def close(self):
        if self._flag_2:
            result = QMessageBox.question(self, "ПРЕДУПРЕЖДЕНИЕ!", "Сохранить карту?", QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
            if result == QMessageBox.Yes:
                edit_map.save_map()
        self.setVisible(False)
        game.setVisible(True)

    def updateValues(self):
        self.update()

    def move_button(self):
        self.resize(self._col * 40 + 100, self._row * 40)
        # расширяем окно по параметрам x, y, добавляем 100 по х для elem_map
        self.button_back.move(self._col * 40 + 15, self._row * 40 - 30)  # задаем положение кнопки "НАЗАД"
        self.button_save.move(self._col * 40 + 15, self._row * 40 - 60)  # задаем положение кнопки "СОХРАНИТЬ"
        self.button_open.move(self._col * 40 + 15, self._row * 40 - 90)  # задаем положение кнопки "ОТКРЫТЬ"
        self.button_create.move(self._col * 40 + 15, self._row * 40 - 120)  # задаем положение кнопки "СОЗДАТЬ"


class Game(QWidget):
    def __init__(self):
        super().__init__()
        self._flag_1 = False
        self.media = QtCore.QUrl.fromLocalFile("MP3/music.mp3")
        content = QtMultimedia.QMediaContent(self.media)
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setMedia(content)
        self.player.setVolume(50)
        self.initUI()

    def initUI(self):
        self.file_number = 2
        self._score = 0
        self.setMouseTracking(True)
        self.resize(500, 500)
        self.center()
        self.setWindowTitle('Игра')

        self.main_pic = QLabel(self)
        self.main_pic.setPixmap(QPixmap(resource_path("PIC/running_rabbit.jpg")))
        self.main_pic.resize(500, 500)

        self.button_start_game = QPushButton("НАЧАТЬ ИГРУ", self)
        self.button_start_game.resize(140, 50)
        self.button_start_game.move(70, 300)
        self.button_start_game.clicked.connect(self.start_game)

        self.button_edit_map = QPushButton("СОЗДАТЬ КАРТУ", self)
        self.button_edit_map.resize(140, 50)
        self.button_edit_map.move(70, 360)
        self.button_edit_map.clicked.connect(self.edit_map_menu)

        self.button_exit = QPushButton("ЗАКОНЧИТЬ СЕАНС", self)
        self.button_exit.resize(140, 50)
        self.button_exit.move(70, 420)
        self.button_exit.clicked.connect(self.exit)

        self.timer_game = QTimer()
        self.timer_game.timeout.connect(self.updateValues)
        self.timer_game.start(200)
        self.setFocusPolicy(Qt.StrongFocus)

        self.lable_score = QLabel(self)
        self.lable_score.resize(200, 35)
        self.lable_score.setFont(QFont("RetroComputer[RUS by Daymarius]", 26, QFont.Bold))
        self.lable_score.setVisible(False)

        self.button_menu = QPushButton("НАЗАД", self)
        self.button_menu.resize(120, 40)
        self.button_menu.clicked.connect(self.show_menu)
        self.button_menu.setVisible(False)

        self.lable_name = QLabel("ВВЕДИТЕ ВАШЕ ИМЯ:", self)
        self.lable_name.sizeHint()
        self.lable_name.setFont(QFont("RetroComputer[RUS by Daymarius]", 10, QFont.Bold))
        self.lable_name.move(230, 300)

        self.input_name = QLineEdit("Без имени", self)
        self.input_name.resize(200, 20)
        self.input_name.move(230, 325)

        self.table_score = QTableWidget(self)
        self.table_score.resize(200, 120)
        self.table_score.move(230, 350)

    def bd_score(self):
        con = sqlite3.connect(resource_path("DB/score.db"))
        # Создание курсора
        cur = con.cursor()
        # Выполнение запроса и получение всех результатов
        result = cur.execute("SELECT * FROM main ORDER BY score DESC;").fetchmany(5)
        cur.execute("DROP TABLE main")
        cur.execute("CREATE TABLE main (name STRING, score INTEGER)")
        for item in result:
            cur.execute("INSERT INTO main VALUES(?, ?)", (item[0], item[1]))
            con.commit()
        # Вывод результатов на экран
        if result != []:
            self.table_score.setColumnCount(len(result[0]))
            self.table_score.setRowCount(0)
            for i, row in enumerate(result):
                self.table_score.setRowCount(self.table_score.rowCount() + 1)
                for j, elem in enumerate(row):
                    item = QTableWidgetItem(str(elem))
                    self.table_score.setItem(i, j, item)
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.table_score.setHorizontalHeaderItem(0, QTableWidgetItem("Имя игрока"))
            self.table_score.setHorizontalHeaderItem(1, QTableWidgetItem("Счет"))
            self.table_score.setColumnWidth(0, 127)
            self.table_score.setColumnWidth(1, 20)
        con.close()

    def append_bd_score_and_name(self):
        con = sqlite3.connect("DB/score.db")
        # Создание курсора
        cur = con.cursor()
        cur.execute("INSERT INTO main VALUES(?, ?)", (self.input_name.text(), self.get_score()))
        con.commit()
        self.bd_score()
        con.close()

    def get_score(self):
        return self._score

    def set_score(self, score):
        self._score = score

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.hero.go_right()
        elif event.key() == Qt.Key_Left:
            self.hero.go_left()
        elif event.key() == Qt.Key_Up:
            self.hero.go_up()
        elif event.key() == Qt.Key_Down:
            self.hero.go_down()
        elif event.key() == Qt.Key_Space:
            self.hero.go_dig()

    def keyReleaseEvent(self, QKeyEvent):
        if self._flag_1 and not QKeyEvent.isAutoRepeat():
            self.hero.stop()

    def edit_map_menu(self):
        game.setVisible(False)
        edit_map.create_map()
        edit_map.show()

    def exit(self):
        sys.exit(app.exec())

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def reload_game(self):
        score = self.get_score()
        lifes = self.hero.get_lifes()
        self.start_game()
        self.set_score(score)
        self.hero.set_lifes(lifes)

    def start_game(self):
        self.player.play()
        self.set_score(0)
        self.map = Map(resource_path("MAP/" + str(self.file_number) + ".map"))
        for enemy in self.enemies:
            enemy.create_labirint()
        self.button_menu.setVisible(True)
        self.button_menu.setFocusPolicy(False)
        self.lable_score.setVisible(True)
        self.lable_score.move(0, 0)
        self.button_menu.move(self.map.get_col() * 40 - 120, 0)
        self.lable_score.setText("00000")
        sp_0_1 = []
        for j in range(self.map.get_row()):
            for i in range(self.map.get_col()):
                if type(self.map.get_elem_xy(i, j)) == Empty and (
                        self.map.get_row() - 1 == j or type(self.map.get_elem_xy(i, j + 1))
                        in [Stairs, Brick]):
                    sp_0_1.append((i, j))

        zerro = Zerro()
        one = One()
        for i in range(int(round(len(sp_0_1) * 0.2))):
            t = randrange(0, len(sp_0_1))
            x, y = sp_0_1[t]
            self.map.set_elem_xy(x, y, choice([zerro, one]))
            del sp_0_1[t]
        self.hide_menu()

    def show_menu(self):
        self.append_bd_score_and_name()
        game.player.pause()
        self.hero.timer.stop()
        for enemy in self.enemies:
            enemy.timer.stop()
        self.timer_game.stop()
        self.main_pic.show()
        self.table_score.show()
        self.input_name.show()
        self.lable_name.show()
        self.button_menu.setVisible(False)
        self.lable_score.setVisible(False)
        self.button_edit_map.setVisible(True)
        self.button_exit.setVisible(True)
        self.button_start_game.setVisible(True)
        self.resize(500, 500)
        self.center()
        self._flag_1 = False

    def hide_menu(self):
        game.player.play()
        self.hero.timer.start(200)
        for enemy in self.enemies:
            enemy.timer.start(200)
        game.timer_game.start(200)
        self.main_pic.hide()
        self.table_score.hide()
        self.input_name.hide()
        self.lable_name.hide()
        self.button_menu.setVisible(True)
        self.lable_score.setVisible(True)
        self.button_edit_map.setVisible(False)
        self.button_exit.setVisible(False)
        self.button_start_game.setVisible(False)
        self.resize(self.map.get_col() * 40, self.map.get_row() * 40 + 40)
        self.center()
        self._flag_1 = True

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self._flag_1:
            for i in range(self.map.get_col()):
                for j in range(self.map.get_row()):
                    qp.drawPixmap(i * 40, j * 40 + 40,
                                  self.map.get_elem_xy(i, j).get_pic())  # рисуем картинками из elem_map
            qp.drawPixmap(self.hero.get_x() * 40, self.hero.get_y() * 40 + 40, self.hero.get_pic())
            for enemy in self.enemies:
                qp.drawPixmap(enemy.get_x() * 40, enemy.get_y() * 40 + 40, enemy.get_pic())
            for i in range(game.hero.get_lifes()):
                qp.drawPixmap(280 + i * 40, 0, self.hero._pic[self.hero._STOP][0])

            txt = "00000" + str(self._score)
            self.lable_score.setText(txt[len(txt) - 5: len(txt)])
        qp.end()

    def updateValues(self):
        self.update()

    def you_lose(self):
        self.player.pause()
        self.hero.timer.stop()
        for enemy in self.enemies:
            enemy.timer.stop()
        self.timer_game.stop()
        if self.hero.get_lifes() > 1:
            game.player.pause()
            buttonReply = QMessageBox.question(self, 'ВЫ ПРОИГРАЛИ', "Продолжить игру?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if buttonReply == QMessageBox.Yes:
                self.hero.set_lifes(self.hero.get_lifes() - 1)
                self.reload_game()
                self.timer_game.start(200)
            else:
                self.set_score(0)
                self.show_menu()
        else:
            game.player.pause()
            buttonReply = QMessageBox.information(self, 'ИГРА ОКОНЧЕНА', "Вы проиграли.")
            self.append_bd_score_and_name()
            self.show_menu()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("PIC/5_0.png")))
    game = Game()
    game.show()
    game.bd_score()
    edit_map = EditMap()

    sys.exit(app.exec())

import sys
# import os
# import subprocess
import json

from collections import deque

from PyQt5.QtGui import QContextMenuEvent
from audit import AUDIT_FILTER_EXCLUDE
from matplotlib.backend_bases import MouseButton
from screeninfo import get_monitors

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, \
    QGraphicsItem

for monitor in get_monitors():
    monitor_width = int(monitor.width)
    monitor_height = int(monitor.height)


def QColor_to_hex(qcolor):
    return '#{:02X}{:02X}{:02X}'.format(qcolor.red(), qcolor.green(), qcolor.blue())


def hex_to_QColor(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return QtGui.QColor(r, g, b)


class ConfirmationDialog(QtWidgets.QDialog):
    def __init__(self, reason, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.reason = reason
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(f"Are you sure {self.reason}?")
        self.setFixedSize(400, 200)  # Фиксируем размер окна

        label_text = f"Are you sure {self.reason}?"
        self.label = QtWidgets.QLabel(label_text, self)

        self.yes_button = QtWidgets.QPushButton("YES", self)
        self.no_button = QtWidgets.QPushButton("NO", self)

        # Размещаем элементы управления с помощью менеджеров компоновки
        vbox_layout = QtWidgets.QVBoxLayout()
        hbox_layout = QtWidgets.QHBoxLayout()

        vbox_layout.addWidget(self.label)
        hbox_layout.addStretch(1)
        hbox_layout.addWidget(self.yes_button)
        hbox_layout.addWidget(self.no_button)
        hbox_layout.addStretch(1)

        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)

        # Подключаем обработчики событий
        self.yes_button.clicked.connect(self._yes)
        self.no_button.clicked.connect(self._no)

    def _yes(self):
        self.accept()  # Закрывает диалог и возвращает результат

    def _no(self):
        self.reject()  # Закрывает диалог и возвращает результат


class Settings(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Настройкти")
        self.setFixedSize(400, 300)  # Фиксируем размер окна

        # Установка стиля
        self.setStyleSheet("background-color: gray;")


# ставим QDialog чтобы было модальное окно, оно делает невозможность взаимодействия с другими окнами пока полльзователь не зароет это
class About_program(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)  # Устанавливаем модальность окна
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("О программе")
        self.setFixedSize(400, 300)  # Фиксируем размер окна

        # Установка стиля
        self.setStyleSheet("background-color: white;")

        # Создание layout для размещения элементов
        layout = QtWidgets.QVBoxLayout()

        # Создание QTextEdit для отображения текста
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setReadOnly(True)  # Делаем текстовое поле только для чтения
        self.load_description()  # Загружаем текст из файла

        # Кнопка закрытия
        close_button = QtWidgets.QPushButton("Закрыть")
        close_button.clicked.connect(self.close)  # Закрываем окно при нажатии

        # Добавление элементов в layout
        layout.addWidget(self.text_edit)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_description(self):  # функция для отображения текста
        try:
            with open("About_program.txt", "r", encoding="utf-8") as file:
                description = file.read()
                self.text_edit.setPlainText(description)
        except FileNotFoundError:
            self.text_edit.setPlainText("Файл описания не найден.")
        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при загрузке описания: {str(e)}")


class Algorithms:
    def __init__(self, parent=None, orientation=False, weighted=False):
        self.parent = parent
        self.orientation = orientation
        self.weighted = weighted

    def BFS(self, graph, start_vertex):
        # Создаем очередь для хранения вершин, которые нужно посетить
        queue = deque()
        queue.append(start_vertex)

        # Массив для отслеживания посещенных вершин
        visited = [False] * len(graph)
        visited[start_vertex] = True

        while queue:
            current_vertex = queue.popleft()

            self.parent.add_hints_text(f"Визит в вершину {current_vertex + 1}", "\n")

            for i in range(len(graph[current_vertex])):
                if not visited[i] and graph[current_vertex][i]:
                    visited[i] = True
                    queue.append(i)

    def DFS(self, graph, start_vertex):
        """Обход графа в глубину (DFS)."""

        def dfs_recursive(vertex, visited):
            visited[vertex] = True
            self.parent.add_hints_text(f"Визит в вершину {vertex + 1}", "\n")

            for i in range(len(graph[vertex])):
                if not visited[i] and graph[vertex][i]:
                    dfs_recursive(i, visited)

        visited = [False] * len(graph)
        dfs_recursive(start_vertex, visited)


class SortedPointDict:
    def __init__(self):
        self.data = {}  # Основной словарь {точка: [[связанная точка, рёро которым связано], ...] ...}
        self.sorted_keys = []  # Список точек, отсортированный по label.toPlainText()

    def __setitem__(self, point, connected_points):
        if point not in self.data:
            self.sorted_keys.append(point)
            self.sort_keys()
        # Сортируем связанные точки перед добавлением
        self.data[point] = connected_points
        self.sort_values()

    def __getitem__(self, point):
        return self.data[point]

    def __delitem__(self, point):
        del self.data[point]
        self.sorted_keys.remove(point)

    def __contains__(self, point):
        return point in self.data

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for point in self.sorted_keys:
            yield point

    def clear(self):
        self.data = {}
        self.sorted_keys = []

    def keys(self):
        return self.sorted_keys

    def values(self):
        return [self.data[point] for point in self.sorted_keys]

    def items(self):
        return [(point, self.data[point]) for point in self.sorted_keys]

    def sort_keys(self):
        """Сортировка точек по метке."""
        self.sorted_keys.sort(key=lambda point: int(point.label.toPlainText()))

    def sort_values(self):
        """Сортировка значений (связанных точек) для каждого ключа."""
        for key in self.data:
            if (len(self.data[key]) != 0):
                self.data[key] = sorted(self.data[key], key=lambda p: int(p[0].label.toPlainText()))

    def sort_all(self):
        """Сортировка ключей и значений."""
        self.sort_keys()
        self.sort_values()

    def __repr__(self):
        return f"{[(point.label.toPlainText(), [(p.label.toPlainText(), (ed.start_v.label.toPlainText(), ed.end_v.label.toPlainText())) for p, ed in connected_points]) for point, connected_points in self.items()]}"


class SignalEmitter(QtCore.QObject):
    """Класс для работы с сигналами."""
    positionChanged = QtCore.pyqtSignal()  # Сигнал для изменения позиции

    def __init__(self, parent=None):
        super().__init__(parent)


class LabeledEllipse(QGraphicsEllipseItem):
    def __init__(self, x, y, size, color, label, parent=None):
        super().__init__(-size / 2, -size / 2, size, size, parent)  # Инициализируем QGraphicsEllipseItem
        self.setPos(x, y)
        self.color = color

        self.setZValue(1)

        # Добавляем объект для сигналов
        self.signals = SignalEmitter()

        # Настройка внешнего вида вершины
        self.setBrush(QtGui.QBrush(color))
        self.setPen(QtGui.QPen(QtGui.QColor("#000000"), 0))  # Убираем обводку

        # Создаём метку с номером
        self.label = QtWidgets.QGraphicsTextItem(str(label), self)
        self.label.setDefaultTextColor(QtGui.QColor("#000000"))  # Устанавливаем цвет по умолчанию
        self.update_text_font(size)  # Настраиваем размер текста
        self.update_text_position(size)  # Центрируем текст
        self.update_text_color()  # Обновляем цвет текста в зависимости от цвета вершины

        self.label.setZValue(1000)

        # Устанавливаем флаги для перемещения и выделения
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)

        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def contextMenuEvent(self, event):
        """Контекстное меню для вершины."""
        menu = QtWidgets.QMenu()

        # Действие для изменения цвета вершины
        change_color_action = menu.addAction("Изменить цвет")
        change_color_action.triggered.connect(self.change_color)

        # Действие для изменения размера вершины
        change_size_action = menu.addAction("Изменить размер")
        change_size_action.triggered.connect(self.change_size)

        # Показать меню
        menu.exec(event.screenPos())

    def change_color(self):
        """Изменение цвета вершины."""
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.setBrush(QtGui.QBrush(color))
            self.update_text_color()

    def change_size(self):
        """Изменение размера вершины."""
        new_size, ok = QtWidgets.QInputDialog.getInt(
            None, "Изменить размер", "Введите новый размер:", int(self.rect().width()), 5, 50
        )
        if ok:
            self.set_size(new_size)

    # def paint(self, painter, option, widget):
    #     # Проверяем, выбран ли элемент
    #     if self.isSelected():
    #         print(painter.brush())
    #         print(option.palette)
    #         # Если выбран, просто отрисуем круг без рамки
    #         painter.drawEllipse(self.rect())
    #     else:
    #         # Если не выбран, отрисуем круг с заливкой и рамкой
    #         painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 200, 255)))  # Цвет заливки
    #         painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))  # Цвет рамки и ее толщина
    #         painter.drawEllipse(self.rect())

    def itemChange(self, change, value):
        super().itemChange(change, value)
        # Проверяем, если изменена позиция объекта
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            self.signals.positionChanged.emit()  # Отправляем сигнал через SignalEmitter
        return super().itemChange(change, value)

    def set_label(self, label):
        """Изменить номер (метку)"""
        self.label.setPlainText(str(label))
        self.update_text_position(self.rect().width())  # Перерасчёт позиции текста
        self.update_text_color()  # Перепроверка цвета текста

    def update_text_font(self, size):
        """Обновляем размер шрифта текста в зависимости от размера вершины и длины текста."""
        text_length = len(self.label.toPlainText())
        font_size = size * 0.8 / (1 + 0.3 * (text_length - 1)) - 1  # Уменьшаем шрифт, если текст длинный
        font = self.label.font()
        font.setPointSizeF(font_size)
        self.label.setFont(font)

    def update_text_position(self, size):
        """Обновляем позицию текста, чтобы он оставался в центре вершины"""
        text_rect = self.label.boundingRect()
        self.label.setPos(-text_rect.width() / 2, -text_rect.height() / 2)

    def update_text_color(self):
        """Обновляем цвет текста в зависимости от фона вершины"""
        color = self.brush().color()
        brightness = color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
        text_color = QtGui.QColor(255, 255, 255) if brightness < 128 else QtGui.QColor(0, 0, 0)
        self.label.setDefaultTextColor(text_color)

    def set_size(self, size):
        """Обновление размера вершины и перенастройка текста"""
        self.setRect(-size / 2, -size / 2, size, size)
        self.update_text_font(size)
        self.update_text_position(size)


class GraphEdge(QGraphicsLineItem):
    """Класс для рёбер графа"""

    def __init__(self, start, end, color, weight=0, parent=None):
        super().__init__(parent)
        self.start_v = start
        self.end_v = end
        self.weight = weight

        self.setZValue(0)

        self.setPen(QtGui.QPen(QtGui.QColor(color), 2))

        self.label = QtWidgets.QGraphicsTextItem(self)
        self.label.setDefaultTextColor(QtGui.QColor("#000000"))

        self.label.setZValue(1000)

        self.update_position()

        self.start_v.signals.positionChanged.connect(self.update_position)
        self.end_v.signals.positionChanged.connect(self.update_position)

    def contextMenuEvent(self, event):
        """Контекстное меню для ребра."""
        menu = QtWidgets.QMenu()

        # Действие для изменения цвета ребра
        change_color_action = menu.addAction("Изменить цвет")
        change_color_action.triggered.connect(self.change_color)

        # Действие для изменения веса ребра
        change_weight_action = menu.addAction("Изменить вес")
        change_weight_action.triggered.connect(self.change_weight)

        # Показать меню
        menu.exec(event.screenPos())

    def change_color(self):
        """Изменение цвета ребра."""
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.setPen(QtGui.QPen(color, 2))

    def change_weight(self):
        """Изменение веса ребра."""
        new_weight, ok = QtWidgets.QInputDialog.getInt(
            None, "Изменить вес", "Введите новый вес:", self.weight, 0, 100
        )
        if ok:
            self.set_weight(new_weight)

    def update_position(self):
        """Обновить положение линии и текста при перемещении вершин."""
        line = QtCore.QLineF(self.start_v.scenePos(), self.end_v.scenePos())
        self.setLine(line)

        text_position = line.pointAt(0.5)  # 0 - начало, 1 - конец
        self.label.setPos(text_position - QtCore.QPointF(self.label.boundingRect().width() / 2,
                                                         self.label.boundingRect().height() / 2))

        self.update()

    def set_weight(self, weight):
        """Изменить вес ребра."""
        self.weight = weight
        self.label.setPlainText(str(weight))


class GraphArea(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Создаем сцену с очень большим sceneRect
        self.scene = QGraphicsScene(self)
        infinite_size = 10 ** 6  # Задаем большой размер
        self.scene.setSceneRect(-infinite_size, -infinite_size, 2 * infinite_size, 2 * infinite_size)
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Убираем ползунки для рабочей области
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Параметры для точек (вершин графа)
        self.point_size = 10
        self.point_color = QtGui.QColor("#000000")

        # Список смежности (словарь) для хранения вершин и их порядковых номеров
        self.points = SortedPointDict()

        self.start_point = None

        # шаг увеличения
        self.scale_factor = 1.1
        # Стандартное увеличени
        self.scale(2, 2)

        # СПРОСИТЬ КАК ОТРИСОВЫВАТЬ СЕТКУ
        # Параметры сетки
        self.grid_enabled = True  # Флаг для включения сетки
        self.grid_size = 5  # Размер одной ячейки сетки
        self.grid_color = QtGui.QColor(200, 200, 200, 125)  # Цвет сетки (с четвёртым паказателем для прозрачности)
        self.draw_grid()

        # Режимы взаимодействия
        self.move_mode = True
        self.paint_ellipse_mode = False
        self.paint_line_mode = False
        self.delete_mode = False
        self.choise_mode = False
        self.tools_mode = False

    def draw_grid(self):
        pass

    def wheelEvent(self, event):
        """Обработка колесика мыши для масштабирования сцены."""
        if event.angleDelta().y() > 0:
            self.scale(self.scale_factor, self.scale_factor)  # Увеличение
        else:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)  # Уменьшение

    def contextMenuEvent(self, event):
        """Handle context menu events in the graph area."""
        pos = self.mapToScene(event.pos())
        items = self.scene.items(pos)
        print(items)

        if items:
            # Create a context menu
            menu = QtWidgets.QMenu(self)

            # Add actions to the menu
            change_color_action = menu.addAction("Change Color")
            change_size_action = menu.addAction("Change Size")

            # Connect actions to slots
            change_color_action.triggered.connect(lambda: items[1].change_color())
            change_size_action.triggered.connect(lambda: items[1].change_size())

            # Show the menu at the cursor position
            menu.exec(event.globalPos())
        else:
            super().contextMenuEvent(event)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для добавления, удаления или выбора точек."""
        pos = self.mapToScene(event.position().toPoint())
        but = event.button()

        if but == QtCore.Qt.MouseButton.LeftButton:
            fl = 1

            if self.choise_mode:
                for item in self.scene.items(pos):
                    if isinstance(item, QGraphicsEllipseItem):
                        self.start_point = item
                        item.setSelected(True)
                        # Завершаем локальный цикл выбора, если он активен
                        if self.parent.choice_event_loop is not None:
                            self.parent.choice_event_loop.exit()
                        break
                else:
                    self.parent.set_hints_text("Вы не выбрали вершину, попробуйте снова")

            elif self.paint_line_mode and self.start_point is not None and (
                    event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                fl = 0
                items = self.scene.items(pos)
                for item in items:
                    if isinstance(item, QGraphicsEllipseItem) and item != self.start_point:
                        if self.can_add_line(self.start_point, item):
                            self.add_line(self.start_point, item)
                            break

            elif self.paint_line_mode and self.start_point is not None:
                fl = 0
                items = self.scene.items(pos)
                for item in items:
                    if isinstance(item, QGraphicsEllipseItem) and item != self.start_point:
                        if self.can_add_line(self.start_point, item):
                            self.add_line(self.start_point, item)
                            break
                self.start_point = None
                self.scene.clearSelection()

            elif self.paint_line_mode and not (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                self.select_point(pos)

            elif self.paint_ellipse_mode:
                # Добавление новой точки
                self.add_point(pos)

            elif self.delete_mode:
                # Удаление точки при нажатии
                self.delete_obj(pos)

            elif self.move_mode and not (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                # Логика перемещения (можно доработать)
                self.select_point(pos)

            if fl:
                super().mousePressEvent(event)
        elif but == QtCore.Qt.MouseButton.RightButton:
            pass

    def can_add_line(self, start_point, end_point):
        """
        Проверяет, можно ли добавить линию между двумя точками.
        Возвращает True, если линия может быть добавлена, иначе False.
        """
        try:
            if start_point is None or end_point is None:
                return False

            for point, _ in self.points[start_point]:
                if point == end_point:
                    return False

            return True
        except Exception as e:
            return False

    def reverse_edge(self, edge):
        r_edge = GraphEdge(edge.end_v, edge.start_v, edge.weight)
        return r_edge

    def add_line(self, start_vertex, end_vertex, weight=1):
        """Добавление нового ребра между двумя вершинами."""
        try:
            edge = GraphEdge(start_vertex, end_vertex, weight)
            self.scene.addItem(edge)
            self.points[start_vertex].append((end_vertex, edge))
            self.points[end_vertex].append((start_vertex, self.reverse_edge(edge)))
            self.points.sort_values()
        except Exception as e:
            pass

    def find_and_add_line(self, start_id, end_id, weight=1):
        start_vertex = None
        end_vertex = None
        for point in self.points.keys():
            if point.label.toPlainText() == start_id:
                start_vertex = point
            if point.label.toPlainText() == end_id:
                end_vertex = point
            if not start_vertex is None and not end_vertex is None:
                if self.can_add_line(start_vertex, end_vertex):
                    self.add_line(start_vertex, end_vertex, weight)
                break

    def can_add_ellipse(self, new_ellipse):
        # Получаем центр нового элипса в координатах сцены
        new_center = new_ellipse.mapToScene(new_ellipse.rect().center())

        # Проходим по всем объектам на сцене
        for item in self.points.sorted_keys:
            # Получаем центр существующего элипса в координатах сцены
            existing_center = item.mapToScene(item.rect().center())

            # Вычисляем расстояние между центрами
            distance = (
                    new_center - existing_center).manhattanLength()  # создаёт вектор разности между центрами и возвращает сумму абсолютных разностей по осям, или же Манхэттенское расстояние (|х2 - х1|+|у2-у1|).

            # Проверка, что расстояние больше суммы радиусов и минимального расстояния
            if distance < (new_ellipse.rect().width() / 2 + item.rect().width() / 2 + 3):
                return False

        return True

    def add_point(self, pos, *args):
        """Добавление новой точки (вершины) на сцену."""
        if len(args) == 0:
            label = len(self.points) + 1  # Нумерация вершин
            point_item = LabeledEllipse(pos.x(), pos.y(), self.point_size, self.point_color, label)
            if self.can_add_ellipse(point_item):
                self.scene.addItem(point_item)
                if len(self.points):
                    point_item.label.setPlainText(f"{int(self.points.keys()[-1].label.toPlainText()) + 1}")
                    self.points[point_item] = []
                else:
                    point_item.label.setPlainText("1")
                    self.points[point_item] = []
                self.start_point = point_item
            else:
                del point_item
                self.select_point(pos)
        else:
            point_item = LabeledEllipse(pos["x"], pos["y"], args[0]["size"], hex_to_QColor(args[0]["color"]),
                                        args[0]["id"])
            self.scene.addItem(point_item)
            self.points[point_item] = []

    def delete_obj(self, pos):
        """Удаление бъекта на сцене при нажатии на него."""
        items = self.scene.items(pos)

        # Проверка вершин
        for item in items:
            if isinstance(item, QGraphicsEllipseItem):
                # Удаляем рёбра, связанные с вершиной
                for connected_point, edge in self.points[item]:
                    self.scene.removeItem(edge)  # Удаляем ребро из сцены
                    # Также удалим запись об этом ребре у связанной вершины
                    for i in range(len(self.points[connected_point])):
                        if self.points[connected_point][i][0] == item:
                            self.scene.removeItem(self.points[connected_point][i][1])
                            del self.points[connected_point][i]
                            break
                # Теперь удаляем вершину
                self.scene.removeItem(item)
                if self.points.sorted_keys[0] == item and len(self.points.sorted_keys) > 1:
                    self.points.sorted_keys[1].label.setPlainText("1")
                del self.points[item]
                if len(self.points.sorted_keys):
                    self.update_number_on_point()
                self.start_point = None
                self.scene.clearSelection()
                return  # Прерываем обработку, если нашли вершину

        # Проверка рёбер
        threshold = 4  # Пороговое расстояние для удаления линии
        # Проверка линий на близость к месту клика
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                line = item.line()
                dist = self._distance_from_point_to_line(pos, line)
                if dist <= threshold:  # Проверяем расстояние
                    start_v = item.start_v
                    end_v = item.end_v
                    self.scene.removeItem(item)

                    # Удаляем ссылки на ребра из self.points
                    self._update_points(start_v, end_v)
                    self._update_points(end_v, start_v)
                    self.start_point = None
                    self.scene.clearSelection()
                    return  # Прерываем обработку, если удалено ребро

    def _update_points(self, from_vertex, to_vertex):
        """Обновляет структуру self.points, удаляя ссылку на ребро."""
        edges_to_remove = []
        for connected_point, edge in self.points[from_vertex]:
            if connected_point == to_vertex:
                edges_to_remove.append((connected_point, edge))

        for edge in edges_to_remove:
            self.points[from_vertex].remove(edge)

    def _distance_from_point_to_line(self, point, line, end_threshold=10):
        """
        Вычислить расстояние от точки до линии с учётом порога около концов
        и ограничением на принадлежность проекции отрезку.

        :param point: Точка, для которой вычисляется расстояние.
        :param line: Линия, до которой вычисляется расстояние.
        :param end_threshold: Пороговое расстояние от концов линии, в пределах которого расстояние не считается.
        :return: Расстояние от точки до линии или бесконечность, если точка близка к концам или не проецируется на отрезок.
        """
        p1, p2 = line.p1(), line.p2()

        # Вычисляем расстояния от точки до концов линии
        distance_to_p1 = ((point.x() - p1.x()) ** 2 + (point.y() - p1.y()) ** 2) ** 0.5
        distance_to_p2 = ((point.x() - p2.x()) ** 2 + (point.y() - p2.y()) ** 2) ** 0.5

        # Если точка близка к одному из концов, возвращаем бесконечность
        if distance_to_p1 < end_threshold or distance_to_p2 < end_threshold:
            return float('inf')

        # Векторы
        p1_to_p2 = QtCore.QPointF(p2.x() - p1.x(), p2.y() - p1.y())  # Вектор от p1 к p2
        p1_to_point = QtCore.QPointF(point.x() - p1.x(), point.y() - p1.y())  # Вектор от p1 к точке

        # Скалярное произведение и длина вектора
        dot_product = (p1_to_point.x() * p1_to_p2.x() + p1_to_point.y() * p1_to_p2.y())
        segment_length_squared = (p1_to_p2.x() ** 2 + p1_to_p2.y() ** 2)

        # Проекция точки на линию
        projection_length = dot_product / segment_length_squared if segment_length_squared != 0 else -1

        # Координаты проекции на линии
        proj_x = p1.x() + projection_length * p1_to_p2.x()
        proj_y = p1.y() + projection_length * p1_to_p2.y()

        # Проверяем, находится ли проекция внутри сегмента
        if not (min(p1.x(), p2.x()) <= proj_x <= max(p1.x(), p2.x()) and
                min(p1.y(), p2.y()) <= proj_y <= max(p1.y(), p2.y())):
            return float('inf')

        # Вычисляем расстояние от точки до линии
        numerator = abs(
            (p2.y() - p1.y()) * point.x() - (p2.x() - p1.x()) * point.y() + p2.x() * p1.y() - p2.y() * p1.x()
        )
        denominator = line.length()

        return numerator / denominator if denominator != 0 else float('inf')

    def update_number_on_point(self):
        keys = self.points.keys()
        for i in range(len(keys) - 1):
            if int(keys[i + 1].label.toPlainText()) - int(keys[i].label.toPlainText()) > 1:
                for j in range(i + 1, len(keys)):
                    keys[j].label.setPlainText(f"{int(keys[j].label.toPlainText()) - 1}")
                    keys[j].update_text_position(keys[j].rect().width())
                break

    def select_point(self, pos):
        """Выбор точки для перемещения (или дополнительного взаимодействия)."""
        items = self.scene.items(pos)
        for item in items:
            if isinstance(item, QGraphicsEllipseItem):
                # Дополнительная логика для работы с выбранной точкой
                item.setSelected(True)
                self.start_point = item

    def set_point_color(self, color):
        """Изменение цвета точек (вершин)."""
        self.point_color = color

    def set_point_size(self, size):
        """Изменение размера точек (вершин)."""
        self.point_size = size

    def reset_graph(self):
        """Очистка сцены."""
        self.start_point = None
        self.scene.clearSelection()
        self.scene.clear()
        self.points.clear()


class SvgButton(QtWidgets.QPushButton):
    def __init__(self, icon_path):
        super().__init__()
        self.setIcon(QtGui.QIcon(icon_path))


class Grafs(QtWidgets.QMainWindow):  # Используем QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graf++")
        self.resize(int(monitor_width * 0.6), int(monitor_height * 0.6))
        self.color = "#000000"
        self.graph_area = None
        self.alg = Algorithms(self)
        self.wnd_about = None
        self.wnd_settings = None
        self.setupUi()

    def setupUi(self):
        # Создание центрального виджета и его Layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Создаём главные layout
        vertical_layout = QtWidgets.QVBoxLayout(central_widget)
        gorizontal_layout = QtWidgets.QHBoxLayout(central_widget)

        # Создаем панель инструментов
        self.tool_panel = QtWidgets.QFrame()
        self.tool_panel.setStyleSheet("""
        QFrame{
            background-color:  #FFFFFF; /* Цвет фона панели */
            border: 1px solid  #BDBDBD; /* Рамка */
            border-radius: 15px; /* Закругленные углы */
            padding: 10px; /* Отступы внутри панели */
            rgba(0, 0, 0, 0.2); /* Тенб панели */
        }
        QPushButton{
            background-color:  #F0F0F0; /* Цвет фона кнопок */
            border: none; /* Без рамки */
            border-radius: 10px; /* Закругленные углы кнопок */
            padding: 10px; /* Отступы внутри кнопки */
            margin: 5px; /* Отступ между кнопками */
            font-size: 14px; /* Размер шрифта кнопок */
        }
        QPushButton: hover{
            background-color:  #007BFF; /* Цвет фона при наведении */
            color: white; /* Цвет текста при наведении */
        }
        QPushButton: pressed{
            background-color:  #0056b3; /* Цвет фона при нажатии */
        }
        QSlider{
            background-color:  #F0F0F0; /* Цвет фона слайдера */
            border-radius: 5px; /* Закругленныеуглы */
        }
        QSlider::handle: horizontal{
            background:  #007BFF; /* Цвет ползунка */
            width: 10px; /* Ширина ползунка */
            border-radius: 5px; /* Закругленные углы ползунка */
        }
        """)
        self.tool_panel_layout = QtWidgets.QHBoxLayout(self.tool_panel)

        self.tool_panel_layout.setContentsMargins(5, 0, 5, 0)
        self.tool_panel_layout.setSpacing(0)

        # Кнопка "Инструменты"
        # self.tools_button = SvgButton("tools-solid.svg")
        # self.tools_button.setFixedWidth(int(monitor_width * 0.03))
        # self.tools_button.setCheckable(True)
        # self.tools_button.clicked.connect(self.swith_tools_mode)
        # self.tools_button.clicked.connect(self.switch_move_mode)
        # self.tool_panel_layout.addWidget(self.tools_button)

        # Кнопка рисования кругов
        self.paint_ellipse_button = SvgButton("circle-solid.svg")
        self.paint_ellipse_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_ellipse_button.setCheckable(True)
        self.paint_ellipse_button.clicked.connect(self.switch_paint_ellipse_mode)
        self.paint_ellipse_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_ellipse_button)

        # Кнопка рисования линий
        self.paint_line_button = SvgButton("line.svg")
        self.paint_line_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_line_button.setCheckable(True)
        self.paint_line_button.clicked.connect(self.switch_paint_line_mode)
        self.paint_line_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_line_button)

        # Кнопка удаления (корзинка)
        self.erase_button = SvgButton("trash-alt-solid.svg")
        self.erase_button.setFixedWidth(int(monitor_width * 0.03))
        self.erase_button.setCheckable(True)
        self.erase_button.clicked.connect(self.switch_erase_mode)
        self.erase_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.erase_button)

        # Выбор пользовательского цвета
        self.custom_color_button = SvgButton("palette-solid.svg")
        self.custom_color_button.setFixedWidth(int(monitor_width * 0.03))
        self.custom_color_button.clicked.connect(self.choose_custom_color)
        self.tool_panel_layout.addWidget(self.custom_color_button)

        self.color_btn = QtWidgets.QPushButton()
        self.color_btn.setFixedWidth(12)
        self.color_btn.setStyleSheet(f"background-color: {self.color}; border-radius: 6px; width: 12px; height: 12px;")
        self.color_btn.clicked.connect(self.choose_custom_color)
        self.tool_panel_layout.addWidget(self.color_btn)

        # Ползунок для размера точки
        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(3)
        self.size_slider.setMaximum(11)
        self.size_slider.setValue(6)
        self.size_slider.setFixedWidth(int(monitor_width * 0.06))
        self.size_slider.valueChanged.connect(self.change_size)
        self.tool_panel_layout.addWidget(self.size_slider)

        # Кнопка выбора фона
        self.background_button = SvgButton("border-all-solid.svg")
        self.background_button.setFixedWidth(int(monitor_width * 0.03))
        self.background_button.clicked.connect(self.choose_background)
        self.tool_panel_layout.addWidget(self.background_button)

        # Добавляем панель инструментов в layout
        vertical_layout.addWidget(self.tool_panel)

        # Создание боковой панели
        self.side_panel = QtWidgets.QFrame()
        self.side_panel.setStyleSheet("background-color: white;")
        self.side_panel_size = int(self.width() * 0.15)
        self.side_panel.setFixedWidth(self.side_panel_size)  # Ширина боковой панели
        # QSplitter для разделения боковой панели на две части
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # Верхняя часть боковой панели (кнопки)
        top_side_panel = QtWidgets.QWidget()
        top_side_panel_style = "QFrame{" + f"background-color: white; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);" + "}" + "QPushButton{" + f"background-color: #EAEAEA; border: 1px solid #DCDCDC; border-radius: {self.side_panel_size * 0.05}px; padding: {int(self.height() * 0.01)}px {int(self.side_panel_size * 0.005)}px; font-size: {int(self.side_panel_size * 0.068)}px;" + "}" + "QPushButton:hover{" + f"background-color: #007BFF; color: white; border-color: #0069d9;" + "}" + "QPushButton:pressed{" + f"background-color: #0056b3; border-color: #0047a1;" + "}"
        top_side_panel.setStyleSheet(top_side_panel_style)
        top_side_layout = QtWidgets.QVBoxLayout(top_side_panel)

        # Кнопки для верхней части
        self.graph_algorithm_bfs = QtWidgets.QPushButton("Обход графа в ширину")
        self.graph_algorithm_dfs = QtWidgets.QPushButton("Обход графа в глубину")

        self.graph_algorithm_bfs.clicked.connect(self.alghoritms)
        self.graph_algorithm_dfs.clicked.connect(self.alghoritms)

        top_side_layout.addWidget(self.graph_algorithm_bfs)
        top_side_layout.addWidget(self.graph_algorithm_dfs)

        # Прокручиваемая область для верхней части
        top_scroll_area = QtWidgets.QScrollArea()
        top_scroll_area.setWidgetResizable(True)
        top_scroll_area.setWidget(top_side_panel)

        # Нижняя часть боковой панели (текст с подсказками)
        bottom_side_panel = QtWidgets.QWidget()
        bottom_side_panel_style = None
        bottom_side_panel.setStyleSheet("""
                    QWidget {
                        background-color: rgb(200, 200, 250); /* Светло-серый фон */
                    }

                    QLabel {
                        color: black; /* Основной текст черный */
                    }

                    .error {
                        color: red; /* Ошибки будут красного цвета */
                    }
                """)
        bottom_side_layout = QtWidgets.QVBoxLayout(bottom_side_panel)

        # Текст с подсказками
        self.hints_label = QtWidgets.QLabel(self)
        self.hints_label.setWordWrap(True)
        bottom_side_layout.addWidget(self.hints_label)

        # Добавляем растяжимость, чтобы текст был прижатым к верхнему краю
        bottom_side_layout.addStretch(1)

        # Прокручиваемая область для нижней части
        bottom_scroll_area = QtWidgets.QScrollArea()
        bottom_scroll_area.setWidgetResizable(True)
        bottom_scroll_area.setWidget(bottom_side_panel)

        # Добавление частей в splitter
        splitter.addWidget(top_scroll_area)
        splitter.addWidget(bottom_scroll_area)

        # Установка размеров частей splitter'а
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])

        # Добавляем splitter в боковую панель
        side_layout = QtWidgets.QVBoxLayout(self.side_panel)
        side_layout.addWidget(splitter)

        # Добавляем боковую панель в основной layout
        gorizontal_layout.addWidget(self.side_panel)

        # Создание рабочей зоны
        self.graph_area = GraphArea(self)
        gorizontal_layout.addWidget(self.graph_area)  # Добавляем рабочую зону в layout

        self.switch_move_mode()

        # Установка растяжения для боковой панели и рабочей зоны
        # Боковая панель не растягивается, а рабочая зона будет занимать оставшееся пространство
        gorizontal_layout.setStretch(0, 0)  # Боковая панель (не будет растягиваться)
        gorizontal_layout.setStretch(1, 1)  # GraphArea (будет растягиваться)

        vertical_layout.addLayout(gorizontal_layout)

        vertical_layout.setStretch(0, 0)
        vertical_layout.setStretch(1, 1)  # H
        vertical_layout.setStretch(2, 1)

        # Создание меню
        menu_bar = self.menuBar()  # Используем встроенный метод menuBar()
        file_menu = menu_bar.addMenu("File")

        # Создание кнопок в выпадающем меню
        self.new_action = QtGui.QAction("New", self)
        self.save_action = QtGui.QAction("Save", self)
        self.load_action = QtGui.QAction("Load", self)
        self.settings_action = QtGui.QAction("Settings", self)
        self.about_action = QtGui.QAction("About program", self)
        self.exit_action = QtGui.QAction("Exit", self)

        # Подключение действий для кнопок
        self.new_action.triggered.connect(self.new_graf)
        self.save_action.triggered.connect(self.save_graf)
        self.load_action.triggered.connect(self.load_graf)
        self.settings_action.triggered.connect(self.settings)
        self.about_action.triggered.connect(self.about_program)
        self.exit_action.triggered.connect(self.close)

        # Добавление действий в меню
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.settings_action)
        file_menu.addAction(self.about_action)
        file_menu.addSeparator()  # Разделитель между элементами
        file_menu.addAction(self.exit_action)

        # Установка стиля для меню
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #F0F0F0; /* Цвет фона меню */
            }
            QMenu {
                background-color: #FFF; /* Цвет фона выпадающего меню */
            }
            QMenu::item {
                padding: 10px; /* Отступы для пунктов меню */
            }
            QMenu::item:selected {
                background-color: #007BFF; /* Цвет фона при наведении */
                color: white; /* Цвет текста при наведении */
            }
        """)

    def _create_adjacency_matrix(self, graph_points):
        # Шаг 1: Присваиваем каждой вершине уникальный индекс
        vertex_to_index = {v: i for i, v in enumerate(graph_points)}

        # Шаг 2: Создаем пустую матрицу смежности
        num_vertices = len(vertex_to_index)
        adjacency_matrix = [[0] * num_vertices for _ in range(num_vertices)]

        # Шаг 3: Заполнение матрицы смежности
        for vertex, edges in graph_points.items():
            u = vertex_to_index[vertex]
            for pt, edge in edges:
                v = vertex_to_index[pt]
                adjacency_matrix[u][v] = 1

        return adjacency_matrix, vertex_to_index

    def choise_start(self):
        self.graph_area.start_point = None
        self.graph_area.scene.clearSelection()
        self.set_hints_text("Выберите вершину с которой начнётся обход")
        self.graph_area.choise_mode = True
        self.graph_area.paint_line_mode = False
        self.graph_area.paint_ellipse_mode = False
        self.graph_area.delete_mode = False
        self.graph_area.move_mode = False
        self.paint_ellipse_button.setChecked(False)
        self.paint_line_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Создаём локальный цикл событий и запускаем его
        self.choice_event_loop = QtCore.QEventLoop()
        self.choice_event_loop.exec()

        # После завершения цикла проверяем выбор
        if self.graph_area.start_point is None:
            self.set_hints_text("Вы не выбрали вершину. Попробуйте снова.")
        else:
            self.set_hints_text(f"Выбрана вершина: {self.graph_area.start_point.label.toPlainText()}")

    def alghoritms(self):
        text = self.sender().text()
        if len(self.graph_area.points):
            if text == "Обход графа в ширину":
                try:
                    self.choise_start()
                    input_data, vertex_to_index = self._create_adjacency_matrix(self.graph_area.points)
                    self.alg.BFS(input_data, vertex_to_index[self.graph_area.start_point])
                except Exception as e:
                    self.set_error_hint(e)
            elif text == "Обход графа в глубину":
                try:
                    self.choise_start()
                    input_data, vertex_to_index = self._create_adjacency_matrix(self.graph_area.points)
                    self.alg.DFS(input_data, vertex_to_index[self.graph_area.start_point])
                except Exception as e:
                    self.set_error_hint(e)
        self.graph_area.choise_mode = False
        self.switch_move_mode(True)

    def new_graf(self):
        """Метод для создания нового графа."""
        dialog = ConfirmationDialog("you want to clear the graph", self)  # Возможно QMessagebox
        if dialog.exec():
            # Очистка текущего графа
            self.graph_area.reset_graph()

    def tansform_graph(self, points):
        # трансформирование точек
        t_points = [
            {
                "id": pt.label.toPlainText(),
                "pos": {"x": pt.pos().x(), "y": pt.pos().y()},
                "link": [x[0].label.toPlainText() for x in points[pt]],
                "size": pt.rect().width(),
                "color": QColor_to_hex(pt.color),
            }
            for pt in points.keys()]

        data = {
            "points": t_points,
        }
        return json.dumps(data, indent=4)

    def save_graf(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить граф", "", "Graf Files (*.graf)")
        if name:
            with open(name, 'w') as file:
                file.write(self.tansform_graph(self.graph_area.points))

    def load_graf(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Открыть граф", "")
        if name:
            with open(name, 'r') as file:
                graph_data = json.load(file)
            convert_points = graph_data["points"]
            # Восстановить граф, используя полученные данные
            self.graph_area.reset_graph()
            for point in convert_points:
                self.graph_area.add_point(point["pos"], point)
            for point in convert_points:
                for link_point in point["link"]:
                    self.graph_area.find_and_add_line(point["id"], link_point)

    def settings(self):
        self.wnd_settings = Settings(self)  # Создаем экземпляр Settings
        self.wnd_settings.show()  # Используем show() для открытия окна

    def about_program(self):
        self.wnd_about = About_program(self)  # Создаем экземпляр About_program
        self.wnd_about.show()  # Используем show() для открытия окна

    def choose_custom_color(self):
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color = color.name()
            self.graph_area.set_point_color(hex_to_QColor(self.color))
            self.color_btn.setStyleSheet(
                f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size) - 4}px; width: {2 * self.graph_area.point_size - 6}px; height: {2 * self.graph_area.point_size - 6}px;")

    def change_size(self):
        self.graph_area.set_point_size(self.size_slider.value() + 3)  # Меняем размер точки в рабочей области
        self.color_btn.setFixedWidth(2 * self.graph_area.point_size - 6)
        self.color_btn.setStyleSheet(
            f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size) - 3}px; width: {2 * self.graph_area.point_size - 6}px; height: {2 * self.graph_area.point_size - 6}px;")

    def set_hints_text(self, text):
        """Метод для установки текста в область с подсказками."""
        html_text = f"<p><span style='color: black'>{text}</span></p>"
        self.hints_label.setText(html_text)

    def add_hints_text(self, text, splitter=None):
        if splitter is None:
            self.hints_label.setText(self.hints_label.text()[:-11] + text + "</span></p>")
        elif splitter == "\n":
            html_text = f"<p><span style='color: black'>{text}</span></p>"
            self.hints_label.setText(self.hints_label.text() + html_text)

    def set_error_hint(self, error_message):
        """Метод для добавления ошибки в область с подсказками."""
        html_text = f"<p><span class='error'>{error_message}</span></p>"  # <p> - абзац <span> - применение стилей
        self.hints_label.setText(html_text)
        self.hints_label.setProperty("class", "error")
        self.hints_label.style().unpolish(self.hints_label)
        self.hints_label.style().polish(self.hints_label)

    def switch_paint_ellipse_mode(self):
        self.paint_line_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.graph_area.paint_ellipse_mode = True
        self.graph_area.paint_line_mode = False
        self.graph_area.delete_mode = False
        self.graph_area.move_mode = False
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)
        text = """
                Вы в режиме рисования вершин, нажмите на сцену, чтобы поставить вершину.
            """
        self.set_hints_text(text)

    def switch_paint_line_mode(self):
        self.graph_area.paint_line_mode = True
        self.graph_area.paint_ellipse_mode = False
        self.graph_area.delete_mode = False
        self.graph_area.move_mode = False
        self.paint_ellipse_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)
        text = """
                Вы в режиме рисования рёбер, выделите одну вершину нажатием, а затем нажмите на другую вершину.
                Зажав Ctrl, при выбранной вершине, вы можете нарисовать несколько ребер от неё.
            """
        self.set_hints_text(text)

    def switch_erase_mode(self):
        self.graph_area.delete_mode = True
        self.graph_area.paint_ellipse_mode = False
        self.graph_area.paint_line_mode = False
        self.graph_area.move_mode = False
        self.paint_ellipse_button.setChecked(False)
        self.paint_line_button.setChecked(False)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)
        text = """
                Вы в режиме удаления, нажмите на объект, чтобы удалить его.
                (На вершину или ближе к середине ребра).
            """
        self.set_hints_text(text)

    # def swith_tools_mode(self): если вернуть, то дополнить остальные
    #     self.graph_area.tools_mode = True
    #     self.graph_area.delete_mode = False
    #     self.graph_area.paint_ellipse_mode = False
    #     self.graph_area.paint_line_mode = False
    #     self.graph_area.move_mode = False
    #     self.paint_ellipse_button.setChecked(False)
    #     self.paint_line_button.setChecked(False)
    #     self.tools_button.setChecked(False)

    def switch_move_mode(self, missing_text=False):
        if not (
                self.erase_button.isChecked() or self.paint_ellipse_button.isChecked() or self.paint_line_button.isChecked()):
            self.graph_area.move_mode = True
            self.graph_area.paint_ellipse_mode = False
            self.graph_area.paint_line_mode = False
            self.graph_area.delete_mode = False
            self.graph_area.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            self.graph_area.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.graph_area.update()
            if not missing_text:
                text = """
                        Вы в режиме передвижения и выбора.
                        Зажав Ctrl вы сможете выбрать сразу несколько вершин.
                    """
                self.set_hints_text(text)

    def choose_background(self):
        """Переключение сетки на графе."""
        self.graph_area.grid_enabled = not self.graph_area.grid_enabled
        self.graph_area.update()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    wnd = Grafs()
    wnd.show()
    sys.exit(app.exec())

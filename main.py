import time
import sys

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


class Settings(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Настройкти")
        self.setFixedSize(400, 300)  # Фиксируем размер окна

        # Установка стиля
        self.setStyleSheet("background-color: gray;")


class About_program(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
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


class SortedPointDict:
    def __init__(self):
        self.data = {}  # Основной словарь {точка: [связанные точки]}
        self.sorted_keys = []  # Список точек, отсортированный по label.toPlainText()

    def __setitem__(self, point, connected_points):
        if point not in self.data:
            self.sorted_keys.append(point)
            self.sort_keys()
        # Сортируем связанные точки перед добавлением
        self.data[point] = sorted(connected_points, key=lambda p: int(p.label.toPlainText()))

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

    def keys(self):
        return self.sorted_keys

    def values(self):
        return [self.data[point] for point in self.sorted_keys]

    def items(self):
        return [(point, self.data[point]) for point in self.sorted_keys]

    def change_key(self, old_point, new_point):
        """Изменение ключа (точки) в словаре. (подмена на новую с сохранением значений)"""
        if old_point not in self.data:
            raise KeyError(f"Point '{old_point}' not found")
        if new_point in self.data:
            raise KeyError(f"Point '{new_point}' already exists")

        # Перемещаем значение и обновляем ключ
        self.data[new_point] = self.data.pop(old_point)
        self.sorted_keys.remove(old_point)
        self.sorted_keys.append(new_point)
        self.sort_keys()

    def sort_keys(self):
        """Сортировка точек по метке."""
        self.sorted_keys.sort(key=lambda point: int(point.label.toPlainText()))

    def sort_values(self):
        """Сортировка значений (связанных точек) для каждого ключа."""
        for key in self.data:
            self.data[key] = sorted(self.data[key], key=lambda p: int(p.label.toPlainText()))

    def sort_all(self):
        """Сортировка ключей и значений."""
        self.sort_keys()
        self.sort_values()

    def __repr__(self):
        return f"{[(point.label.toPlainText(), [p.label.toPlainText() for p in connected_points]) for point, connected_points in self.items()]}"


class SignalEmitter(QtCore.QObject):
    """Класс для работы с сигналами."""
    positionChanged = QtCore.pyqtSignal()  # Сигнал для изменения позиции

    def __init__(self, parent=None):
        super().__init__(parent)


class LabeledEllipse(QGraphicsEllipseItem):
    def __init__(self, x, y, size, color, label, parent=None):
        super().__init__(-size / 2, -size / 2, size, size, parent)  # Инициализируем QGraphicsEllipseItem
        self.setPos(x, y)

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

        # вспомогательное хранилище для рёбер
        self.edges = []

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

    def draw_grid(self):
        pass

    def wheelEvent(self, event):
        """Обработка колесика мыши для масштабирования сцены."""
        if event.angleDelta().y() > 0:
            self.scale(self.scale_factor, self.scale_factor)  # Увеличение
        else:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)  # Уменьшение

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для добавления, удаления или выбора точек."""
        fl = 1
        pos = self.mapToScene(event.position().toPoint())

        if self.paint_line_mode and self.start_point is not None and (
                event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            fl = 0
            items = self.scene.items(pos)
            for item in items:
                if (isinstance(item, QGraphicsEllipseItem) and item != self.start_point and
                        item not in self.points[self.start_point]):
                    self.add_line(self.start_point, item)
                    self.points[self.start_point].append(item)
                    self.points[item].append(self.start_point)
                    self.points.sort_values()
                    break
        elif self.paint_line_mode and self.start_point is not None:
            fl = 0
            items = self.scene.items(pos)
            for item in items:
                if (isinstance(item, QGraphicsEllipseItem) and item != self.start_point and
                        item not in self.points[self.start_point]):
                    self.add_line(self.start_point, item)
                    self.points[self.start_point].append(item)
                    self.points[item].append(self.start_point)
                    self.points.sort_values()
                    break
            self.start_point = None
            self.scene.clearSelection()
        elif self.paint_line_mode:
            self.select_point(pos)
        elif self.paint_ellipse_mode:
            # Добавление новой точки
            self.add_point(pos)
        elif self.delete_mode:
            # Удаление точки при нажатии
            self.delete_obj(pos)
        elif self.move_mode:
            # Логика перемещения (можно доработать)
            self.select_point(pos)

        if fl:
            super().mousePressEvent(event)

    def add_line(self, start_vertex, end_vertex, weight=1):
        """Добавление нового ребра между двумя вершинами."""
        edge = GraphEdge(start_vertex, end_vertex, weight)
        self.scene.addItem(edge)
        self.edges.append(edge)

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

    def add_point(self, pos):
        """Добавление новой точки (вершины) на сцену."""
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

    def delete_obj(self, pos):
        """Удаление бъекта на сцене при нажатии на него."""
        items = self.scene.items(pos)

        # Проверка вершин
        for item in items:
            if isinstance(item, QGraphicsEllipseItem):
                self.scene.removeItem(item)
                temp = []
                for l in self.edges:
                    if l.start_v == item or l.end_v == item:
                        self.scene.removeItem(l)
                        temp.append(l)
                for l in temp:
                    self.edges.remove(l)
                for p in self.points[item]:
                    self.points[p].remove(item)
                if self.points.sorted_keys[0] == item and len(self.points.sorted_keys) > 1:
                    self.points.sorted_keys[1].label.setPlainText("1")
                del self.points[item]
                if len(self.points.sorted_keys):
                    self.update_number_on_point()
                return  # Прерываем обработку, если нашли вершину

        # Проверка рёбер
        threshold = 5  # Пороговое расстояние для удаления линии
        # Проверка линий на близость к месту клика
        for item in self.edges:
            line = item.line()
            dist = self._distance_from_point_to_line(pos, line)
            if dist <= threshold:  # Проверяем расстояние
                self.scene.removeItem(item)
                self.points[item.start_v].remove(item.end_v)
                self.points[item.end_v].remove(item.start_v)
                self.edges.remove(item)
                return  # Прерываем обработку, если удалено ребро

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
        self.scene.clear()


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
        self.tools_button = SvgButton("tools-solid.svg")
        self.tools_button.setFixedWidth(int(monitor_width * 0.03))
        self.tool_panel_layout.addWidget(self.tools_button)

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
        self.side_panel.setFixedWidth(int(self.width() * 0.15))  # Ширина боковой панели
        side_layout = QtWidgets.QVBoxLayout()
        self.side_panel.setLayout(side_layout)

        # Пример: добавляем кнопки для графов в боковой панели
        self.graph_button1 = QtWidgets.QPushButton("Граф 1")
        self.graph_button2 = QtWidgets.QPushButton("Граф 2")
        side_layout.addWidget(self.graph_button1)
        side_layout.addWidget(self.graph_button2)

        # Добавляем боковую панель в основной layout
        gorizontal_layout.addWidget(self.side_panel)

        # Создание рабочей зоны
        self.graph_area = GraphArea()
        gorizontal_layout.addWidget(self.graph_area)  # Добавляем рабочую зону в layout

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
        file_menu = menu_bar.addMenu("Файл")

        # Создание кнопок в выпадающем меню
        self.new_action = QtGui.QAction("New", self)
        self.save_action = QtGui.QAction("Save", self)
        self.load_action = QtGui.QAction("Load", self)
        self.settings_action = QtGui.QAction("Settings", self)
        self.about_action = QtGui.QAction("About program", self)
        self.exit_action = QtGui.QAction("Exit", self)

        # Подключение действий для кнопок
        self.new_action.triggered.connect(self.new_graf)
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

    def new_graf(self):
        """Метод для создания нового графа."""
        # Очистка и сброс текущего графа
        self.graph_area.reset_graph()

        name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить граф", "", "Graf Files (*.graf)")

    def save_graf(self):
        pass

    def load_graf(self):
        pass

    def settings(self):
        self.wnd_settings = Settings()  # Создаем экземпляр Settings
        self.wnd_settings.show()  # Используем show() для открытия окна

    def about_program(self):
        self.wnd_about = About_program()  # Создаем экземпляр About_program
        self.wnd_about.show()  # Используем show() для открытия окна

    def choose_custom_color(self):
        color = QtWidgets.QColorDialog.getColor()
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

    def switch_paint_ellipse_mode(self):
        self.paint_line_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.graph_area.paint_ellipse_mode = True
        self.graph_area.paint_line_mode = False
        self.graph_area.delete_mode = False
        self.graph_area.move_mode = False
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)

    def switch_paint_line_mode(self):
        self.graph_area.paint_line_mode = True
        self.graph_area.paint_ellipse_mode = False
        self.graph_area.delete_mode = False
        self.graph_area.move_mode = False
        self.paint_ellipse_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)

    def switch_erase_mode(self):
        self.graph_area.delete_mode = True
        self.graph_area.paint_ellipse_mode = False
        self.graph_area.paint_line_mode = False
        self.graph_area.move_mode = False
        self.paint_ellipse_button.setChecked(False)
        self.paint_line_button.setChecked(False)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)

    def switch_move_mode(self):
        if not (
                self.erase_button.isChecked() or self.paint_ellipse_button.isChecked() or self.paint_line_button.isChecked()):
            self.graph_area.move_mode = True
            self.graph_area.paint_ellipse_mode = False
            self.graph_area.paint_line_mode = False
            self.graph_area.delete_mode = False
            self.graph_area.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            self.graph_area.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.graph_area.update()

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

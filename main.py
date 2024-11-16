import time
import sys

from screeninfo import get_monitors

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem

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


class GraphArea(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Создаем сцену с очень большим sceneRect
        self.scene = QGraphicsScene(self)
        infinite_size = 10 ** 6  # Задаем большой размер
        self.scene.setSceneRect(-infinite_size, -infinite_size, 2 * infinite_size, 2 * infinite_size)
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Убираем ползунки для рабочей области
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Параметры для точек (вершин графа)
        self.point_size = 10
        self.point_color = QtGui.QColor("#000000")

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
        fl = 1
        """Обработка нажатия мыши для добавления, удаления или выбора точек."""
        pos = self.mapToScene(event.position().toPoint())

        if self.paint_line_mode:
                fl = 0
                items = self.scene.items(pos)
                for item in items:
                    if isinstance(item, QGraphicsEllipseItem) and item != self.start_point:
                        self.add_line(self.start_point.mapToScene(self.start_point.rect().center()),
                                      item.mapToScene(item.rect().center()))
                        print(546546)
        elif self.paint_ellipse_mode:
            # Добавление новой точки
            self.add_point(pos)
        elif self.delete_mode:
            # Удаление точки при нажатии
            self.delete_point(pos)
        elif self.move_mode:
            # Логика перемещения (можно доработать)
            self.select_point(pos)

        if fl:
            super().mousePressEvent(event)

    def add_line(self, pos1, pos2):
        pass

    def can_add_ellipse(self, new_ellipse):
        # Получаем центр нового элипса в координатах сцены
        new_center = new_ellipse.mapToScene(new_ellipse.rect().center())

        # Проходим по всем объектам на сцене
        for item in self.scene.items():
            if isinstance(item, QGraphicsEllipseItem):
                # Получаем центр существующего элипса в координатах сцены
                existing_center = item.mapToScene(item.rect().center())

                # Вычисляем расстояние между центрами
                distance = (new_center - existing_center).manhattanLength()

                # Проверка, что расстояние больше суммы радиусов и минимального расстояния
                if distance < (new_ellipse.rect().width() / 2 + item.rect().width() / 2 + 3):
                    return False

        return True

    def add_point(self, pos):
        """Добавление новой точки (вершины) на сцену."""
        point_item = QGraphicsEllipseItem(0, 0, self.point_size, self.point_size)
        point_item.setBrush(QtGui.QBrush(self.point_color))

        # Установка обводки
        pen = QtGui.QPen(QtGui.QColor("#000000"))  # Черный цвет обводки
        pen.setWidth(0)  # Устанавливаем толщину обводки в 1 пиксель
        point_item.setPen(pen)

        point_item.setPos(pos.x() - self.point_size / 2, pos.y() - self.point_size / 2)
        point_item.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)  # Включаем перемещение
        point_item.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)  # Включаем выбор
        if self.can_add_ellipse(point_item):
            self.scene.addItem(point_item)
            self.start_point = point_item
        else:
            del point_item

    def delete_point(self, pos):
        """Удаление точки при нажатии на неё."""
        items = self.scene.items(pos)
        for item in items:
            if isinstance(item, QGraphicsEllipseItem):
                self.scene.removeItem(item)

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

        # Кнопка рисования (кисточка)
        self.paint_button = SvgButton("paint-brush-solid.svg")
        self.paint_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_button.setCheckable(True)
        self.paint_button.clicked.connect(self.switch_paint_mode)
        self.paint_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_button)

        # Кнопка рисования кругов
        self.paint_Ellipse_button = SvgButton("")
        self.paint_Ellipse_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_Ellipse_button.setCheckable(True)
        self.paint_Ellipse_button.clicked.connect(self.switch_paint_mode)
        self.paint_Ellipse_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_Ellipse_button)

        # Кнопка рисования линий
        self.paint_Line_button = SvgButton("")
        self.paint_Line_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_Line_button.setCheckable(True)
        self.paint_Line_button.clicked.connect(self.switch_paint_mode)
        self.paint_Line_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_Line_button)

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
                f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size) - 3}px; width: {2 * self.graph_area.point_size - 6}px; height: {2 * self.graph_area.point_size - 6}px;")

    def change_size(self):
        self.graph_area.set_point_size(self.size_slider.value() + 3)  # Меняем размер точки в рабочей области
        self.color_btn.setFixedWidth(2 * self.graph_area.point_size - 6)
        self.color_btn.setStyleSheet(
            f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size) - 3}px; width: {2 * self.graph_area.point_size - 6}px; height: {2 * self.graph_area.point_size - 6}px;")

    def switch_paint_ellipse_mode(self):
        if self.erase_button.isChecked():
            self.erase_button.setChecked(False)
        self.graph_area.move_mode = False
        self.graph_area.paint_mode = True
        self.graph_area.delete_mode = False
        self.graph_area.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.graph_area.update()

    def switch_paint_line_mode(self):
        if self.erase_button.isChecked():
            self.erase_button.setChecked(False)
        self.graph_area.move_mode = False
        self.graph_area.paint_mode = True
        self.graph_area.delete_mode = False
        self.graph_area.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.graph_area.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.graph_area.update()

    def switch_erase_mode(self):
        if self.paint_button.isChecked():
            self.paint_button.setChecked(False)
        self.graph_area.move_mode = False
        self.graph_area.paint_mode = False
        self.graph_area.delete_mode = True
        self.graph_area.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.graph_area.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.graph_area.update()

    def switch_move_mode(self):
        if not (self.erase_button.isChecked() or self.paint_button.isChecked()):
            self.graph_area.move_mode = True
            self.graph_area.paint_mode = False
            self.graph_area.delete_mode = False
            self.graph_area.setCursor(QtCore.Qt.CursorShape.BusyCursor)
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

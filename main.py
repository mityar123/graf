import time

from screeninfo import get_monitors

from PyQt5 import QtCore, QtGui, QtWidgets
import sys

for monitor in get_monitors():
    monitor_width = int(monitor.width)
    monitor_height = int(monitor.height)


def QColor_to_hex(qcolor):
    return '#{:02X}{:02X}{:02X}'.format(qcolor.red(), qcolor.green(), qcolor.blue())


def hex_to_QColor(hex_color):
    hex_color = hex_color.lstrip('#')  # Удаляем символ <code>#</code> в начале
    r = int(hex_color[0:2], 16)  # Красный
    g = int(hex_color[2:4], 16)  # Зеленый
    b = int(hex_color[4:6], 16)  # Синий
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


class Point:
    def __init__(self, kw, kh, size, color=QtGui.QColor(255, 0, 0)):
        self.kw = kw
        self.kh = kh
        self.size = size
        self.color = color


class GraphArea(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.my_width = self.width()
        self.my_height = self.height()
        self.setStyleSheet("background-color: #32CD32;")
        self.reset_graph()
        self.points = []  # Список для хранения точек
        self.offset_x = 0
        self.offset_y = 0
        self.point_size = 10
        self.point_color = QtGui.QColor(0, 0, 0)
        self.temp1 = None
        self.temp2 = None

    def resizeEvent(self, event):
        # Обновляем ширину и высоту на основе текущих размеров виджета
        self.my_width = self.width()
        self.my_height = self.height()
        self.update()  # Обновляем область после изменения размеров
        super().resizeEvent(event)

    def reset_graph(self):
        """Метод для сброса графа."""
        self.points = []  # Очистка данных графа
        self.update()  # Обновление области рисования

    def can_add_point(self, kw, kh):
        """Проверяет, можно ли добавить точку в указанное место."""
        for point in self.points:
            xt = int(self.width() * point.kw) + self.offset_x
            yt = int(self.height() * point.kh) + self.offset_y
            x = int(self.width() * kw) + self.offset_x
            y = int(self.height() * kh) + self.offset_y
            if ((x - xt) ** 2 + (y - yt) ** 2) ** 0.5 <= point.size + self.point_size + 3:
                return False
        return True

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)  # Рамка виджета

        # Рисуем сетку
        grid_color = QtGui.QColor(200, 200, 200)  # Цвет сетки
        painter.setPen(grid_color)

        grid_spacing = 20  # Расстояние между линиями

        # Вертикальные линии с учетом смещения
        for x in range(self.offset_x % grid_spacing, self.width() + grid_spacing, grid_spacing):
            painter.drawLine(x, 0, x, self.height())

        # Горизонтальные линии с учетом смещения
        for y in range(self.offset_y % grid_spacing, self.height() + grid_spacing, grid_spacing):
            painter.drawLine(0, y, self.width(), y)

        # Рисуем точки
        for point in self.points:
            painter.setBrush(QtGui.QBrush(point.color))  # Используем цвет точки
            painter.drawEllipse(
                int(self.width() * point.kw) + self.offset_x - point.size,
                int(self.height() * point.kh) + self.offset_y - point.size,
                point.size * 2,
                point.size * 2
            )  # Рисуем круг вокруг точки

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.RightButton and self.temp1 is not None:
            # Вычисляем новое смещение
            dx = event.pos().x() - self.temp1.x()
            dy = event.pos().y() - self.temp1.y()

            # Применяем смещение
            self.offset_x += dx
            self.offset_y += dy

            # Сохраняем текущее положение мыши для следующих вычислений
            self.temp1 = event.pos()

            self.update()  # Обновление области

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.temp1 = event.pos()  # Сохраняем текущую позицию мыши

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Вычисляем координаты с учетом текущего смещения
            kw = (event.x() - self.offset_x) / self.width()
            kh = (event.y() - self.offset_y) / self.height()
            if self.can_add_point(kw, kh):
                self.points.append(Point(kw, kh, self.point_size, self.point_color))
                self.update()  # Обновляем область для перерисовки

    def wheelEvent(self, evnt):
        if evnt.modifiers() == QtCore.Qt.ControlModifier:
            print(evnt.angleDelta().y())


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
        QFrame
        {
            background - color:  # FFFFFF; /* Цвет фона панели */
                border: 1
        px
        solid  # BDBDBD; /* Рамка */
        border - radius: 15
        px; / *Закругленные
        углы * /
        padding: 10
        px; / *Отступы
        внутри
        панели * /
        box - shadow: 2
        px
        2
        px
        10
        px
        rgba(0, 0, 0, 0.2); / *Тень
        панели * /
        }
        QPushButton
        {
            background - color:  # F0F0F0; /* Цвет фона кнопок */
                border: none; / *Без
        рамки * /
        border - radius: 10
        px; / *Закругленные
        углы
        кнопок * /
        padding: 10
        px; / *Отступы
        внутри
        кнопки * /
        margin: 5
        px; / *Отступ
        между
        кнопками * /
        font - size: 14
        px; / *Размер
        шрифта
        кнопок * /
        }
        QPushButton: hover
        {
            background - color:  # 007BFF; /* Цвет фона при наведении */
                color: white; / *Цвет
        текста
        при
        наведении * /
        }
        QPushButton: pressed
        {
            background - color:  # 0056b3; /* Цвет фона при нажатии */
        }
        QSlider
        {
            background - color:  # F0F0F0; /* Цвет фона слайдера */
                border - radius: 5
        px; / *Закругленные
        углы * /

        }
        QSlider::handle: horizontal
        {
            background:  # 007BFF; /* Цвет ползунка */
                width: 10
        px; / *Ширина
        ползунка * /
        border - radius: 5
        px; / *Закругленные
        углы
        ползунка * /
        }
        """)
        self.tool_panel_layout = QtWidgets.QHBoxLayout(self.tool_panel)

        # Кнопка "Инструменты"
        self.tools_button = QtWidgets.QPushButton("Инструменты")
        self.tool_panel_layout.addWidget(self.tools_button)

        # Выбор пользовательского цвета
        self.custom_color_button = QtWidgets.QPushButton("Выбрать цвет")
        self.custom_color_button.clicked.connect(self.choose_custom_color)
        self.tool_panel_layout.addWidget(self.custom_color_button)

        self.color_btn = QtWidgets.QPushButton()
        self.color_btn.setStyleSheet(f"background-color: {self.color}; border-radius: 10px; width: 20px; height: 20px;")
        self.color_btn.clicked.connect(self.choose_custom_color)
        self.tool_panel_layout.addWidget(self.color_btn)

        # Ползунок для размера точки
        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.size_slider.setMinimum(5)
        self.size_slider.setMaximum(30)
        self.size_slider.setValue(10)
        self.size_slider.valueChanged.connect(self.change_size)
        self.tool_panel_layout.addWidget(self.size_slider)

        # Кнопка удаления (корзинка)
        self.erase_button = QtWidgets.QPushButton("Удалить")
        self.erase_button.clicked.connect(self.enter_erase_mode)
        self.tool_panel_layout.addWidget(self.erase_button)

        # Кнопка выбора фона
        self.background_button = QtWidgets.QPushButton("Выбрать фон")
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
        self.new_action = QtWidgets.QAction("New", self)
        self.save_action = QtWidgets.QAction("Save", self)
        self.load_action = QtWidgets.QAction("Load", self)
        self.settings_action = QtWidgets.QAction("Settings", self)
        self.about_action = QtWidgets.QAction("About program", self)
        self.exit_action = QtWidgets.QAction("Exit", self)

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

    def change_point_size_user(self):
        self.size_user.setText(f"Пользовательский ({self.slider.value()})")
        if self.size_user.isChecked():
            self.graph_area.point_size = int(self.slider.value())

    def choose_custom_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.graph_area.point_color = hex_to_QColor(self.color)
            self.color_btn.setStyleSheet(
                f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size)}px; width: {2 * self.graph_area.point_size}px; height: {2 * self.graph_area.point_size}px;")

    def change_size(self):
        self.graph_area.point_size = self.size_slider.value()  # Меняем размер точки в рабочей области
        self.color_btn.setStyleSheet(
            f"background-color: {self.color}; border-radius: {int(self.graph_area.point_size)}px; width: {2 * self.graph_area.point_size}px; height: {2 * self.graph_area.point_size}px;")

    def enter_erase_mode(self):
        self.graph_area.set_erase_mode(True)  # Вход в режим удаления

    def choose_background(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.graph_area.set_background_color(color.name())  # Устанавливаем цвет фона


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    wnd = Grafs()
    wnd.show()
    sys.exit(app.exec())

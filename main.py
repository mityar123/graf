import time

from screeninfo import get_monitors

from PyQt5 import QtCore, QtGui, QtWidgets
import sys

for monitor in get_monitors():
    monitor_width = int(monitor.width)
    monitor_height = int(monitor.height)


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
    def __init__(self, kw, kh, size):
        self.kw = kw
        self.kh = kh
        self.size = size


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
            if ((x - xt) ** 2 + (y - yt) ** 2) ** 0.5 <= point.size + self.point_size + 5:
                return False
        return True

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)  # Используем текущие размеры

        # Рисуем точки
        painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
        for point in self.points:
            painter.drawEllipse(int(self.width() * point.kw) + self.offset_x - point.size,
                                int(self.height() * point.kh) + self.offset_y - point.size, point.size * 2,
                                point.size * 2)  # Рисуем круг вокруг точки

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
                self.points.append(Point(kw, kh, self.point_size))
                self.update()  # Обновляем область для перерисовки


class Grafs(QtWidgets.QMainWindow):  # Используем QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graf++")
        self.resize(int(monitor_width * 0.6), int(monitor_height * 0.6))
        self.graph_area = None
        self.setupUi()

    def setupUi(self):
        # Создание центрального виджета и его Layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Создаём главные layout
        vertical_layout = QtWidgets.QVBoxLayout(central_widget)
        gorizontal_layout = QtWidgets.QHBoxLayout(central_widget)

        # Создаём панель инструментов
        self.tool_panel = QtWidgets.QFrame()
        self.tool_panel_layout = QtWidgets.QHBoxLayout(self.tool_panel)

        # Создание радиокнопок для выбора размера точки
        self.size_user = QtWidgets.QRadioButton("Пользовательский (10)")
        self.size_small = QtWidgets.QRadioButton("Маленький")
        self.size_medium = QtWidgets.QRadioButton("Средний")
        self.size_large = QtWidgets.QRadioButton("Большой")

        # Устанавливаем начальное состояние (например, средний размер по умолчанию)
        self.size_medium.setChecked(True)

        # Применение стиля к радиокнопкам
        self.size_user.setStyleSheet("""
            QRadioButton {
                padding: 10px; /* Отступы для радиокнопок */
                background-color: #F0F0F0; /* Цвет фона кнопки */
                border: 1px solid #007BFF; /* Цвет рамки */
                border-radius: 5px; /* Закругление углов */
            }
            QRadioButton:checked {
                background-color: #007BFF; /* Цвет фона при выборе */
                color: white; /* Цвет текста при выборе */
            }
            QRadioButton:hover {
                background-color: #E0E0E0; /* Цвет фона при наведении */
            }
        """)

        self.size_small.setStyleSheet(self.size_user.styleSheet())  # Применяем тот же стиль
        self.size_medium.setStyleSheet(self.size_user.styleSheet())  # Применяем тот же стиль
        self.size_large.setStyleSheet(self.size_user.styleSheet())  # Применяем тот же стиль

        # Подключаем сигнал изменения состояния кнопок
        self.size_user.toggled.connect(self.change_point_size_user)
        self.size_small.toggled.connect(self.change_point_size1)
        self.size_medium.toggled.connect(self.change_point_size2)
        self.size_large.toggled.connect(self.change_point_size3)

        # Добавляем радиокнопки в панель инструментов
        self.tool_panel_layout.addWidget(self.size_user)
        self.tool_panel_layout.addWidget(self.size_small)
        self.tool_panel_layout.addWidget(self.size_medium)
        self.tool_panel_layout.addWidget(self.size_large)

        # Создаем ползунок
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(30)
        self.slider.setValue(10)  # Значение по умолчанию
        self.slider.setVisible(False)  # Скрываем ползунок по умолчанию
        self.slider.setFixedHeight(20)
        self.slider.setFixedWidth(
            int(self.size_user.sizeHint().width() * 2) - int(self.size_user.sizeHint().width() * 2) % 29)

        self.slider.sliderMoved.connect(self.change_point_size_user)

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_slider)

        self.size_user.enterEvent = self.show_slider
        self.size_user.leaveEvent = self.on_leave
        self.slider.enterEvent = self.show_slider
        self.slider.leaveEvent = self.on_leave

        # Добавляем ползунок в layout
        vertical_layout.addWidget(self.tool_panel)
        vertical_layout.addWidget(self.slider)

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
        vertical_layout.setStretch(1, 0)  # H
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

    def change_point_size1(self):
        self.graph_area.point_size = 5

    def change_point_size2(self):
        self.graph_area.point_size = 10

    def change_point_size3(self):
        self.graph_area.point_size = 15

    def show_slider(self, event):
        self.slider.setVisible(True)
        self.timer.stop()

    def hide_slider(self):
        self.slider.setVisible(False)

    def on_leave(self, event):
        self.timer.start(1000)  # Запускаем таймер на 1 секунду

    def change_point_size_user(self):
        self.size_user.setText(f"Пользовательский ({self.slider.value()})")
        if self.size_user.isChecked():
            self.graph_area.point_size = int(self.slider.value())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    wnd = Grafs()
    wnd.show()
    sys.exit(app.exec())

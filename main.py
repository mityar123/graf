import sys
import os
import subprocess
import json

import shutil

from screeninfo import get_monitors

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Папка, где будут храниться алгоритмы
ALGORITHMS_DIR = "algorithms"

# Получаем размеры монитора для создания относительного размера приложения
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


# Диалог согласия/отказа
class ConfirmationDialog(QtWidgets.QDialog):
    def __init__(self, reason, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.reason = reason
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(f"Are you sure {self.reason}?")
        self.setFixedSize(400, 200)

        label_text = f"Are you sure {self.reason}?"
        self.label = QtWidgets.QLabel(label_text, self)

        self.yes_button = QtWidgets.QPushButton("YES", self)
        self.no_button = QtWidgets.QPushButton("NO", self)

        vbox_layout = QtWidgets.QVBoxLayout()
        hbox_layout = QtWidgets.QHBoxLayout()

        vbox_layout.addWidget(self.label)
        hbox_layout.addStretch(1)
        hbox_layout.addWidget(self.yes_button)
        hbox_layout.addWidget(self.no_button)
        hbox_layout.addStretch(1)

        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)

        self.yes_button.clicked.connect(self._yes)
        self.no_button.clicked.connect(self._no)

    def _yes(self):
        self.accept()  # Закрывает диалог и возвращает результат "принято"

    def _no(self):
        self.reject()  # Закрывает диалог и возвращает результат "отказано"


# Класс для отображения шаблона
class TemplateDialog(QtWidgets.QDialog):
    def __init__(self, code_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сгенерированный шаблон")
        self.resize(600, 400)

        self.setStyleSheet("""
            QDialog {
                background-color: #F7F7F7;  /* Светлый фон */
                border-radius: 10px;
            }
            QPlainTextEdit {
                background-color: #FFFFFF;  /* Белый фон для текста */
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 10px;
                font-family: Arial, sans-serif;
                font-size: 12pt;
                color: #333;
            }
            QPushButton {
                background-color: #2196F3;  /* Синий цвет */
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12pt;
                margin: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;  /* Темно-синий при наведении */
            }
            QPushButton:pressed {
                background-color: #1565C0;  /* Еще более темный синий при нажатии */
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)

        # Поле для кода
        self.text_edit = QtWidgets.QPlainTextEdit(self)
        self.text_edit.setPlainText(code_text)
        self.text_edit.setReadOnly(True)

        layout.addWidget(self.text_edit)

        copy_button = QtWidgets.QPushButton("Скопировать", self)
        save_button = QtWidgets.QPushButton("Сохранить", self)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(copy_button)
        buttons_layout.addWidget(save_button)

        layout.addLayout(buttons_layout)

        copy_button.clicked.connect(self.copy_to_clipboard)
        save_button.clicked.connect(self.save_to_file)

    def copy_to_clipboard(self):
        QtWidgets.QApplication.clipboard().setText(self.text_edit.toPlainText())
        QtWidgets.QMessageBox.information(self, "Скопировано", "Шаблон скопирован в буфер обмена.")

    def save_to_file(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить шаблон", "", "Python files (*.py)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QtWidgets.QMessageBox.information(self, "Сохранено", f"Шаблон сохранён в:\n{path}")


# Диалог для добавления алгоритмов
class AddAlgorithmDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить алгоритм")
        self.setFixedSize(400, 300)

        self.setStyleSheet("""
            QDialog {
                background-color: #F0F0F0;  /* Очень светлый фон для всего окна */
                border-radius: 10px;
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: #333;
                font-size: 12pt;
            }
            QCheckBox {
                font-size: 12pt;
                color: #333;
            }
            QRadioButton {
                font-size: 12pt;
                color: #333;
            }
            QPushButton {
                background-color: #2196F3;  /* Синий цвет */
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12pt;
                margin: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;  /* Темно-синий при наведении */
            }
            QPushButton:pressed {
                background-color: #1565C0;  /* Еще более темный синий при нажатии */
            }
        """)

        self.config_data = None

        self.vertices_checkbox = QtWidgets.QCheckBox("Передать количество вершин", self)

        self.adjacency_matrix_radio = QtWidgets.QRadioButton("Передать матрицу смежности", self)
        self.adjacency_list_radio = QtWidgets.QRadioButton("Передать список смежности (словарь)", self)

        self.adjacency_group = QtWidgets.QButtonGroup(self)
        self.adjacency_group.addButton(self.adjacency_matrix_radio)
        self.adjacency_group.addButton(self.adjacency_list_radio)

        # По умолчанию выбираем матрицу смежности
        self.adjacency_matrix_radio.setChecked(True)

        self.start_point_checkbox = QtWidgets.QCheckBox("Нужна начальная точка", self)
        self.end_point_checkbox = QtWidgets.QCheckBox("Нужна конечная точка", self)

        self.add_button = QtWidgets.QPushButton("Выбрать файл", self)
        self.cancel_button = QtWidgets.QPushButton("Отмена", self)

        self.create_template_button = QtWidgets.QPushButton("Создать шаблон", self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.vertices_checkbox)
        layout.addWidget(self.adjacency_matrix_radio)
        layout.addWidget(self.adjacency_list_radio)
        layout.addWidget(self.start_point_checkbox)
        layout.addWidget(self.end_point_checkbox)
        layout.addWidget(self.create_template_button)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        layout.addLayout(buttons_layout)

        self.add_button.clicked.connect(self.add_algorithm)
        self.cancel_button.clicked.connect(self.reject)
        self.create_template_button.clicked.connect(self.show_template_dialog)
        self.adjacency_matrix_radio.toggled.connect(self.update_vertices_checkbox_state)
        self.adjacency_list_radio.toggled.connect(self.update_vertices_checkbox_state)
        self.update_vertices_checkbox_state()

    def update_vertices_checkbox_state(self):
        if self.adjacency_list_radio.isChecked():
            # Для списка обязательно указывать количество вершин
            self.vertices_checkbox.setChecked(True)
            self.vertices_checkbox.setEnabled(False)
        else:
            # Для матрицы можно выбирать
            self.vertices_checkbox.setEnabled(True)

    def add_algorithm(self):
        # Проверка, что выбран один из типов графа на всякий случай
        if not self.adjacency_matrix_radio.isChecked() and not self.adjacency_list_radio.isChecked():
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                                          "Пожалуйста, выберите тип графа (матрица или список смежности).")
            return

        # Сохранение данных о выбранном алгоритме
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Python files (*.py)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            os.makedirs(ALGORITHMS_DIR, exist_ok=True)
            filename = os.path.basename(selected_file)
            destination = os.path.join(ALGORITHMS_DIR, filename)

            if os.path.exists(destination):
                QtWidgets.QMessageBox.warning(self, "Файл уже существует", "Алгоритм с таким именем уже существует.")
                return

            shutil.copyfile(selected_file, destination)

            # Логика добавления алгоритма
            self.config_data = {
                "vertices": self.vertices_checkbox.isChecked(),
                "adjacency_type": "matrix" if self.adjacency_matrix_radio.isChecked() else "list",
                "start_point": self.start_point_checkbox.isChecked(),
                "end_point": self.end_point_checkbox.isChecked(),
                "file": destination
            }

            self.accept()
            return

    def generate_template_text(self):
        parts = []

        if self.vertices_checkbox.isChecked():
            parts.append("    num_vertices = int(input())  # количество вершин")

        if self.adjacency_matrix_radio.isChecked():
            if self.vertices_checkbox.isChecked():
                parts.append(
                    "    adjacency_matrix = [list(map(int, input().split())) for _ in range(num_vertices)]  # матрица смежности")
            else:
                parts.append("    first_line = list(map(int, input().split()))")
                parts.append("    num_vertices = len(first_line)")
                parts.append("    adjacency_matrix = [first_line] # матрица смежности")
                parts.append("    for _ in range(num_vertices - 1):")
                parts.append("        adjacency_matrix.append(list(map(int, input().split())))")
        elif self.adjacency_list_radio.isChecked():
            parts.append("    # Введите список смежности в формате: \"вершина: соседи через пробел\"")
            parts.append("    adjacency_list = {}")
            parts.append("    for _ in range(num_vertices):")
            parts.append("        parts = input().split(':')")
            parts.append("        key = int(parts[0])")
            parts.append("        neighbors = list(map(int, parts[1].strip().split()))")
            parts.append("        adjacency_list[key] = neighbors")

        if self.start_point_checkbox.isChecked():
            parts.append("    start = int(input())  # начальная вершина")

        if self.end_point_checkbox.isChecked():
            parts.append("    end = int(input())  # конечная вершина")

        body = "\n".join(parts) if parts else "    pass  # нет параметров"
        template = f"""def run_algorithm():\n{body}\n\n    # Для вывода как вершина используйте перед числом знак $\n    # Например $0 - это переведёт номер в вершину приложения\n    # Ваш алгоритм здесь\n\nrun_algorithm()\n"""
        return template

    def show_template_dialog(self):
        code = self.generate_template_text()
        dialog = TemplateDialog(code, self)
        dialog.exec()


# Класс настроек
class Settings(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Настройки")
        self.setFixedSize(300, 150)

        self.setStyleSheet("""
                    background-color: #f0f0f0;
                    font-family: 'Arial', sans-serif;
                """)

        layout = QtWidgets.QVBoxLayout(self)

        self.checkbox_weighted = QtWidgets.QCheckBox("Взвешенный граф", self)
        self.checkbox_weighted.setChecked(False)
        self.checkbox_weighted.setStyleSheet("""
                   font-size: 14px;
                   color: #333333;
                   padding: 10px;
                   margin: 5px;
               """)
        self.checkbox_weighted.stateChanged.connect(self.toggle_weight)
        layout.addWidget(self.checkbox_weighted)

    def toggle_weight(self):
        """Обработчик для переключения флага взвешенного графа"""
        if self.checkbox_weighted.isChecked():
            wnd.graph_area.weighted_graph = True
            wnd.graph_area.toggle_weighted_graph()
        else:
            wnd.graph_area.weighted_graph = False
            wnd.graph_area.toggle_weighted_graph()


# Ставим QDialog чтобы было модальное окно, оно делает невозможно взаимодействие с другими окнами пока пользователь не зароет это
class About_program(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)  # Устанавливаем модальность окна в ручную (необязательно)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("О программе")
        self.setFixedSize(400, 300)

        self.setStyleSheet("background-color: white;")

        layout = QtWidgets.QVBoxLayout()

        # Создание QTextEdit для отображения текста
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setReadOnly(True)
        self.load_description()  # Загружаем текст из файла

        close_button = QtWidgets.QPushButton("Закрыть")
        close_button.clicked.connect(self.close)

        layout.addWidget(self.text_edit)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_description(self):
        """Функция для отображения текста"""
        try:
            with open(resource_path("About_program.txt"), "r", encoding="utf-8") as file:
                description = file.read()
                self.text_edit.setPlainText(description)
        except FileNotFoundError:
            self.text_edit.setPlainText("Файл описания не найден.")
        except Exception as e:
            self.text_edit.setPlainText(f"Ошибка при загрузке описания: {str(e)}")


# Переписанный QGraphicsScene для правильного выбора вершины при наложении
class CustomGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        """Переопределяем метод mousePressEvent для выбора только верхнего элемента."""
        pos = event.scenePos()
        items = self.items(pos, order=QtCore.Qt.SortOrder.DescendingOrder)  # Сортируем элементы сверху вниз

        # Отключаем выбор для всех элементов
        for item in items:
            item.setSelected(False)

        # Выбираем только верхний элемент
        if items:
            top_item = items[0]
            if isinstance(top_item, (QGraphicsEllipseItem, QGraphicsLineItem)):
                top_item.setSelected(True)

        # Передаем событие дальше
        super().mousePressEvent(event)


# Класс сортированного списка точек
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


# Собственный класс SignalEmitter для обработки некоторых событий
class SignalEmitter(QtCore.QObject):
    """Класс для работы с сигналами."""
    positionChanged = QtCore.pyqtSignal()  # Сигнал для изменения позиции

    def __init__(self, parent=None):
        super().__init__(parent)


# Класс "вершин"
class LabeledEllipse(QGraphicsEllipseItem):
    def __init__(self, x, y, size, color, label, parent=None):
        super().__init__(-size / 2, -size / 2, size, size, parent)  # Инициализируем QGraphicsEllipseItem
        self.setPos(x, y)
        self.color = color

        self.setZValue(1)

        # Добавляем объект для сигналов
        self.signals = SignalEmitter()

        self.setBrush(QtGui.QBrush(color))
        self.setPen(QtGui.QPen(QtGui.QColor("#000000"), 0))  # Убираем обводку

        # Создаём метку с номером
        self.label = QtWidgets.QGraphicsTextItem(str(label), self)
        self.label.setDefaultTextColor(QtGui.QColor("#000000"))  # Устанавливаем цвет по умолчанию
        self.update_text_font(size)
        self.update_text_position(size)
        self.update_text_color()

        self.label.setZValue(1000)

        # Устанавливаем флаги для перемещения и выделения
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)

        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def config_menu(self, pos):
        """Контекстное меню для вершины."""
        menu = QtWidgets.QMenu()

        change_color_action = menu.addAction("Изменить цвет")
        change_color_action.triggered.connect(self.change_color)

        change_size_action = menu.addAction("Изменить размер")
        change_size_action.triggered.connect(self.change_size)

        menu.exec(pos)

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
        self.update_text_position(self.rect().width())
        self.update_text_color()

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


# Класс "рёбер"
class GraphEdge(QGraphicsLineItem):
    def __init__(self, start, end, color, weight=1, parent=None):
        super().__init__(parent)
        self.start_v = start
        self.end_v = end
        self.weight = weight

        self.setZValue(0)

        self.setPen(QtGui.QPen(QtGui.QColor(color), 2))

        # Настройка текста
        self.label = QtWidgets.QGraphicsTextItem(self)
        self.label.setDefaultTextColor(QtGui.QColor("#000000"))
        self.label.setPlainText(str(weight))

        self.label.setZValue(1000)

        # Используем моноширинный шрифт для стабильного размера
        font = QtGui.QFont("Monospace", 10)
        self.label.setFont(font)

        # Выравниваем текст по центру, делаем его поворот относительно центра
        self.label.setTransformOriginPoint(self.label.boundingRect().center())

        self.update_position()

        self.start_v.signals.positionChanged.connect(self.update_position)
        self.end_v.signals.positionChanged.connect(self.update_position)

        self.update_weight_display()

    def update_weight_display(self):
        """Обновить отображение веса в зависимости от флага weighted_graph"""
        if wnd.graph_area.weighted_graph:
            self.label.setVisible(True)
        else:
            self.label.setVisible(False)

    def config_menu(self, pos):
        """Контекстное меню для ребра."""
        menu = QtWidgets.QMenu()

        change_color_action = menu.addAction("Изменить цвет")
        change_color_action.triggered.connect(self.change_color)

        change_weight_action = menu.addAction("Изменить вес")
        change_weight_action.triggered.connect(self.change_weight)

        menu.exec(pos)

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
        """Обновить положение линии и текста с учётом читаемости"""
        line = QtCore.QLineF(self.start_v.scenePos(), self.end_v.scenePos())
        self.setLine(line)

        # Центр линии и вектор направления
        center = line.pointAt(0.5)
        direction = line.p2() - line.p1()

        # Рассчитываем базовый угол поворота
        angle = line.angle()

        # Определяем главное направление линии
        is_horizontal = abs(direction.x()) > abs(direction.y())

        # Корректируем угол для читаемости (верхногами)
        if direction.x() < 0:
            angle += 180 if is_horizontal else 0
        if direction.y() > 0 and not is_horizontal:
            angle += 180

        # Ограничиваем угол в диапазоне [0, 360)
        angle %= 360

        # Автоматическая коррекция для четвертей
        if 90 < angle < 270:
            angle = (angle + 180) % 360  # Переворачиваем на 180 градусов

        self.label.setRotation(-angle)

        # Рассчитываем смещение относительно нормали
        offset = 12
        normal = line.normalVector().unitVector()
        offset_vector = QtCore.QPointF(
            normal.dx() * offset,
            normal.dy() * offset
        )

        # Корректируем направление смещения
        if angle > 90 and angle < 270:
            offset_vector *= -1

        # Позиционирование текста
        text_rect = self.label.boundingRect()
        self.label.setTransformOriginPoint(text_rect.center())
        self.label.setPos(
            center
            + offset_vector
            - QtCore.QPointF(
                text_rect.width() / 2,
                text_rect.height() / 2
            )
        )

    def set_weight(self, weight):
        """Изменить вес ребра"""
        self.weight = weight
        links = wnd.graph_area.points[self.end_v]
        for pt, ed in links:
            if self.start_v == pt:
                ed.weight = weight
        self.label.setPlainText(str(weight))
        self.update_position()
        self.update_weight_display()


class GraphArea(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Создаем сцену с очень большим sceneRect
        # Создаем кастомную сцену
        self.scene = CustomGraphicsScene(self)
        infinite_size = 10 ** 6  # Задаем большой размер
        self.scene.setSceneRect(-infinite_size, -infinite_size, 2 * infinite_size, 2 * infinite_size)
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Убираем ползунки для рабочей области
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Начальные параметры для точек (вершин графа)
        self.point_size = 10
        self.point_color = QtGui.QColor("#000000")

        # Список смежности (словарь) для хранения вершин и их порядковых номеров
        self.points = SortedPointDict()

        self.start_point = None

        # шаг увеличения
        self.scale_factor = 1.1
        # Стандартное увеличени
        self.scale(2, 2)

        self.weighted_graph = False

        # Режимы взаимодействия
        self.move_mode = True
        self.paint_ellipse_mode = False
        self.paint_line_mode = False
        self.delete_mode = False
        self.choise_mode = False
        self.tools_mode = False

    def toggle_weighted_graph(self):
        """Переключить отображение веса рёбер"""
        for item in self.scene.items():
            if isinstance(item, GraphEdge):
                item.update_weight_display()

    def wheelEvent(self, event):
        """Обработка колесика мыши для масштабирования сцены."""
        if event.angleDelta().y() > 0:
            self.scale(self.scale_factor, self.scale_factor)  # +размер
        else:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)  # -размер

    def contextMenuEvent(self, event):
        """Handle context menu events in the graph area."""
        pos = self.mapToScene(event.pos())  # Преобразуем координаты в систему координат сцены
        items = self.scene.items(pos)
        activ_item = None
        for x in items:
            if isinstance(x, LabeledEllipse):
                activ_item = x
        else:
            threshold = 4  # Пороговое расстояние для удаления линии
            # Проверка линий на близость к месту клика
            for item in self.scene.items():
                if isinstance(item, QGraphicsLineItem):
                    line = item.line()
                    dist = self._distance_from_point_to_line(pos, line)
                    if dist <= threshold:
                        activ_item = item

        if activ_item is not None:
            # Преобразуем координаты в глобальные
            global_pos = self.mapToGlobal(event.pos())
            activ_item.config_menu(global_pos)  # Передаем глобальные координаты
        else:
            super().contextMenuEvent(event)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для добавления, удаления или выбора точек."""
        pos = self.mapToScene(event.position().toPoint())
        but = event.button()

        if but == QtCore.Qt.MouseButton.LeftButton:
            fl = 1

            # Получаем все элементы под курсором, отсортированные по z-значению (сверху вниз)
            items = sorted(self.scene.items(pos), key=lambda x: x.zValue(), reverse=True)

            # Отключаем выбор для всех элементов, кроме верхнего
            for item in items:
                if isinstance(item, QGraphicsEllipseItem) or isinstance(item, QGraphicsLineItem):
                    item.setSelected(False)

            # Выбираем только верхний элемент
            if items:
                top_item = items[0]
                if isinstance(top_item, QGraphicsEllipseItem) or isinstance(top_item, QGraphicsLineItem):
                    top_item.setSelected(True)

            if self.choise_mode:
                for item in items:
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
                for item in items:
                    if isinstance(item, QGraphicsEllipseItem) and item != self.start_point:
                        if self.can_add_line(self.start_point, item):
                            self.add_line(self.start_point, item)
                            break

            elif self.paint_line_mode and self.start_point is not None:
                fl = 0
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
                self.add_point(pos)

            elif self.delete_mode:
                self.delete_obj(pos)

            elif self.move_mode and not (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                # Логика перемещения
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
        r_edge = GraphEdge(edge.end_v, edge.start_v, 1, edge.weight)
        return r_edge

    def add_line(self, start_vertex, end_vertex, weight=1):
        """Добавление нового ребра между двумя вершинами."""
        try:
            edge = GraphEdge(start_vertex, end_vertex, 0, weight=weight)
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

        for item in self.points.sorted_keys:
            # Получаем центр существующего элипса в координатах сцены
            existing_center = item.mapToScene(item.rect().center())

            # Вычисляем расстояние между центрами
            distance = (
                    new_center - existing_center).manhattanLength()  # создаёт вектор разности между центрами и возвращает сумму абсолютных разностей по осям, или же Манхэттенское расстояние (|х2 - х1|+|у2-у1|)

            # Проверка что расстояние больше суммы радиусов и минимального расстояния
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


# Класс кнопки с svg-картинкой
class SvgButton(QtWidgets.QPushButton):
    def __init__(self, icon_path):
        super().__init__()
        self.setIcon(QtGui.QIcon(icon_path))


# Основной класс приложения
class Grafs(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graf++")
        self.resize(int(monitor_width * 0.6), int(monitor_height * 0.6))
        self.color = "#000000"
        self.graph_area = None
        self.wnd_about = None
        self.wnd_settings = Settings(self)

        self.custom_algorithm_buttons = {}  # key: filename (без .py), value: (QPushButton, alg_data)

        self.setupUi()

        self.load_custom_algorithms()

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

        # Кнопка рисования кругов
        self.paint_ellipse_button = SvgButton(resource_path("svg_folder/circle-solid.svg"))
        self.paint_ellipse_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_ellipse_button.setCheckable(True)
        self.paint_ellipse_button.clicked.connect(self.switch_paint_ellipse_mode)
        self.paint_ellipse_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_ellipse_button)

        # Кнопка рисования линий
        self.paint_line_button = SvgButton(resource_path("svg_folder/line.svg"))
        self.paint_line_button.setFixedWidth(int(monitor_width * 0.03))
        self.paint_line_button.setCheckable(True)
        self.paint_line_button.clicked.connect(self.switch_paint_line_mode)
        self.paint_line_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.paint_line_button)

        # Кнопка удаления (корзинка)
        self.erase_button = SvgButton(resource_path("svg_folder/trash-alt-solid.svg"))
        self.erase_button.setFixedWidth(int(monitor_width * 0.03))
        self.erase_button.setCheckable(True)
        self.erase_button.clicked.connect(self.switch_erase_mode)
        self.erase_button.clicked.connect(self.switch_move_mode)
        self.tool_panel_layout.addWidget(self.erase_button)

        # Выбор пользовательского цвета
        self.custom_color_button = SvgButton(resource_path("svg_folder/palette-solid.svg"))
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

        # Добавляем панель инструментов в layout
        vertical_layout.addWidget(self.tool_panel)

        # Создание боковой панели
        self.side_panel = QtWidgets.QFrame()
        self.side_panel.setStyleSheet("background-color: white;")
        self.side_panel_size = int(self.width() * 0.15)
        self.side_panel.setFixedWidth(self.side_panel_size)  # Ширина боковой панели

        # Основной layout боковой панели
        side_layout = QtWidgets.QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        # Верхняя часть боковой панели: фиксированный блок с кнопками + прокручиваемая часть для динамических элементов
        top_container = QtWidgets.QWidget()
        top_container_layout = QtWidgets.QVBoxLayout(top_container)
        top_container_layout.setContentsMargins(0, 0, 0, 0)
        top_container_layout.setSpacing(0)

        # Фиксированная панель с кнопками (всегда видна)
        fixed_buttons_panel = QtWidgets.QWidget()
        fixed_buttons_panel.setStyleSheet(
            "background-color: white;"
        )
        fixed_buttons_layout = QtWidgets.QHBoxLayout(fixed_buttons_panel)
        fixed_buttons_layout.setContentsMargins(5, 5, 5, 5)
        fixed_buttons_layout.setSpacing(10)

        self.add_algorithm_button = QtWidgets.QPushButton("➕ Добавить")
        self.remove_algorithm_button = QtWidgets.QPushButton("🗑 Удалить")

        self.add_algorithm_button.clicked.connect(self.add_algorithm)
        self.remove_algorithm_button.clicked.connect(self.remove_algorithm)

        buttons_style = (
            "QPushButton {"
            f"background-color: #EAEAEA; border: 1px solid #DCDCDC; border-radius: {self.side_panel_size * 0.05}px;"
            f"padding: {int(self.height() * 0.01)}px {int(self.side_panel_size * 0.005)}px; font-size: {int(self.side_panel_size * 0.068)}px;"
            "}"
            "QPushButton:pressed {"
            "background-color: #0056b3; border-color: #0047a1;"
            "}"
        )
        self.add_algorithm_button.setStyleSheet(buttons_style)
        self.remove_algorithm_button.setStyleSheet(buttons_style)

        fixed_buttons_layout.addWidget(self.add_algorithm_button)
        fixed_buttons_layout.addWidget(self.remove_algorithm_button)

        dynamic_container = QtWidgets.QWidget()
        # layout для динамического добавления кнопок и других виджетов
        self.top_side_layout = QtWidgets.QVBoxLayout(dynamic_container)
        self.top_side_layout.setContentsMargins(5, 5, 5, 5)
        self.top_side_layout.setSpacing(5)

        # Прокручиваемая область, в которой размещен dynamic_container
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(dynamic_container)
        scroll_area.setStyleSheet("background-color: white; border: none;")
        scroll_area.setStyleSheet(buttons_style)

        top_container_layout.addWidget(fixed_buttons_panel)
        top_container_layout.addWidget(scroll_area)

        # Далее создаем нижнюю часть боковой панели
        bottom_side_panel = QtWidgets.QWidget()
        bottom_side_panel.setStyleSheet("""
            QWidget {
                background-color: rgb(200, 200, 250); /* Фон подсказок */
            }
            QLabel {
                color: black;
            }
            .error {
                color: red;
            }
        """)
        bottom_side_layout = QtWidgets.QVBoxLayout(bottom_side_panel)
        bottom_side_layout.setContentsMargins(5, 5, 5, 5)

        # Текст с подсказками
        self.hints_label = QtWidgets.QLabel(self)
        self.hints_label.setWordWrap(True)
        bottom_side_layout.addWidget(self.hints_label)
        bottom_side_layout.addStretch(1)

        # Создаем прокручиваемую область для подсказок
        bottom_scroll_area = QtWidgets.QScrollArea()
        bottom_scroll_area.setWidgetResizable(True)
        bottom_scroll_area.setWidget(bottom_side_panel)
        bottom_scroll_area.setStyleSheet("border: none;")

        # Используем QSplitter для организации верхней и нижней частей боковой панели
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        splitter.addWidget(top_container)
        splitter.addWidget(bottom_scroll_area)
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])

        # Добавляем splitter в основной layout боковой панели
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

    def load_custom_algorithms(self):
        config_path = os.path.join(ALGORITHMS_DIR, "algorithms_configurations")

        if not os.path.exists(config_path):
            return

        with open(config_path, 'r') as json_file:
            try:
                all_configs = json.load(json_file)
            except json.JSONDecodeError:
                all_configs = {}

        for algorithm_name, config in all_configs.items():
            self._add_algorithm_button(algorithm_name, config, save_to_file=False)

    def _add_algorithm_button(self, algorithm_name, algorithm_data, save_to_file=True):
        if algorithm_name in self.custom_algorithm_buttons:
            return  # уже есть

        button = QtWidgets.QPushButton(algorithm_name)
        button.clicked.connect(self.alghoritms)
        self.custom_algorithm_buttons[algorithm_name] = (button, algorithm_data)
        self.top_side_layout.addWidget(button)

        if save_to_file:
            config_path = os.path.join(ALGORITHMS_DIR, "algorithms_configurations")
            if os.path.exists(config_path):
                with open(config_path, 'r') as json_file:
                    try:
                        all_configs = json.load(json_file)
                    except json.JSONDecodeError:
                        all_configs = {}
            else:
                all_configs = {}

            all_configs[algorithm_name] = algorithm_data

            with open(config_path, 'w') as json_file:
                json.dump(all_configs, json_file, indent=4)

    def add_algorithm(self):
        dialog = AddAlgorithmDialog(self)
        if dialog.exec():
            algorithm_data = dialog.config_data

            selected_file = algorithm_data["file"]

            if algorithm_data:
                name = os.path.splitext(os.path.basename(selected_file))[0]
                self._add_algorithm_button(name, algorithm_data)

    def _delete_algorithm_from_config(self, json_path, algorithm_name):
        with open(json_path, "r", encoding="utf-8") as f1:
            data = json.load(f1)

        if algorithm_name in data:
            del data[algorithm_name]
            with open(json_path, "w", encoding="utf-8") as f2:
                json.dump(data, f2, indent=4, ensure_ascii=False)
            return True
        return False

    def remove_algorithm(self):
        if not os.path.exists(ALGORITHMS_DIR):
            QtWidgets.QMessageBox.information(self, "Папка с алгоритмами", "Папка с алгоритмами пуста.")
            return

        files = [f for f in os.listdir(ALGORITHMS_DIR) if f.endswith('.py')]
        if not files:
            QtWidgets.QMessageBox.information(self, "Нет алгоритмов", "Нет доступных алгоритмов для удаления.")
            return

        item, ok = QtWidgets.QInputDialog.getItem(self, "Удалить алгоритм", "Выберите алгоритм:", files, editable=False)
        if ok and item:
            confirm = ConfirmationDialog(f"you want to delete '{item}'", self)
            if confirm.exec():
                try:
                    os.remove(os.path.join(ALGORITHMS_DIR, item))
                    name = os.path.splitext(item)[0]
                    if name in self.custom_algorithm_buttons:
                        btn = self.custom_algorithm_buttons.pop(name)[0]
                        self.top_side_layout.removeWidget(btn)
                        config_path = os.path.join(ALGORITHMS_DIR, "algorithms_configurations")
                        self._delete_algorithm_from_config(config_path, name)
                        btn.deleteLater()
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {e}")

    def _create_adjacency_matrix(self, graph_points):
        # Присваиваем каждой вершине уникальный индекс
        vertex_to_index = {v: i for i, v in enumerate(graph_points)}

        # Создаем отображение от индекса к вершине
        index_to_vertex = {i: v for i, v in enumerate(graph_points)}

        # Создаем пустую матрицу смежности
        num_vertices = len(vertex_to_index)
        adjacency_matrix = [[0] * num_vertices for _ in range(num_vertices)]

        # Заполнение матрицы смежности
        for vertex, edges in graph_points.items():
            u = vertex_to_index[vertex]
            for pt, edge in edges:
                v = vertex_to_index[pt]
                adjacency_matrix[u][v] = edge.weight

        return adjacency_matrix, vertex_to_index, index_to_vertex

    def _create_adjecency_list(self, graph_points):
        # Присваиваем каждой вершине уникальный индекс
        vertex_to_index = {v: i for i, v in enumerate(graph_points)}

        # Создаем отображение от индекса к вершине
        index_to_vertex = {i: v for i, v in enumerate(graph_points)}

        # Создаём словарь для списка смежности
        dic = {
            i: [vertex_to_index[x[0]] for x in graph_points[index_to_vertex[i]]]
            for i in range(len(vertex_to_index))
        }

        return dic, vertex_to_index, index_to_vertex

    def choise_start(self, text="Выберите вершину с которой начнётся обход"):
        self.graph_area.start_point = None
        self.graph_area.scene.clearSelection()
        self.set_hints_text(f"{text}")
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
        sender_but = self.sender()
        text = sender_but.text()
        sender_but.repaint()
        if len(self.graph_area.points):

            algorithm_data = self.custom_algorithm_buttons[f"{self.sender().text()}"][1]

            # Данные, которые нужно передать в алгоритм
            data = ""

            if algorithm_data["vertices"]:
                data += f"{len(self.graph_area.points)}\n"
            if algorithm_data["adjacency_type"] == "matrix":
                input_data, vertex_to_index, index_to_vertex = self._create_adjacency_matrix(self.graph_area.points)
                for i in input_data:
                    temp_str = [str(x) for x in i]
                    data += f"{' '.join(temp_str)}\n"
            else:
                input_data, vertex_to_index, index_to_vertex = self._create_adjecency_list(self.graph_area.points)
                for i in input_data.keys():
                    data += f"{i}: {input_data[i]}"

            if algorithm_data["start_point"]:
                self.choise_start()
                alg_start = self.graph_area.start_point
                data += f"{vertex_to_index[alg_start]}\n"
            if algorithm_data["end_point"]:
                self.choise_start("Выберете конечную вершину")
                alg_end = self.graph_area.start_point
                data += f"{vertex_to_index[alg_end]}\n"

            # Запускаем алгоритм, передавая данные через stdin и захватываем stdout
            process = subprocess.Popen(
                ['python', f'algorithms/{text}.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Передаем данные в процесс и получаем вывод
            output, errors = process.communicate(input=data)

            # Замена $индекса на имя вершины
            for index, vertex in index_to_vertex.items():
                output = output.replace(f"${index}", vertex.label.toPlainText())

            # Выводим результаты
            self.set_hints_text(f"Вывод алгоритма:\n{output}")
            if errors:
                self.set_error_hint(f"Ошибки:\n{errors}")
        else:
            text = self.get_plain_hints_text()
            self.set_hints_text("Графа не существует, применение алгоритмов невозможно.")
            QtCore.QTimer.singleShot(3000, lambda: self.set_hints_text(text))
        self.graph_area.choise_mode = False
        self.switch_move_mode(True)

    def new_graf(self):
        """Метод для создания нового графа."""
        dialog = ConfirmationDialog("you want to clear the graph", self)
        if dialog.exec():
            self.graph_area.reset_graph()

    def tansform_graph(self, points):
        # трансформирование точек
        t_points = [
            {
                "id": pt.label.toPlainText(),
                "pos": {"x": pt.pos().x(), "y": pt.pos().y()},
                "link": [(x[0].label.toPlainText(), x[1].weight) for x in points[pt]],
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
                for link_point, weight in point["link"]:
                    self.graph_area.find_and_add_line(point["id"], link_point, weight)

    def settings(self):
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

    def get_plain_hints_text(self):
        """Метод для получения текста из области с подсказками без HTML-разметки."""
        doc = QtGui.QTextDocument()
        doc.setHtml(self.hints_label.text())
        return doc.toPlainText()

    def set_hints_text(self, text):
        """Метод для установки текста в область с подсказками."""
        # Заменяем \n на <br> для переноса строк
        text = text.replace("\n", "<br>")
        html_text = f"<p><span style='color: black'>{text}</span></p>"
        self.hints_label.setText(html_text)

    def add_hints_text(self, text, splitter=None):
        """Метод для добавления текста в область с подсказками."""
        if splitter is None:
            self.hints_label.setText(self.hints_label.text()[:-11] + text + "</span></p>")
        elif splitter == "\n":
            # Заменяем \n на <br> и добавляем новый блок
            text = text.replace("\n", "<br>")
            html_text = f"<p><span style='color: black'>{text}</span></p>"
            self.hints_label.setText(self.hints_label.text() + html_text)

    def set_error_hint(self, error_message):
        """Метод для добавления ошибки в область с подсказками."""
        # Заменяем \n на <br> в сообщении об ошибке
        error_message = error_message.replace("\n", "<br>")
        html_text = f"<p><span class='error'>{error_message}</span></p>"
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
        text = """Вы в режиме рисования вершин, нажмите на сцену, чтобы поставить вершину.
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
        text = """Вы в режиме рисования рёбер, выделите одну вершину нажатием, а затем нажмите на другую вершину.
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
        text = """Вы в режиме удаления, нажмите на объект, чтобы удалить его.
                (На вершину или ближе к середине ребра).
            """
        self.set_hints_text(text)

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
                text = """Вы в режиме передвижения и выбора.
                        Зажав Ctrl вы сможете выбрать сразу несколько вершин.
                    """
                self.set_hints_text(text)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path('icon.ico')))
    wnd = Grafs()
    wnd.show()
    sys.exit(app.exec())

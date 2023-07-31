import sys
import os
import io
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
import ga_tsp

sys.path.append(os.path.abspath("."))
default_dir = "./src/"


class MainWindow(QWidget):
    tsp = None
    running = False
    last_best_distance = -1
    magic_button_case = "start"

    def __init__(self):
        super().__init__()
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_draw)

    def init_ui(self):
        self.setMaximumSize(1200, 800)
        self.setMinimumSize(1200, 800)
        self.setWindowTitle("Route Finder")

        self.webView = QWebEngineView(self)
        self.webView.setGeometry(230, 0, 1000, 800)

        self.threadpool = QThreadPool()

        # Font for Group Titles
        font = QFont()
        font.setKerning(True)
        font.ExtraBold = True

        # SETTINGS #
        # region
        self.gb_settings = QGroupBox(self)
        self.gb_settings.setTitle("Settings")
        self.gb_settings.setFont(font)
        self.gb_settings.setGeometry(QRect(5, 0, 220, 350))

        self.btn_import = QPushButton(self.gb_settings)
        self.btn_import.move(0, 30)
        self.btn_import.resize(220, 30)
        self.btn_import.setText("Import Data")
        self.btn_import.clicked.connect(self.import_data)

        self.lbl_locations = QLabel(self.gb_settings)
        self.lbl_locations.move(5, 60)
        self.lbl_locations.setText("Locations:")

        self.lbl_locations_value = QLabel(self.gb_settings)
        self.lbl_locations_value.move(153, 60)
        self.lbl_locations_value.setFixedWidth(60)
        self.lbl_locations_value.setText("None")
        self.lbl_locations_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lbl_maxgeneration = QLabel(self.gb_settings)
        self.lbl_maxgeneration.move(5, 90)
        self.lbl_maxgeneration.setText("Max Generation")

        self.txt_maxgeneration_value = QLineEdit(self.gb_settings)
        self.txt_maxgeneration_value.setGeometry(175, 85, 40, 25)
        self.txt_maxgeneration_value.setText("")
        self.txt_maxgeneration_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_maxgeneration_value.setEnabled(False)

        self.lbl_pop_size = QLabel(self.gb_settings)
        self.lbl_pop_size.move(5, 125)
        self.lbl_pop_size.setText("Population Size")

        self.txt_pop_size_value = QLineEdit(self.gb_settings)
        self.txt_pop_size_value.setGeometry(175, 120, 40, 25)
        self.txt_pop_size_value.setText("")
        self.txt_pop_size_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_pop_size_value.setEnabled(False)

        self.lbl_childrensize = QLabel(self.gb_settings)
        self.lbl_childrensize.move(5, 160)
        self.lbl_childrensize.setText("Number of Children")

        self.txt_childrensize_value = QLineEdit(self.gb_settings)
        self.txt_childrensize_value.setGeometry(175, 155, 40, 25)
        self.txt_childrensize_value.setText("")
        self.txt_childrensize_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_childrensize_value.setEnabled(False)

        self.lbl_mutationpercent = QLabel(self.gb_settings)
        self.lbl_mutationpercent.move(5, 195)
        self.lbl_mutationpercent.setText("Mutation Probability (%)")

        self.txt_mutationpercent_value = QLineEdit(self.gb_settings)
        self.txt_mutationpercent_value.setGeometry(175, 190, 40, 25)
        self.txt_mutationpercent_value.setText("")
        self.txt_mutationpercent_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_mutationpercent_value.setEnabled(False)

        self.btn_savesettings = QPushButton(self.gb_settings)
        self.btn_savesettings.move(0, 225)
        self.btn_savesettings.resize(220, 60)
        self.btn_savesettings.setText("Save Setup")
        self.btn_savesettings.clicked.connect(self.save_settings)
        self.btn_savesettings.setEnabled(False)

        self.btn_start = QPushButton(self.gb_settings)
        self.btn_start.move(0, 285)
        self.btn_start.resize(220, 60)
        self.btn_start.setText("Start/Stop")
        self.btn_start.clicked.connect(self.magic_button_click)
        self.btn_start.setEnabled(False)
        # endregion

        # INFORMATION #
        # region
        self.gb_info = QGroupBox(self)
        self.gb_info.setTitle("Information")
        self.gb_info.setFont(font)
        self.gb_info.setGeometry(QRect(5, 360, 220, 160))

        self.lbl_generation = QLabel(self.gb_info)
        self.lbl_generation.move(5, 30)
        self.lbl_generation.setText("Generation:")

        self.lbl_generation_value = QLabel(self.gb_info)
        self.lbl_generation_value.move(153, 30)
        self.lbl_generation_value.setFixedWidth(60)
        self.lbl_generation_value.setText("None")
        self.lbl_generation_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lbl_distance = QLabel(self.gb_info)
        self.lbl_distance.move(5, 60)
        self.lbl_distance.setText("Distance:")

        self.lbl_distance_value = QLabel(self.gb_info)
        self.lbl_distance_value.move(153, 60)
        self.lbl_distance_value.setFixedWidth(60)
        self.lbl_distance_value.setText("None")
        self.lbl_distance_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_export = QPushButton(self.gb_info)
        self.btn_export.move(0, 90)
        self.btn_export.resize(220, 60)
        self.btn_export.setText("Save Route")
        self.btn_export.clicked.connect(self.save_results)
        self.btn_export.setEnabled(False)
        # endregion

        self.center()
        self.show()

    def import_data(self):
        options = QFileDialog.Option(QFileDialog.Option.DontUseNativeDialog)
        self.fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Import Data File",
            default_dir,
            "Excel Files (*.xlsx)",
            options=options,
        )

        worker = Worker(self.import_data_thread)
        worker.signals.finished.connect(self.draw_locations)
        self.threadpool.start(worker)

    def import_data_thread(self):
        try:
            self.tsp = ga_tsp.GA_TSP(
                data_path=self.fileName,
            )
            self.lbl_locations_value.setText(str(len(self.tsp.data.dataset)))

            # Activate parameter controls
            self.txt_maxgeneration_value.setEnabled(True)
            self.txt_pop_size_value.setEnabled(True)
            self.txt_childrensize_value.setEnabled(True)
            self.txt_mutationpercent_value.setEnabled(True)
            self.btn_savesettings.setEnabled(True)

            self.txt_maxgeneration_value.setText("500")
            self.txt_pop_size_value.setText("50")
            self.txt_childrensize_value.setText("10")
            self.txt_mutationpercent_value.setText("0.01")

            self.btn_start.setEnabled(False)
            self.btn_export.setEnabled(False)

            self.last_best_distance = -1
            self.lbl_distance_value.setText("None")
            self.lbl_generation_value.setText("None")

        except Exception as ex:
            pass

    def save_settings(self):
        try:
            maxgeneration = int(self.txt_maxgeneration_value.text())
            pop_size = int(self.txt_pop_size_value.text())
            childrensize = int(self.txt_childrensize_value.text())
            mutationpercent = float(self.txt_mutationpercent_value.text())

            self.tsp.set_problem(
                pop_size=pop_size,
                number_of_children=childrensize,
                max_generation=maxgeneration,
                mutation_percent=mutationpercent,
            )

            self.tsp.max_generation = maxgeneration
            self.tsp.population.pop_size = pop_size
            self.tsp.population.number_of_children = childrensize
            self.tsp.mutation_percent = mutationpercent

            self.btn_start.setEnabled(True)

            # Deactivate parameter controls
            self.txt_maxgeneration_value.setEnabled(False)
            self.txt_pop_size_value.setEnabled(False)
            self.txt_childrensize_value.setEnabled(False)
            self.txt_mutationpercent_value.setEnabled(False)
            self.btn_savesettings.setEnabled(False)

            self.lbl_generation_value.setText("None")
            self.lbl_distance_value.setText("None")
            self.btn_export.setEnabled(True)

        except Exception as ex:
            pass

    def magic_button_click(self):
        if self.magic_button_case == "start":
            self.start_ga()
            self.magic_button_case = "pause"
        elif self.magic_button_case == "pause":
            self.pause_ga()
            self.magic_button_case = "start"
        else:
            pass

    def start_ga(self):
        self.running = True
        self.refresh_drawing = True

        worker = Worker(self.start_ga_thread)
        self.threadpool.start(worker)

        self.timer.start(1000)

    def start_ga_thread(self):
        while self.running == True and (
            self.tsp.population.current_generation < self.tsp.max_generation
        ):
            improved_flag = self.tsp.population.iterate_generation()

            # improved = True
            if improved_flag == True:
                self.lbl_distance_value.setText(
                    str("%.2f" % self.tsp.population.best_distance)
                )

            self.lbl_generation_value.setText(
                str(self.tsp.population.current_generation)
            )

    def pause_ga(self):
        # Pass the function to execute
        worker = Worker(self.pause_ga_thread)
        self.threadpool.start(worker)

    def pause_ga_thread(self):
        self.running = False
        self.refresh_drawing = False

    def draw_locations(self):
        m = self.tsp.draw_locations()
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())

    def draw_route(self):
        m = self.tsp.draw_route(self.tsp.population.best_route)
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())

    def auto_draw(self):
        try:
            if (self.running == True) and (
                self.tsp.population.current_generation < self.tsp.max_generation
            ):
                if (
                    self.last_best_distance == -1
                    or self.last_best_distance > self.tsp.population.best_distance
                ):
                    self.draw_route()
                    self.last_best_distance = self.tsp.population.best_distance
            elif self.last_best_distance > self.tsp.population.best_distance:
                self.draw_route()
                self.last_best_distance = self.tsp.population.best_distance

            if (self.running == False) or (
                self.tsp.current_generation == self.tsp.max_generation
            ):
                self.timer.stop()

        except Exception as err:
            pass

    def save_results(self):
        new_index = self.sort_by_route(self.tsp.population.best_route.sequence)

        results_df = self.tsp.data.dataset.copy()

        results_df.index = new_index
        results_df.sort_index(inplace=True)

        default_file = f"{default_dir}/best_route.xlsx"
        options = QFileDialog.Option(QFileDialog.Option.DontUseNativeDialog)
        # options = QFileDialog.Option()
        # options |= QFileDialog..DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save File", default_file, "Excel File (*.xlsx)", options=options
        )
        if fileName:
            results_df.to_excel(fileName, index=False)
            show_alert("File saved.")

    # Moves to center
    def center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def sort_by_route(self, sequence: list):
        order_df = pd.DataFrame({"sequence": sequence})
        order_df.sort_values("sequence", inplace=True)
        return list(order_df.index)


class Signals(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = Signals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.started.emit()
            self.fn(*self.args, **self.kwargs)
        except:
            pass
        finally:
            self.signals.finished.emit()


def show_alert(text):
    alert = QMessageBox()
    alert.setText(text)
    alert.exec()


app = QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec())

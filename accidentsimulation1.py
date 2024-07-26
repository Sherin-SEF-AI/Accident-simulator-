import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QDateTimeEdit, QComboBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QDateTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import csv
import time

class SimulationThread(QThread):
    data_signal = pyqtSignal(float, float, float, float, str)

    def __init__(self, speed, scenario, collision_type):
        super().__init__()
        self.speed = speed
        self.scenario = scenario
        self.collision_type = collision_type
        self.running = True

    def run(self):
        start_time = time.time()
        while self.running:
            current_time = time.time() - start_time
            acceleration, gyroscope, gps = self.generate_data()
            self.data_signal.emit(current_time, self.speed, acceleration, gyroscope, gps)
            time.sleep(0.1)

    def generate_data(self):
        if self.scenario == "Urban Driving":
            acceleration = self.speed / 10 + np.random.randn() * 0.5
            gyroscope = np.random.randn() * 5
            gps = "37.7749° N, 122.4194° W"
        elif self.scenario == "Highway Driving":
            acceleration = self.speed / 5 + np.random.randn() * 0.2
            gyroscope = np.random.randn() * 2
            gps = "34.0522° N, 118.2437° W"
        elif self.scenario == "Off-road Driving":
            acceleration = self.speed / 8 + np.random.randn() * 1.0
            gyroscope = np.random.randn() * 15
            gps = "36.7783° N, 119.4179° W"
        elif self.scenario == "Accident":
            if self.collision_type == "Car to Car":
                acceleration = self.speed / 1 + np.random.randn() * 2.0
                gyroscope = np.random.randn() * 30
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Bike":
                acceleration = self.speed / 1.2 + np.random.randn() * 2.5
                gyroscope = np.random.randn() * 35
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Bus":
                acceleration = self.speed / 0.8 + np.random.randn() * 1.8
                gyroscope = np.random.randn() * 25
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Pedestrian":
                acceleration = self.speed / 1.5 + np.random.randn() * 3.0
                gyroscope = np.random.randn() * 40
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Truck":
                acceleration = self.speed / 0.7 + np.random.randn() * 2.0
                gyroscope = np.random.randn() * 20
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Motorcycle":
                acceleration = self.speed / 1.1 + np.random.randn() * 2.8
                gyroscope = np.random.randn() * 33
                gps = "40.7128° N, 74.0060° W"
            elif self.collision_type == "Car to Bicycle":
                acceleration = self.speed / 1.3 + np.random.randn() * 3.2
                gyroscope = np.random.randn() * 38
                gps = "40.7128° N, 74.0060° W"
        return acceleration, gyroscope, gps

    def stop(self):
        self.running = False

class VehicleSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.simulation_thread = None
        self.collision_data = []

    def init_ui(self):
        self.setWindowTitle("Vehicle Accident Simulator")

        # Create widgets
        self.date_input = QDateTimeEdit(self)
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.date_input.setDateTime(QDateTime.currentDateTime())

        self.speed_input = QLineEdit(self)
        self.speed_input.setPlaceholderText("Enter speed (km/h)")

        self.scenario_input = QComboBox(self)
        self.scenario_input.addItems(["Urban Driving", "Highway Driving", "Off-road Driving", "Accident"])

        self.collision_type_input = QComboBox(self)
        self.collision_type_input.addItems([
            "Car to Car", "Car to Bike", "Car to Bus", "Car to Pedestrian", 
            "Car to Truck", "Car to Motorcycle", "Car to Bicycle"
        ])

        self.status_label = QLabel(self)
        self.status_label.setText("Status: Ready")

        # Layouts
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Date and Time:"))
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(QLabel("Speed (km/h):"))
        form_layout.addWidget(self.speed_input)
        form_layout.addWidget(QLabel("Scenario:"))
        form_layout.addWidget(self.scenario_input)
        form_layout.addWidget(QLabel("Collision Type:"))
        form_layout.addWidget(self.collision_type_input)
        form_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        start_button = QPushButton("Start Simulation")
        stop_button = QPushButton("Stop Simulation")
        save_button = QPushButton("Save Data")
        clear_button = QPushButton("Clear Data")

        start_button.clicked.connect(self.start_simulation)
        stop_button.clicked.connect(self.stop_simulation)
        save_button.clicked.connect(self.save_data)
        clear_button.clicked.connect(self.clear_data)

        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        # Create and set up canvas for plots
        self.figure, self.ax = plt.subplots(4, 1, figsize=(10, 15), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.time_data = []
        self.speed_data = []
        self.acceleration_data = []
        self.gyroscope_data = []
        self.gps_data = []

    def start_simulation(self):
        try:
            date_time = self.date_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            speed = float(self.speed_input.text())
            scenario = self.scenario_input.currentText()
            collision_type = self.collision_type_input.currentText()

            if scenario == "Accident" and not collision_type:
                self.status_label.setText("Error: Collision type must be selected for accidents.")
                return

            self.status_label.setText("Status: Simulation Running")
            self.simulation_thread = SimulationThread(speed, scenario, collision_type)
            self.simulation_thread.data_signal.connect(self.collect_data)
            self.simulation_thread.start()
            self.timer.start(100)
        except ValueError:
            self.status_label.setText("Error: Please enter valid numeric values.")

    def stop_simulation(self):
        if self.simulation_thread is not None:
            self.simulation_thread.stop()
            self.simulation_thread.wait()
            self.timer.stop()
            self.status_label.setText("Status: Simulation Stopped")

    def collect_data(self, current_time, speed, acceleration, gyroscope, gps):
        self.time_data.append(current_time)
        self.speed_data.append(speed)
        self.acceleration_data.append(acceleration)
        self.gyroscope_data.append(gyroscope)
        self.gps_data.append(gps)

        if len(self.time_data) > 100:
            self.time_data.pop(0)
            self.speed_data.pop(0)
            self.acceleration_data.pop(0)
            self.gyroscope_data.pop(0)
            self.gps_data.pop(0)

        self.collision_data.append({
            'time': current_time,
            'speed': speed,
            'acceleration': acceleration,
            'gyroscope': gyroscope,
            'gps': gps
        })

    def save_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)", options=options)
        if file_name:
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Time', 'Speed', 'Acceleration', 'Gyroscope', 'GPS'])
                for data in self.collision_data:
                    writer.writerow([data['time'], data['speed'], data['acceleration'], data['gyroscope'], data['gps']])
            self.status_label.setText(f"Data saved to {file_name}")

    def clear_data(self):
        self.time_data.clear()
        self.speed_data.clear()
        self.acceleration_data.clear()
        self.gyroscope_data.clear()
        self.gps_data.clear()
        self.collision_data.clear()
        self.ax[0].clear()
        self.ax[1].clear()
        self.ax[2].clear()
        self.ax[3].clear()
        self.canvas.draw()
        self.status_label.setText("Data cleared")

    def update_plot(self):
        self.ax[0].clear()
        self.ax[1].clear()
        self.ax[2].clear()
        self.ax[3].clear()

        self.ax[0].plot(self.time_data, self.speed_data, label='Speed (km/h)', color='blue')
        self.ax[0].set_title('Speed Over Time')
        self.ax[0].set_xlabel('Time (s)')
        self.ax[0].set_ylabel('Speed (km/h)')
        self.ax[0].legend()
        self.ax[0].grid(True)

        self.ax[1].plot(self.time_data, self.acceleration_data, label='Acceleration (m/s²)', color='green')
        self.ax[1].set_title('Acceleration Over Time')
        self.ax[1].set_xlabel('Time (s)')
        self.ax[1].set_ylabel('Acceleration (m/s²)')
        self.ax[1].legend()
        self.ax[1].grid(True)

        self.ax[2].plot(self.time_data, self.gyroscope_data, label='Gyroscope (degrees/s)', color='red')
        self.ax[2].set_title('Gyroscope Over Time')
        self.ax[2].set_xlabel('Time (s)')
        self.ax[2].set_ylabel('Gyroscope (degrees/s)')
        self.ax[2].legend()
        self.ax[2].grid(True)

        # Scatter plot for GPS data
        gps_times = [i for i in range(len(self.gps_data))]
        self.ax[3].scatter(gps_times, [1]*len(self.gps_data), label='GPS Data', color='purple', marker='x')
        self.ax[3].set_title('GPS Data')
        self.ax[3].set_xlabel('Time (Index)')
        self.ax[3].set_yticks([])
        self.ax[3].set_ylabel('GPS Data')
        self.ax[3].legend()
        self.ax[3].grid(True)

        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    simulator = VehicleSimulator()
    simulator.show()
    sys.exit(app.exec_())


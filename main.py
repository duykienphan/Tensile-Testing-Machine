import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from gui import Ui_MainWindow
import time
import csv
import serial.tools.list_ports
import pyqtgraph as pg

from esp import ESP

class SerialReceiverThread(QThread):
    # Tín hiệu để gửi dữ liệu nhận được từ luồng đến giao diện chính
    data_received = pyqtSignal(str)

    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com  # Cổng serial mà ta đã kết nối
        self.is_running = True

    def run(self):
        while self.is_running:
            if self.serial_com and self.serial_com.in_waiting > 0:
                raw_data = self.serial_com.readline().strip()
                decoded_data = raw_data.decode("utf-8", errors="replace")
                print(decoded_data)
                if decoded_data:
                    self.data_received.emit(decoded_data)  # Phát tín hiệu khi có dữ liệu mới
    
    def stop(self):
        self.is_running = False
        self.wait()  # Đợi luồng dừng hẳn

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_win = QMainWindow()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self.main_win)
        self.esp = ESP()

        # Đồ thị PyQtGraph 1
        self.uic.graphicsView.setBackground("w")
        self.curve = self.uic.graphicsView.plot(pen=pg.mkPen(color='r', width=2, style=pg.QtCore.Qt.SolidLine), symbol='o', symbolSize=8, symbolBrush='r')
        self.curve_line2 = self.uic.graphicsView.plot(pen=pg.mkPen(color='b', width=2))
        self.uic.graphicsView.setLabel('left', 'Force (mN)')
        self.uic.graphicsView.setLabel('bottom', 'Distance (mm)')
        legend = self.uic.graphicsView.addLegend()
        legend.addItem(self.curve, "Force")
        legend.addItem(self.curve_line2, "Resistance")

        self.COM_PORT = ""
        self.BAUD_RATE = 9600
        self.PORT_LIST, self.DRIVER_LIST = self.esp.get_com_port()
        self.serialCom = None
        self.data_force = []
        self.data_distance = []
        self.data_time = []
        self.time_sent = 0
        self.csv_data = []

        self.uic.comboBox.addItems(self.PORT_LIST)
        self.uic.comboBox_2.addItems(["4800", "9600", "14400", "19200", "28800", "38400", "57600", "115200"])
        self.uic.comboBox_2.setCurrentText(str(self.BAUD_RATE))

        self.uic.pushButton_6.clicked.connect(self.btn_refresh)
        self.uic.pushButton_3.clicked.connect(self.btn_connect)
        self.uic.pushButton_4.clicked.connect(self.btn_disconnect)
        self.uic.pushButton.clicked.connect(self.btn_send_serial_monitor)
        self.uic.pushButton_2.clicked.connect(self.btn_clear_serial_monitor)

        self.uic.actionOpen.triggered.connect(self.open_serial_monitor)
        self.uic.actionClose.triggered.connect(self.close_serial_monitor)
        self.uic.actionClear_Graph_1.triggered.connect(self.clear_graph_1)
        self.uic.actionClear_All.triggered.connect(self.clear_all)
        self.uic.actionExit.triggered.connect(self.exit_application)
        self.uic.actionSave_as_2.triggered.connect(self.csv_save)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
    
    def clear_graph_1(self):
        self.curve.clear()
        self.curve_line2.clear()
        self.data_force = []
        self.data_distance = []
        self.data_time = []

    def clear_all(self):
        self.curve.clear()
        self.curve_line2.clear()

        self.data_force = []
        self.data_distance = []

    def update_plot(self):
        if len(self.data_force) > 100:
            self.data_force.pop(0)
            self.data_distance.pop(0)
            self.data_time.pop(0)
            #print(self.data_force)
        self.curve.setData(self.data_distance, self.data_force)

    def btn_send_serial_monitor(self):
        data = self.uic.lineEdit.text()
        #print(data)
        if self.serialCom is not None:
            try:
                self.serialCom.write(data.encode())
                print("Data send:", data)
                self.serial_monitor(data)
                self.uic.lineEdit.clear()
                #time.sleep(0.5)
            except:
                print("Failed to send data!")
                self.serial_monitor("Failed to send data!")

    def btn_clear_serial_monitor(self):
        self.uic.textEdit.clear()

    def btn_refresh(self):
        self.PORT_LIST, self.DRIVER_LIST = self.esp.get_com_port()
        self.uic.comboBox.clear()
        self.uic.comboBox.addItems(self.PORT_LIST)
        self.serial_monitor("Refreshed serial port")
    
    def btn_connect(self):
        self.COM_PORT = self.uic.comboBox.currentText()
        self.BAUD_RATE = int(self.uic.comboBox_2.currentText())
        if self.COM_PORT:
            self.uic.label_13.setText(self.DRIVER_LIST[self.PORT_LIST.index(self.COM_PORT)])
            try:
                self.serialCom = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
                print("Initialized serial port")
                self.serial_monitor("Initialized serial port")

                # Khởi tạo và chạy luồng nhận dữ liệu
                self.receiver_thread = SerialReceiverThread(self.serialCom)
                self.receiver_thread.data_received.connect(self.handle_data_received)
                self.receiver_thread.start()  # Bắt đầu nhận dữ liệu

                # QTimer
                self.clear_all()
                self.timer.start(50)  # Cập nhật đồ thị mỗi 50ms
            except:
                print("Failed to initialize serial port")
                self.serial_monitor("Failed to initialize serial port")
                self.serialCom = None
        else:
            print("No serial port selected.")
            self.serial_monitor("No serial port selected.")
    
    def btn_disconnect(self):
        if self.receiver_thread:
            self.receiver_thread.stop()  # Dừng luồng nhận dữ liệu
            self.receiver_thread = None

        if hasattr(self, 'serialCom') and self.serialCom.is_open:
            self.serialCom.close()
            print("Serial port closed.")
            self.serial_monitor("Serial port closed.")
        self.timer.stop()
        self.time_sent = 0
        self.uic.label_13.setText("N/A")

    def handle_data_received(self, data):
        #print(data)
        self.serial_monitor(data)
        self.csv_data.append(data)
        try:
            values = data.split(',') 
            if len(values) == 3:
                if len(values[0]) < 5:
                    self.data_force.append(int(values[0]))
                else:
                    self.data_force.append(0)
                self.data_distance.append(int(values[1]))
                self.data_time.append(int(values[2]))
                self.time_sent += 50 # Thời gian delay trên vi điều khiển
                #print(values)
            else:
                print("Error: Invalid data format")
                self.serial_monitor("Error: Invalid data format")
        except Exception as e:
            error_message = f"Error parsing data: {e}"
            print(error_message)
            self.serial_monitor(error_message)
        
    def csv_save(self):
        file_name = time.strftime("data_%Y%m%d_%H%M%S.csv")
        try:
            with open(file_name, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Process each string in csv_data
                for row in self.csv_data:
                    writer.writerow(row.split(','))
            error_message = f"Data saved to {file_name} successfully."
            print(error_message)
            self.serial_monitor(error_message)
        except Exception as e:
            error_message = f"Error saving to CSV: {e}"
            self.serial_monitor(error_message)
    
    def open_serial_monitor(self):
        self.uic.groupBox.setVisible(True)

    def close_serial_monitor(self):
        self.uic.groupBox.setVisible(False)

    def serial_monitor(self, text):
        display_text = str(time.strftime('%H:%M:%S', time.localtime())) + "->" + str(text)
        self.uic.textEdit.append(display_text)


    def show(self):
        self.main_win.show()

    def exit_application(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
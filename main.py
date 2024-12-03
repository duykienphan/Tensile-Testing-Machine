import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from gui import Ui_MainWindow
import time
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
        self.curve = self.uic.graphicsView.plot(pen=pg.mkPen(color='r', width=2))
        self.curve_line2 = self.uic.graphicsView.plot(pen=pg.mkPen(color='b', width=2))
        self.uic.graphicsView.setLabel('left', 'Value')
        self.uic.graphicsView.setLabel('bottom', 'Time (ms)')
        legend = self.uic.graphicsView.addLegend()
        legend.addItem(self.curve, "Pressure")
        legend.addItem(self.curve_line2, "Voltage")

        self.COM_PORT = ""
        self.BAUD_RATE = 115200
        self.PORT_LIST, self.DRIVER_LIST = self.esp.get_com_port()
        self.serialCom = None
        self.data_graph = []
        self.data_graph_line2 = []
        self.data_graph_2 = []
        self.data_graph_3 = []
        self.time_graph = []
        self.time_graph_2 = []
        self.time_graph_3 = []
        self.time_sent = 0

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
    
    def clear_graph_1(self):
        self.curve.clear()
        self.curve_line2.clear()
        self.data_graph = []
        self.data_graph_line2 = []
        self.time_graph = []

    def clear_all(self):
        self.curve.clear()
        self.curve_line2.clear()

        self.data_graph = []
        self.data_graph_line2 = []

    def update_plot(self):
        if len(self.data_graph) > 100:
            self.data_graph.pop(0)
            self.data_graph_line2.pop(0)
            self.time_graph.pop(0)
            #print(self.data_graph)
        self.curve.setData(self.time_graph, self.data_graph)
        self.curve_line2.setData(self.time_graph, self.data_graph_line2)

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

        try:
            values = data.split('/') 
            if len(values) == 2:
                self.data_graph.append(int(values[0]))
                self.data_graph_line2.append(int(values[1]))
                self.time_sent += 50 # Thời gian delay trên vi điều khiển
                #print(values)
            else:
                print("Error: Invalid data format")
                self.serial_monitor("Error: Invalid data format")
        except:
            print("Error parsing data")
            self.serial_monitor("Error parsing data")
    
    def open_serial_monitor(self):
        self.uic.groupBox.setVisible(True)

    def close_serial_monitor(self):
        self.uic.groupBox.setVisible(False)

    def serial_monitor(self, text):
        display_text = str(time.strftime("%H:%M:%S", time.localtime())) + " -> " + text
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
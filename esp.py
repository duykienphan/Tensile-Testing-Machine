import serial.tools.list_ports

class ESP:
    def __init__(self):
        self.processors = ["USB-SERIAL CH340", "Silicon Labs CP210x USB to UART Bridge", "USB Serial Port"]

    def get_com_port(self):
        self.ports = list(serial.tools.list_ports.comports())
        self.port_lst = []
        self.driver_lst = []
        for port in self.ports:
            self.port_lst.append(port.device)

            driver = port.description.split('(')[0].strip()
            if driver == self.processors[0]:
                driver = "Arduino"
            elif driver == self.processors[1]:
                driver = "ESP32"
            elif driver == self.processors[2]:
                driver = "ESP8266"
            self.driver_lst.append(driver)
        return self.port_lst, self.driver_lst
        
if __name__ == "__main__":
    esp = ESP()

    print(esp.get_name_driver())
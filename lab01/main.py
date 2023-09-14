import time
import tkinter as tk
import serial
from serial.tools import list_ports
from threading import Thread


def get_available_ports():
    return sorted(list(set([int(port.device.split("COM")[1]) for port in list_ports.comports()])))


class MainWindow:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.title('COM-PORT')

        self.port = None
        self.count_stop_bites = serial.STOPBITS_ONE
        self.count_accepted_bytes = 0
        self.speed = 115200

        self.create_interface()
        self.open_port()
        self.auto_detect_ports()

        bytes_thread = Thread(target=self.count_accepted_bytes_thread, args=(), daemon=True)
        bytes_thread.start()
        read_thread = Thread(target=self.read_data_thread, args=(), daemon=True)
        read_thread.start()

    def create_interface(self):
        for c in range(2): self.main_window.columnconfigure(index=c, weight=1)
        for r in range(3): self.main_window.rowconfigure(index=r, weight=1)

        # Окно ввода
        input_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        input_frame.grid(row=0, column=0, padx=5, pady=5)
        input_text = tk.Text(master=input_frame, height=10, width=25)
        input_text.bind("<Key>", self.on_input_update)
        input_text.bind("<Return>", self.on_enter_update, add="+")
        input_text.pack()

        # Окно вывода
        output_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        output_frame.grid(row=0, column=1, padx=5, pady=5)
        self.output_text = tk.Text(master=output_frame, height=10, width=25)
        self.output_text.config(state="disabled")
        self.output_text.pack()

        # Окно управления
        control_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        control_frame.grid(row=1, column=0, padx=5, pady=5)
        top_control_frame = tk.Frame(control_frame)
        bottom_control_frame = tk.Frame(control_frame)

        com_port_label = tk.Label(master=top_control_frame, text="COM Port:")
        com_port_label.pack(side=tk.LEFT)
        self.com_port_var = tk.StringVar()
        self.com_port_menu = tk.OptionMenu(top_control_frame, self.com_port_var, "")
        self.com_port_menu.pack(side=tk.LEFT)
        connect_button = tk.Button(top_control_frame, text="Connect", command=self.connect_to_port)
        connect_button.pack(side=tk.LEFT)

        top_control_frame.pack()

        self.stopbits_label = tk.Label(bottom_control_frame, text="Stop Bits:")
        self.stopbits_label.pack(side=tk.LEFT)
        stop_bits_values = list(map(str, [serial.STOPBITS_ONE, serial.STOPBITS_TWO]))
        self.stopbits_var = tk.StringVar()
        self.stopbits_menu = tk.OptionMenu(bottom_control_frame, self.stopbits_var, "")
        self.stopbits_menu.pack(side=tk.LEFT)
        self.stopbits_menu['menu'].delete(0, 'end')
        for stopbit in stop_bits_values:
            self.stopbits_menu['menu'].add_command(label=stopbit, command=tk._setit(self.stopbits_var, stopbit))
        self.stopbits_var.set(str(stop_bits_values[0]))
        self.apply_button = tk.Button(bottom_control_frame, text="Apply", command=self.apply_settings)
        self.apply_button.pack(side=tk.LEFT)

        bottom_control_frame.pack()

        # Окно состояния
        status_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        status_frame.grid(row=1, column=1, padx=5, pady=5)
        self.status_text = tk.Text(master=status_frame, height=10, width=25)
        self.status_text.config(state="disabled")
        self.status_text.pack()

        # Опциональное отладочное окно
        log_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        log_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        self.log_text = tk.Text(master=log_frame, height=10, width=25)
        self.log_text.config(state="disabled")
        self.log_text.pack()

    def auto_detect_ports(self):
        available_ports = get_available_ports()
        if available_ports:
            self.com_port_menu['menu'].delete(0, 'end')
            for port in available_ports:
                self.com_port_menu['menu'].add_command(label=port, command=tk._setit(self.com_port_var, port))
            self.com_port_var.set(str(self.port.port.split("COM")[1]))

    def open_port(self):
        for port in get_available_ports():
            try:
                self.port = serial.Serial('COM' + str(port), self.speed, stopbits=self.count_stop_bites)
                self.make_log(f"Port is open. Now you can send and receive data\n")
                break
            except serial.SerialException:
                continue
        if self.port is None:
            self.make_log("No available ports\n")

    def connect_to_port(self):
        port = self.com_port_var.get()
        current_port = self.port.port
        try:
            self.port.close()
            self.port = serial.Serial("COM" + port, self.speed, stopbits=self.count_stop_bites)
            self.make_log(f"Connected to {port}\n")
        except serial.SerialException as e:
            self.make_log(f"Error: {str(e)}\n")
            self.port = serial.Serial(current_port, self.speed, stopbits=self.count_stop_bites)
            self.make_log(f"Current port: {current_port}\n")

    def apply_settings(self):
        stop_bites = float(self.stopbits_var.get())
        if self.port:
            try:
                match stop_bites:
                    case serial.STOPBITS_ONE:
                        self.port.stopbits = serial.STOPBITS_ONE
                        self.count_stop_bites = serial.STOPBITS_ONE
                        self.make_log(f"Stop Bits set to {serial.STOPBITS_ONE}")
                    case serial.STOPBITS_TWO:
                        self.port.stopbits = serial.STOPBITS_TWO
                        self.count_stop_bites = serial.STOPBITS_TWO
                        self.make_log(f"Stop Bits set to {serial.STOPBITS_TWO}")
                    case _:
                        self.make_log(f"No one matched")
            except ValueError:
                self.make_log("Invalid Stop Bits value")
        else:
            self.make_log("Port is closed")

    def on_input_update(self, event):
        if len(list(serial.tools.list_ports.comports())) == 0:
            self.open_port()
        self.send_data(event.char.encode('cp1251'))

    def on_enter_update(self, event):
        if len(list(serial.tools.list_ports.comports())) == 0:
            self.open_port()
        self.send_data(b"\n")

    def send_data(self, data):
        try:
            if self.port:
                self.port.write(data)
            else:
                self.make_log('Port is closed')
        except serial.SerialException:
            self.make_log('Error writing to port')

    def make_log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.config(state='disabled')

    def make_status(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.config(state='disabled')

    def count_accepted_bytes_thread(self):
        self.make_status(f"COM-port speed = {self.speed}")
        while True:
            message = f"Accepted bytes = {self.count_accepted_bytes}"
            self.make_status(message)
            time.sleep(10)

    def read_data_thread(self):
        while True:
            out = self.port.read(1).decode('cp1251')
            self.count_accepted_bytes += 1
            self.output_text.config(state='normal')
            self.output_text.insert(tk.END, out)
            self.output_text.config(state='disabled')


if __name__ == "__main__":
    app = MainWindow()
    app.main_window.mainloop()

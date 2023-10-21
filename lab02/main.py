import tkinter as tk
import serial
from serial.tools import list_ports
from threading import Thread

from ByteStuffing import ByteStuffing


def get_available_ports():
    return sorted(list(set([int(port.device.split("COM")[1]) for port in list_ports.comports()])))


class MainWindow:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.title('COM-PORT')
        self.main_window.resizable(False, False)

        self.port = None
        self.count_stop_bites = serial.STOPBITS_ONE
        self.count_accepted_bytes = 0
        self.speed = 115200

        self.cache = ""
        self.byte_stuffing = ByteStuffing()

        self.create_interface()
        self.open_port()
        self.auto_detect_ports()

        read_thread = Thread(target=self.read_data_thread, args=(), daemon=True)
        read_thread.start()

    def create_interface(self):

        # Окно ввода
        input_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        input_frame.grid(row=0, column=0, padx=5, pady=5)
        input_label = tk.Label(master=input_frame, text="Input")
        input_label.pack()

        input_scroll = tk.Scrollbar(input_frame, orient='vertical')
        input_scroll.pack(side=tk.RIGHT, fill='y')

        input_text = tk.Text(master=input_frame, height=15, width=40, yscrollcommand=input_scroll.set)
        input_text.bind("<Key>", self.on_input_update)
        input_text.bind("<Return>", self.on_enter_update, add="+")
        input_scroll.config(command=input_text.yview)
        input_text.pack()

        # Окно вывода
        output_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        output_frame.grid(row=0, column=1, padx=5, pady=5)
        output_label = tk.Label(master=output_frame, text="Output")
        output_label.pack()

        output_scroll = tk.Scrollbar(output_frame, orient='vertical')
        output_scroll.pack(side=tk.RIGHT, fill='y')

        self.output_text = tk.Text(master=output_frame, height=15, width=40, yscrollcommand=output_scroll.set)
        self.output_text.config(state="disabled")
        output_scroll.config(command=self.output_text.yview)
        self.output_text.pack()

        # Окно управления
        control_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        control_frame.grid(row=1, column=0, padx=5, pady=5, ipadx=35)
        top_control_frame = tk.Frame(control_frame, pady=7)
        bottom_control_frame = tk.Frame(control_frame, pady=7)

        com_port_label = tk.Label(master=top_control_frame, text="COM Port:")
        com_port_label.pack(side=tk.LEFT)
        self.com_port_var = tk.StringVar()
        self.com_port_menu = tk.OptionMenu(top_control_frame, self.com_port_var, "")
        self.com_port_menu.pack(side=tk.LEFT)
        connect_button = tk.Button(top_control_frame, text="Choose", command=self.connect_to_port)
        connect_button.pack(side=tk.LEFT)

        top_control_frame.pack(side=tk.TOP)

        self.stopbits_label = tk.Label(bottom_control_frame, text="Stop Bits:")
        self.stopbits_label.pack(side=tk.LEFT)
        stop_bits_values = list(map(str, [serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO]))
        self.stopbits_var = tk.StringVar()
        self.stopbits_menu = tk.OptionMenu(bottom_control_frame, self.stopbits_var, "")
        self.stopbits_menu.pack(side=tk.LEFT)
        self.stopbits_menu['menu'].delete(0, 'end')
        for stopbit in stop_bits_values:
            self.stopbits_menu['menu'].add_command(label=stopbit, command=tk._setit(self.stopbits_var, stopbit))
        self.stopbits_var.set(str(stop_bits_values[0]))
        self.apply_button = tk.Button(bottom_control_frame, text="Apply", command=self.apply_settings)
        self.apply_button.pack(side=tk.LEFT)

        bottom_control_frame.pack(side=tk.TOP)

        self.current_com_port_label = tk.Label(master=control_frame, text="Current COM-port:", height=2)
        self.current_com_port_label.pack(side=tk.TOP)

        self.current_count_stop_bits = tk.Label(master=control_frame, text="Current count stop-bits:", height=2)
        self.current_count_stop_bits.pack(side=tk.TOP)

        # Окно состояния
        status_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        status_frame.grid(row=1, column=1, padx=5, pady=5)

        status_scroll = tk.Scrollbar(status_frame, orient='vertical')
        status_scroll.pack(side=tk.RIGHT, fill='y')

        self.status_text = tk.Text(master=status_frame, height=10, width=30, font="Helvetica 10",
                                   yscrollcommand=status_scroll.set)
        self.status_text.config(state="disabled")
        self.status_text.tag_configure("bold", font="Helvetica 10 bold")
        self.status_text.tag_configure("port", foreground="red")
        status_scroll.config(command=self.status_text.yview)
        self.status_text.pack()

        # Опциональное отладочное окно
        log_frame = tk.Frame(master=self.main_window, relief=tk.RIDGE, borderwidth=5)
        log_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        log_scroll = tk.Scrollbar(log_frame, orient='vertical')
        log_scroll.pack(side=tk.RIGHT, fill='y')

        self.log_text = tk.Text(master=log_frame, height=12, width=60, yscrollcommand=log_scroll.set)
        self.log_text.config(state="disabled")
        log_scroll.config(command=self.log_text.yview)
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
                self.current_com_port_label["text"] = f"Current COM-port: {self.port.port}"
                self.current_count_stop_bits["text"] = f"Current count stop-bits: {self.count_stop_bites}"
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
            self.current_com_port_label["text"] = f"Current COM-port: {self.port.port}"
            self.current_count_stop_bits["text"] = f"Current count stop-bits: {self.count_stop_bites}"
            self.cache = ""
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
                        self.current_count_stop_bits["text"] = f"Current count stop-bits: {self.count_stop_bites}"
                    case serial.STOPBITS_TWO:
                        self.port.stopbits = serial.STOPBITS_TWO
                        self.count_stop_bites = serial.STOPBITS_TWO
                        self.make_log(f"Stop Bits set to {serial.STOPBITS_TWO}")
                        self.current_count_stop_bits["text"] = f"Current count stop-bits: {self.count_stop_bites}"
                    case serial.STOPBITS_ONE_POINT_FIVE:
                        self.port.stopbits = serial.STOPBITS_ONE_POINT_FIVE
                        self.count_stop_bites = serial.STOPBITS_ONE_POINT_FIVE
                        self.make_log(f"Stop Bits set to {serial.STOPBITS_ONE_POINT_FIVE}")
                        self.current_count_stop_bits["text"] = f"Current count stop-bits: {self.count_stop_bites}"
                    case _:
                        self.make_log(f"No one matched")
            except serial.serialutil.SerialException as e:
                self.make_log(f"Invalid Stop Bits value\n {e}")
        else:
            self.make_log("Port is closed")

    def on_input_update(self, event):
        if len(list(serial.tools.list_ports.comports())) == 0:
            self.open_port()

        self.cache += event.char
        if len(self.cache) == 3:
            stuff_package = self.byte_stuffing.stuffing(self.cache, self.port.port.replace("COM", ""))
            sending_data = stuff_package.encode("utf-8")
            self.make_stuff_package_status(stuff_package)
            self.send_data(sending_data)
            self.cache = ""

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
        self.log_text.see("end")
        self.log_text.config(state='disabled')

    def make_status(self, message, end='\n'):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + end)
        self.status_text.see("end")
        self.status_text.config(state='disabled')

    def make_bold_status(self, message, end='\n'):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + end, "bold")
        self.status_text.see("end")
        self.status_text.config(state='disabled')

    def make_num_port_status(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message, "port")
        self.status_text.see("end")
        self.status_text.config(state='disabled')

    def make_stuff_package_status(self, stuff_package: str):
        all_stuffs = self.byte_stuffing.get_index_of_stuffs(stuff_package, self.port.port.replace("COM", ""))
        index_num_port = self.byte_stuffing.get_index_of_num_port(stuff_package, self.port.port.replace("COM", ""))
        str_stuff_package = self.byte_stuffing.package2string(stuff_package)
        for i in range(len(str_stuff_package)):
            if i in all_stuffs:
                self.make_bold_status(str_stuff_package[i], '')
            elif i in index_num_port:
                self.make_num_port_status(str_stuff_package[i])
            else:
                self.make_status(str_stuff_package[i], '')
        self.make_status('')

    def make_output(self, message: str):
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, message)
        self.output_text.see("end")
        self.output_text.config(state='disabled')

    def make_stuff_package_output(self, stuff_package: str):
        if stuff_package != "":
            package = self.byte_stuffing.unstuffing(stuff_package)
            payload = self.byte_stuffing.get_payload(package)
            message = f"Total accepted bytes = {self.count_accepted_bytes}"
            self.make_output(payload)
            self.make_status(message)

    def read_data_thread(self):
        self.make_status(f"COM-port speed = {self.speed}")
        while True:
            try:
                stuff_package = ""
                while self.port.inWaiting() > 0:
                    out = self.port.read(1)
                    self.count_accepted_bytes += 1
                    try:
                        stuff_package += out.decode("utf-8")
                    except UnicodeDecodeError:
                        out += self.port.read(1)
                        stuff_package += out.decode("utf-8")

                self.make_stuff_package_output(stuff_package)

            except serial.serialutil.SerialException:
                continue


if __name__ == "__main__":
    app = MainWindow()
    app.main_window.mainloop()

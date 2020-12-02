from tkinter import Frame, LabelFrame, Tk, Menu, OptionMenu, StringVar
from tkinter.ttk import Button, Style
from ctypes import windll
import platform
from screeninfo import get_monitors
from threading import Thread
from queue import Queue
import queue
import serial
import sys
import glob

font_h1 = 'Corbel 14 bold'
font_h2 = 'Corbel 14 '
font_body = 'Corbel 12'


def buscarPuertos():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class Frontend:
    def __init__(self, master, event):
        self.master = master
        self.event = event
        self.opciones_de_puerto = ['-']
        operatingSystem = platform.system()
        if operatingSystem == 'Windows':
            release = platform.release()
            if release == '7':
                windll.user32.SetProcessDPIAware(1)  # Windows 7 y vista
            elif release == '10' or '8':
                windll.shcore.SetProcessDpiAwareness(1)  # Windows 10 y 8

        self.master.title("GUI: Gimbal 2DOF")
        rootWidth = int(screenWidth * 0.4)
        rootHeight = int(screenHeight * 0.8)
        posWidth = (screenWidth - rootWidth) // 2
        posHeight = (screenHeight - rootHeight) // 2
        self.master.geometry(f"{rootWidth}x{rootHeight}+{posWidth}+{posHeight}")
        # TODO: CREACIÓN DE WIDGETS:
        # ------------------------------------------ PLOT1
        self.plot1_label_frame = LabelFrame(
            self.master,
            text='Variables reguladas',
            font=font_h1,
            fg='#267eb5'
        )
        # ------------------------------------------ PLOT2
        self.plot2_label_frame = LabelFrame(
            self.master,
            text='Acciones de control',
            font=font_h1,
            fg='#267eb5'
        )
        # ------------------------------------------ BOTÓN
        self.style_button = Style()
        self.style_button.configure(
            'style_button.TButton',
            foreground='#267eb5',
            font=font_h2,
            relief="flat",
            background="#ccc"
        )
        # ------------------------------------------ CONFIGURACION
        self.frame_config = Frame(self.master)
        self.conectar_button = Button(
            self.frame_config,
            text='Conectar',
            style='style_button.TButton',
            command=lambda: event_queue.put('CONECTAR')
        )
        self.puerto_seleccionado = StringVar()
        self.puerto_seleccionado.set('Puertos')
        self.puertos_optionMenu = OptionMenu(
            self.frame_config,
            self.puerto_seleccionado,
            *self.opciones_de_puerto
        )

        # TODO: MAQUETADO DE WIDGETS:
        self.plot1_label_frame.pack(
            fill='both',
            expand=1,
            anchor='center',
            padx=10,
            pady=(10, 5)
        )
        self.plot2_label_frame.pack(
            fill='both',
            expand=1,
            anchor='center',
            padx=10,
            pady=(5, 10)
        )
        self.frame_config.pack(
            padx=5,
            pady=(5, 10)
        )
        self.conectar_button.grid(row=0, column=0)
        self.puertos_optionMenu.grid(row=0, column=1)

    def crearPuerto(self, puerto):
        print('puerto CREADO')
        menu = self.puertos_optionMenu['menu']
        menu.add_command(
            label=puerto,
            command=lambda puerto=puerto: self.puerto_seleccionado.set(puerto)
        )

    def eliminarPuerto(self, puerto):
        print('puerto ELIMINADO')
        menu = self.puertos_optionMenu['menu']
        last = menu.index("end")
        items = []
        for index in range(last + 1):
            items.append(menu.entrycget(index, "label"))
        pos = items.index(puerto)
        menu.delete(pos)


def Backend(gui):
    mainMenu = ''
    puertos_creados = []
    while True:
        try:
            event = event_queue.get(timeout=0.001)
        except queue.Empty:
            pass

        else:
            print(event)

        puertos_encontrados = buscarPuertos()
        for puerto in puertos_encontrados:
            if not puerto in puertos_creados:
                puertos_creados.append(puerto)
                gui.crearPuerto(puerto)

        cant_puertos_encontrados = len(puertos_encontrados)
        cant_puertos_creados = len(puertos_creados)
        if cant_puertos_creados != cant_puertos_encontrados:
            for puerto in puertos_creados:
                if not puerto in puertos_encontrados:
                    pos = puertos_creados.index(puerto)
                    puertos_creados.pop(pos)
                    gui.eliminarPuerto(puerto)

        print(f"puertos creados {puertos_creados}, var:{gui.puerto_seleccionado.get()}")


if __name__ == '__main__':
    get_monitors()
    root = Tk()
    root.attributes('-topmost', 1)
    screenWidth = root.winfo_screenwidth()
    screenHeight = root.winfo_screenheight()
    event_queue = Queue()
    UI = Frontend(root, event_queue)
    th = Thread(target=Backend, args=(UI,))
    th.daemon = True
    th.start()
    root.mainloop()

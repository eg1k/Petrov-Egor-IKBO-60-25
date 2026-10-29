"""Эмулятор языка оболочки ОС с графическим интерфейсом (этап 1: REPL)."""

import getpass
import socket
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from shell_parser import ParseError, parse


def get_username():
    try:
        return getpass.getuser()
    except Exception:
        return "user"


def get_hostname():
    try:
        return socket.gethostname()
    except OSError:
        return "localhost"


class Shell:
    """Логика оболочки: разбор строки и выполнение команд."""

    def __init__(self):
        self.username = get_username()
        self.hostname = get_hostname()
        self.running = True
        self.commands = {
            "ls": self.cmd_stub,
            "cd": self.cmd_stub,
            "exit": self.cmd_exit,
        }

    def execute(self, line):
        """Выполняет строку и возвращает текст вывода."""
        try:
            args = parse(line)
        except ParseError as e:
            return "Ошибка синтаксиса: %s" % e
        if not args:
            return ""
        name, params = args[0], args[1:]
        handler = self.commands.get(name)
        if handler is None:
            return "%s: команда не найдена" % name
        return handler(name, params)

    def cmd_stub(self, name, params):
        # Заглушка: выводит имя команды и её аргументы
        return "Команда: %s, аргументы: %s" % (name, params)

    def cmd_exit(self, name, params):
        if len(params) > 1:
            return "exit: слишком много аргументов"
        if params and not params[0].lstrip("-").isdigit():
            return "exit: %s: требуется числовой аргумент" % params[0]
        self.running = False
        return ""


class EmulatorApp:
    """Графический интерфейс эмулятора."""

    def __init__(self, root):
        self.root = root
        self.shell = Shell()
        self.prompt = "%s@%s:~$ " % (self.shell.username, self.shell.hostname)

        root.title("Эмулятор - [%s@%s]" % (self.shell.username, self.shell.hostname))
        root.geometry("800x500")

        self.output = ScrolledText(root, bg="black", fg="white",
                                   insertbackground="white", font=("Consolas", 11),
                                   state="disabled", wrap="word")
        self.output.pack(fill="both", expand=True)

        bottom = tk.Frame(root, bg="black")
        bottom.pack(fill="x")
        tk.Label(bottom, text=self.prompt, bg="black", fg="lime",
                 font=("Consolas", 11)).pack(side="left")
        self.entry = tk.Entry(bottom, bg="black", fg="white", insertbackground="white",
                              font=("Consolas", 11), relief="flat")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

        self.write("Добро пожаловать в эмулятор оболочки. Для выхода введите exit.\n")

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def on_enter(self, event=None):
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.write(self.prompt + line + "\n")
        result = self.shell.execute(line)
        if result:
            self.write(result + "\n")
        if not self.shell.running:
            self.root.destroy()


def main():
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""Эмулятор языка оболочки ОС с графическим интерфейсом."""

import argparse
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
        """Выполняет строку и возвращает пару (текст вывода, успех)."""
        try:
            args = parse(line)
        except ParseError as e:
            return "Ошибка синтаксиса: %s" % e, False
        if not args:
            return "", True
        name, params = args[0], args[1:]
        handler = self.commands.get(name)
        if handler is None:
            return "%s: команда не найдена" % name, False
        return handler(name, params)

    def cmd_stub(self, name, params):
        # Заглушка: выводит имя команды и её аргументы
        return "Команда: %s, аргументы: %s" % (name, params), True

    def cmd_exit(self, name, params):
        if len(params) > 1:
            return "exit: слишком много аргументов", False
        if params and not params[0].lstrip("-").isdigit():
            return "exit: %s: требуется числовой аргумент" % params[0], False
        self.running = False
        return "", True


class EmulatorApp:
    """Графический интерфейс эмулятора."""

    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        self.shell = Shell()
        self.vfs_path = vfs_path
        self.script_path = script_path
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
        self.write_params()
        if self.script_path is not None:
            self.root.after(100, self.run_script)

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def write_params(self):
        # Отладочный вывод всех параметров, заданных при запуске
        self.write("[debug] Параметры запуска:\n")
        self.write("[debug]   VFS: %s\n" % (self.vfs_path or "(не задан)"))
        self.write("[debug]   Стартовый скрипт: %s\n" % (self.script_path or "(не задан)"))

    def run_line(self, line):
        """Выполняет строку, отображая ввод и вывод как в диалоге.

        Возвращает True, если команда выполнилась без ошибки.
        """
        self.write(self.prompt + line + "\n")
        result, ok = self.shell.execute(line)
        if result:
            self.write(result + "\n")
        if not self.shell.running:
            self.root.destroy()
        return ok

    def run_script(self):
        try:
            with open(self.script_path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError as e:
            self.write("Ошибка: не удалось открыть стартовый скрипт '%s': %s\n"
                       % (self.script_path, e.strerror))
            return

        self.write("[script] Выполнение стартового скрипта %s\n" % self.script_path)
        for number, line in enumerate(lines, 1):
            # Пустые строки и комментарии не выполняются
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            ok = self.run_line(line)
            if not self.shell.running:
                return
            if not ok:
                self.write("[script] Строка %d пропущена из-за ошибки\n" % number)
        self.write("[script] Стартовый скрипт завершён\n")

    def on_enter(self, event=None):
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.run_line(line)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Эмулятор языка оболочки ОС")
    parser.add_argument("--vfs", metavar="ПУТЬ",
                        help="путь к физическому расположению VFS")
    parser.add_argument("--script", metavar="ПУТЬ",
                        help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    root = tk.Tk()
    EmulatorApp(root, vfs_path=args.vfs, script_path=args.script)
    root.mainloop()


if __name__ == "__main__":
    main()

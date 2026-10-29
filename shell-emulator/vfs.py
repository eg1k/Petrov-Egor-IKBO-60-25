"""Виртуальная файловая система (VFS), которая целиком хранится в памяти.

Источник VFS — ZIP-архив. Архив только читается и не распаковывается на диск.
Содержимое текстовых файлов хранится как строка, двоичных — в кодировке base64.
"""

import base64
import os
import zipfile


class VFSError(Exception):
    pass


class VFSFile:
    def __init__(self, name, data):
        self.name = name
        try:
            if b"\0" in data:
                raise UnicodeDecodeError("utf-8", data, 0, 1, "нулевой байт")
            self.content = data.decode("utf-8")
            self.binary = False
        except UnicodeDecodeError:
            # Двоичные данные хранятся в base64
            self.content = base64.b64encode(data).decode("ascii")
            self.binary = True

    def data(self):
        if self.binary:
            return base64.b64decode(self.content)
        return self.content.encode("utf-8")


class VFSDir:
    def __init__(self, name):
        self.name = name
        self.children = {}


class VFS:
    def __init__(self, source=None):
        self.root = VFSDir("")
        self.source = source

    @classmethod
    def load(cls, path):
        """Загружает VFS из ZIP-архива в память."""
        vfs = cls(path)
        if os.path.isdir(path):
            raise VFSError("'%s' является каталогом, а не ZIP-архивом" % path)
        try:
            with zipfile.ZipFile(path, "r") as archive:
                for info in archive.infolist():
                    parts = split_path(info.filename)
                    if not parts:
                        continue
                    if info.is_dir():
                        vfs._make_dirs(parts)
                    else:
                        parent = vfs._make_dirs(parts[:-1])
                        if parts[-1] in parent.children:
                            raise VFSError("повторяющийся элемент '%s'" % info.filename)
                        parent.children[parts[-1]] = VFSFile(parts[-1], archive.read(info))
        except FileNotFoundError:
            raise VFSError("файл '%s' не найден" % path)
        except IsADirectoryError:
            raise VFSError("'%s' является каталогом, а не ZIP-архивом" % path)
        except PermissionError:
            raise VFSError("нет доступа к '%s'" % path)
        except zipfile.BadZipFile:
            raise VFSError("'%s' не является корректным ZIP-архивом" % path)
        except OSError as e:
            raise VFSError("не удалось прочитать '%s': %s" % (path, e.strerror))
        return vfs

    def _make_dirs(self, parts):
        node = self.root
        for part in parts:
            child = node.children.get(part)
            if child is None:
                child = VFSDir(part)
                node.children[part] = child
            elif not isinstance(child, VFSDir):
                raise VFSError("'%s' одновременно файл и каталог" % "/".join(parts))
            node = child
        return node

    def save(self, path):
        """Сохраняет текущее состояние VFS на диск в формате ZIP."""
        if os.path.isdir(path):
            raise VFSError("'%s' является каталогом" % path)
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                for entry, node in self.walk():
                    if isinstance(node, VFSDir):
                        archive.writestr(entry + "/", b"")
                    else:
                        archive.writestr(entry, node.data())
        except IsADirectoryError:
            raise VFSError("'%s' является каталогом" % path)
        except PermissionError:
            raise VFSError("нет доступа к '%s'" % path)
        except OSError as e:
            raise VFSError("не удалось записать '%s': %s" % (path, e.strerror))

    def walk(self, node=None, prefix=""):
        """Обходит дерево VFS, возвращая пары (путь, узел)."""
        if node is None:
            node = self.root
        for name in sorted(node.children):
            child = node.children[name]
            path = prefix + name
            yield path, child
            if isinstance(child, VFSDir):
                yield from self.walk(child, path + "/")

    def describe(self):
        """Возвращает строки с описанием содержимого VFS."""
        files = dirs = 0
        lines = []
        for path, node in self.walk():
            if isinstance(node, VFSDir):
                dirs += 1
                lines.append("/%s/" % path)
            else:
                files += 1
                kind = ", base64" if node.binary else ""
                lines.append("/%s (%d Б%s)" % (path, len(node.data()), kind))
        return "файлов: %d, каталогов: %d" % (files, dirs), lines


def split_path(name):
    parts = []
    for part in name.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise VFSError("недопустимый путь в архиве '%s'" % name)
        parts.append(part)
    return parts

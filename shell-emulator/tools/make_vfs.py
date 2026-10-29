"""Создаёт тестовые ZIP-архивы VFS в папке vfs/."""

import os
import zipfile

VFS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vfs")

# Минимальный PNG 1x1 пиксель — пример двоичного файла
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360f8cf00000301010018dd8db00000"
    "000049454e44ae426082"
)

ARCHIVES = {
    # Минимальная VFS: один файл
    "minimal.zip": {
        "readme.txt": "Минимальная VFS\n",
    },
    # Несколько файлов в корне, в том числе двоичный
    "several.zip": {
        "readme.txt": "VFS из нескольких файлов\n",
        "notes.txt": "заметка 1\nзаметка 2\n",
        "config.ini": "[main]\nuser=admin\n",
        "logo.png": PNG,
    },
    # Не менее 3 уровней файлов и папок, пустой каталог
    "deep.zip": {
        "readme.txt": "VFS с вложенными каталогами\n",
        "home/": None,
        "home/user/.profile": "export PATH=/bin\n",
        "home/user/docs/notes.txt": "заметки\n",
        "home/user/docs/reports/2025/report.txt": "отчёт за 2025 год\n",
        "home/user/pictures/logo.png": PNG,
        "etc/hosts": "127.0.0.1 localhost\n",
        "tmp/": None,
    },
}


def main():
    os.makedirs(VFS_DIR, exist_ok=True)
    for name, entries in ARCHIVES.items():
        with zipfile.ZipFile(os.path.join(VFS_DIR, name), "w", zipfile.ZIP_DEFLATED) as archive:
            for path, content in entries.items():
                if content is None:
                    archive.writestr(path, b"")
                elif isinstance(content, str):
                    archive.writestr(path, content.encode("utf-8"))
                else:
                    archive.writestr(path, content)
    # Файл с расширением .zip, который не является архивом
    with open(os.path.join(VFS_DIR, "broken.zip"), "w", encoding="utf-8") as f:
        f.write("это не ZIP-архив\n")
    print("Архивы созданы в", os.path.normpath(VFS_DIR))


if __name__ == "__main__":
    main()

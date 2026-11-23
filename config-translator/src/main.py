"""Read a configuration file and print the translated JSON."""

import argparse
import json
import sys
from pathlib import Path

from translator import ConfigError, translate


EXIT_ERROR = 1


def main(argv=None):
    """Run the command and return its exit status."""
    parser = argparse.ArgumentParser(
        description="Преобразование учебной конфигурации в JSON."
    )
    parser.add_argument(
        "-i", "--input", type=Path, required=True, help="входной файл UTF-8"
    )
    options = parser.parse_args(argv)
    try:
        source = options.input.read_text(encoding="utf-8-sig")
        result = translate(source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, UnicodeError, ConfigError, RecursionError) as error:
        print(f"{options.input}: {error}", file=sys.stderr)
        return EXIT_ERROR
    return 0


if __name__ == "__main__":
    sys.exit(main())

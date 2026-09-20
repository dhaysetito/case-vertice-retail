"""Corrige mojibake conhecido sem alterar dados numéricos.

Os arquivos do protótipo são sempre lidos e gravados como UTF-8. A correção
atua somente em sequências típicas de UTF-8 interpretado como Latin-1.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "docs/prototipo/dashboard.js", ROOT / "docs/prototipo/index.html", ROOT / "docs/prototipo/dados.js"]
SUSPICIOUS = re.compile(r"(?:Ã.|Â.|â.{1,2}|Î.)+")


def repair(text: str) -> str:
    replacements = {
        "\u00e2\u2020\u2014": "->", "\u00e2\u2020\u2018": "<-", "\u00e2\u2014\u02c6": "M",
        "\u00e2\u2013\u00a3": "#", "\u00e2\u2014\u2021": "T", "\u00e2\u0153\u2013": "OK",
        "\u00e2\u2020\u02dc": "-", "\u00e2\u2020\u2019": "->", "\u00e2\u0097\u0086": "M",
        "\u00c3\u0192": "Ã", "\u00c3\u201a": "Â",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    def convert(match: re.Match[str]) -> str:
        value = match.group(0)
        for _ in range(3):
            try:
                candidate = value.encode("latin-1").decode("utf-8")
            except UnicodeError:
                break
            if candidate == value:
                break
            value = candidate
        return value

    return SUSPICIOUS.sub(convert, text)


def main() -> None:
    for path in TARGETS:
        original = path.read_text(encoding="utf-8-sig")
        fixed = repair(original)
        path.write_text(fixed, encoding="utf-8", newline="\n")
        print(f"{path.relative_to(ROOT)}: corrigido")


if __name__ == "__main__":
    main()

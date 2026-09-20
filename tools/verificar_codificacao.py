"""Falha se o protótipo contiver sequências conhecidas de mojibake."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "docs/prototipo/dashboard.js", ROOT / "docs/prototipo/index.html", ROOT / "docs/prototipo/dados.js"]
PATTERN = re.compile(r"Ã.|Â.|â.{1,2}|Î.")

errors = []
for path in TARGETS:
    text = path.read_text(encoding="utf-8")
    matches = list(PATTERN.finditer(text))
    if matches:
        errors.append(f"{path.relative_to(ROOT)}: {matches[0].group(0)!r}")
if errors:
    raise SystemExit("Mojibake detectado:\n" + "\n".join(errors))
print("Codificação UTF-8 validada")

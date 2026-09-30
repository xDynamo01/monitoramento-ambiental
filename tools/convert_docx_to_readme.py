from pathlib import Path
import re

from docx import Document


source = Path("Sistema_Integrado_de_Monitoramento_Ambiental.docx")
destination = Path("README.md")
document = Document(source)
lines = [
    "# Sistema Integrado de Monitoramento Ambiental",
    "",
    "Rede em malha, torres autônomas, base de campo tripulada e aeronaves de patrulha para apoio à defesa ambiental.",
    "",
    "> Documento técnico oficial do projeto. O arquivo DOCX original permanece preservado no repositório.",
    "",
]

for paragraph in document.paragraphs:
    text = paragraph.text.strip()
    if not text or text.startswith(("SISTEMA INTEGRADO DE", "DOCUMENTO TÉCNICO PARA APRESENTAÇÃO INSTITUCIONAL", "Sumário")):
        continue
    if text[0].isdigit() and ". " in text[:8]:
        text = f"## {text}"
    lines.extend((text, ""))

destination.write_text("\n".join(lines), encoding="utf-8")

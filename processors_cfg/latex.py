from pathlib import Path
from tools.common import path_with_suffix, write_to_path
from obj.cfg import CFG


def process(cfg: CFG, original_path: Path, text_format: str = None):
    if not text_format:
        text_format = cfg.min_format()
    output_path = path_with_suffix(original_path, "latex")
    content = cfg.to_latex()
    write_to_path(output_path, content)

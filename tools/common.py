from pathlib import Path


def hasupper(string: str) -> bool:
    """return whether a string contains any uppercase letters"""
    return any(x.isupper() for x in string)


def noupper(string: str) -> bool:
    """return whether a string doesn't contains any uppercase letters"""
    return not hasupper(string)


def path_with_suffix(path: Path, suffix: str, separator="_") -> Path:
    """create new path, where path has a new suffix

    e.g. foo.txt + "new" = foo_new.txt"""
    return path.with_stem(f"{path.stem}{separator}{suffix}")


def write_to_path(path: Path, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

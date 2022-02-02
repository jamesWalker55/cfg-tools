# if __name__ == "__main__": import sys, os ; sys.path.insert(1, os.path.join(sys.path[0], '..'))


META_KEYWORDS = ("mode", "format", "action", "#")


class MetaError(Exception):
    pass


def text_to_lines_lists(text: str):
    """separate given text into 'parsing lines' and 'meta lines'"""
    parse_lines = []
    meta_lines = []
    for line in text.strip().split("\n"):
        if len(line.strip()) == 0:
            continue
        first_word = line.split(maxsplit=1)[0]
        if first_word in META_KEYWORDS:
            meta_lines.append(line)
        else:
            parse_lines.append(line)
    return parse_lines, meta_lines


def parse_meta_lines(meta_lines: list[str]):
    meta_data = {}
    for keyword in META_KEYWORDS:
        meta_data[keyword] = []
    for line in meta_lines:
        args = line.split()
        meta_data[args[0]] = args[1:]
    return meta_data

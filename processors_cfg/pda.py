from pathlib import Path
from typing import NamedTuple, Union
from tools.common import path_with_suffix, write_to_path
from obj.cfg import CFG, Letter

from pprint import pprint


def process(cfg: CFG, original_path: Path):
    output_path = path_with_suffix(original_path, "pda")
    content = to_pda(cfg)
    write_to_path(output_path, content)


class Transition(NamedTuple):
    start: str
    content: str
    end: str

    def __repr__(self) -> str:
        return f"""<Transition: {self.start} {self.content} {self.end}>"""

    def __str__(self) -> str:
        return f"{self.start} {self.content} {self.end}"


# some constants:
STATE_START = "init"
STATE_MAIN = "main"
STATE_END = "ed"
STATE_ALPHA_PREFIX = "alpha"  # prefix for accepting alphabet
STATE_VARIABLE_PREFIX = "var"  # prefix for substituting variables


def html_tagger(
    input_names: list[Union[str, Letter]], prefix: str = None, reverse=False
):
    def process_name(name: Union[str, Letter]):
        if not isinstance(name, str):
            name = name.name
        if len(name) == 1:
            return name
        return name[0] + "<SUB>" + name[1:] + "</SUB>"

    if len(input_names) == 0:
        return "e"
    if prefix:
        template = f"<{prefix}(%s)>"
    else:
        template = "<%s>"
    if reverse:
        input_names = input_names[::-1]
    names = [process_name(n) for n in input_names]
    return template % ("".join(names))


template = """
format informal
action render_in unname

start init
end ed

"""


def to_pda(cfg: CFG):
    transitions = []
    start = cfg.start_variable
    alphabet = cfg.all_alphabet()
    rules_map = cfg.rules_map()

    def add(start, content, end):
        transitions.append(Transition(start, content, end))

    pprint(rules_map)
    # initial setup
    add(STATE_START, html_tagger([start, "$"], "push"), STATE_MAIN)
    add(STATE_MAIN, html_tagger(["$"], "pop"), STATE_END)
    # rules
    for var, rules in rules_map.items():
        state_name = STATE_VARIABLE_PREFIX + var.name
        content = html_tagger([var.name], "pop")
        add(STATE_MAIN, content, state_name)
        for rule in rules:
            content = html_tagger(rule.output_word, "push")
            add(state_name, content, STATE_MAIN)
    # alphabet
    for al in alphabet:
        state_name = STATE_ALPHA_PREFIX + al.name
        add(STATE_MAIN, html_tagger([al], "pop"), state_name)
        add(state_name, al.name, STATE_MAIN)

    pda = template
    pda += "\n".join([str(t) for t in transitions])
    return pda

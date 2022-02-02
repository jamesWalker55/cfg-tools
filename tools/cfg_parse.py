from typing import Callable
from obj.cfg import Letter, CFG, Rule
from tools.common import hasupper

ARROWS = ("->", "→")
EPSILON = ("ε", "e")


def determine_arrow(line: str) -> str:
    for arrow in ARROWS:
        if arrow in line:
            return arrow
    raise Exception(f"Line does not have arrow! '{line}'")


def try_set_starting_variable(grammar: CFG, line: str, word_converter: Callable):
    args = line.split()
    if args[0] == "start":
        assert len(args) >= 2
        starting_var = word_converter(args[1])[0]
        grammar.set_start_variable(starting_var)
        return True
    return False


def lines_to_cfg(parse_lines: list[str], word_converter: Callable) -> CFG:
    """convert a bunch of lines to rules

    `word_converter` is a function that converts "0S1" to a tuple of Letters"""

    grammar = CFG()
    for line in parse_lines:
        set_start = try_set_starting_variable(grammar, line, word_converter)
        if set_start:
            continue
        line = line.strip()
        rules = line_to_rules(line, word_converter)
        for rule in rules:
            grammar.add_rule(rule)
    return grammar


def line_to_rules(line: str, word_converter: Callable) -> tuple[Rule]:
    input_str, output_str = line.split(determine_arrow(line), maxsplit=1)
    input_letter = Letter(input_str.strip(), True)
    output_words = map(word_converter, output_str.split("|"))

    def quick_rule(output_word):
        return Rule(input_letter, output_word)

    rules = tuple(map(quick_rule, output_words))
    return rules


def chars_to_word(str_word: str) -> tuple[Letter]:
    """convert a string to word, by treating each character as a Letter

    Example: "abbXY" will have 2 variables `X`, `Y`

    uppercase characters are treated as variables, e.g. "X" """

    def char_to_letter(char: str) -> Letter:
        return Letter(char, char.isupper())

    full_word = str_word.strip()
    if " " in full_word:
        raise Exception(
            f"Spaces within a letter is disallowed with the `chars_to_word` algorithm: '{str_word}'"
        )

    if full_word in EPSILON:
        return ()

    return tuple(map(char_to_letter, full_word))


def spaced_to_word(str_word: str) -> tuple[Letter]:
    """convert a string to word, by treating spaces as separators

    Example: "a b b Ua Ub" will have 2 variables `Ua`, `Ub`

    words that contain uppercase characters are treated as variables, e.g. "Ua" """
    # "    a   b  c    d     ".split() == ['a', 'b', 'c', 'd']
    def quick_letter(name: str):
        has_uppercase = hasupper(name)
        return Letter(name, has_uppercase)

    full_word = str_word.strip()

    if full_word in EPSILON:
        return ()

    return tuple(map(quick_letter, full_word.split()))


def spaced_exclam_to_word(str_word: str) -> tuple[Letter]:
    """convert a string to word, by treating spaces as separators

    Example: "a! b! b! Ua Ub" will have 3 variables `a`, `b`, `b`

    words that have a `!` at the end are treated as variables, e.g. "abc!" """
    # "    a   b  c    d     ".split() == ['a', 'b', 'c', 'd']
    def quick_letter(name: str):
        if name.endswith("!"):
            return Letter(name[:-1], True)
        return Letter(name, False)

    full_word = str_word.strip()

    if full_word in EPSILON:
        return ()

    return tuple(map(quick_letter, full_word.split()))

# if __name__ == "__main__": import sys, os ; sys.path.insert(1, os.path.join(sys.path[0], '..'))

from collections import defaultdict, namedtuple
from typing import Callable
from tools.common import hasupper, noupper


Letter = namedtuple("Letter", ["name", "is_variable"])
Letter.__repr__ = lambda self: f"<{'! ' if self.is_variable else ''}{self.name}>"


def letter_to_str(letter: Letter) -> str:
    if letter.is_variable:
        return f"{letter.name}!"
    return letter.name


Letter.__str__ = letter_to_str


def word_to_str(
    word: tuple[Letter],
    letter_converter: Callable = letter_to_str,
    empty_word: str = "e",
    separator: str = " ",
) -> str:
    """convert a word to string

    - `word`: the input word (`tuple[Letter]`)
    - `letter_converter`: function that converts a Letter to string, adds "!" to variables by default
    - `empty_word`: string to use for empty words, default is unicode epsilon "ε"
    - `separator`: string to put between letters, default is a space " "
    """
    if len(word) > 0:
        return separator.join(map(letter_converter, word))
    else:
        return empty_word


Rule = namedtuple("Rule", ["input_letter", "output_word"])


def rule_to_str(rule: Rule):
    return f"{word_to_str((rule.input_letter, ))} -> {word_to_str(rule.output_word)}"


class CFG:
    """represents a CFG, containing a set of rules"""

    def __init__(self, rules=tuple()) -> None:
        self.start_variable = None
        self.rules: set[Rule]
        self.rules = set()
        for rule in rules:
            self.add_rule(rule)

    def set_start_variable(self, variable: Letter) -> None:
        self.start_variable = variable

    def to_string(
        self,
        word_converter: Callable,
        arrow: str,
        separator: str,
        newline: str = "\n",
        start_variable=True,
    ):
        """convert this cfg to string

        - `word_converter`: converts a word (`tuple[Letter]`) to string
        - `arrow`: the "->" string between input and output
        - `separator`: the "|" string between output words
        - `newline`: the string to put between rules, usually "\\n"
        """

        def rules_to_str(rules: list[Rule]) -> str:
            words = [word_converter(r.output_word) for r in rules]
            return f" {separator} ".join(words)

        sorted_rules = self.rules_map()
        output_lines = []
        if start_variable and self.start_variable:
            start_line = f"start {word_converter((self.start_variable, ))}"
            output_lines.append(start_line)
            output_lines.append("")
        for input_letter, rules in sorted_rules.items():
            rule_str = f"{word_converter((input_letter, ))} {arrow} "
            rule_str += rules_to_str(rules)
            output_lines.append(rule_str)
        return newline.join(output_lines)

    def clone(self):
        new_cfg = CFG(self.rules.copy())
        new_cfg.start_variable = self.start_variable
        return new_cfg

    def __str__(self) -> str:
        return self.to_string(word_to_str, "->", "|")

    def __repr__(self) -> str:
        return f"<CFG: {len(self.rules)} rules>"

    def add_rule(self, rule: Rule):
        self.rules.add(rule)

    def remove_rule(self, rule: Rule):
        self.rules.remove(rule)

    # def sort_rules(self):
    #     def sorter(rule: Rule):
    #         return rule.input_letter.name
    #     self.rules.sort(key=sorter)

    def rules_map(self) -> dict[Letter, list[Rule]]:
        sorted_rules = defaultdict(list)
        for rule in self.rules:
            sorted_rules[rule.input_letter].append(rule)
        return dict(sorted_rules)

    def all_letters(self) -> set[Letter]:
        """return all letters in CFG, including variables"""
        all_letters = set()
        if self.start_variable:
            all_letters.add(self.start_variable)
        for rule in self.rules:
            all_letters.add(rule.input_letter)
            all_letters = all_letters.union(set(rule.output_word))
        return all_letters

    def all_variables(self) -> set[Letter]:
        return set(l for l in self.all_letters() if l.is_variable)

    def all_alphabet(self) -> set[Letter]:
        return set(l for l in self.all_letters() if not l.is_variable)

    def min_format(self) -> str:
        """return the minimum format required to represent this cfg informally

        1. char
        2. spaced
        3. spaced!"""
        alphabet_names = [l.name for l in self.all_alphabet()]
        variable_names = [l.name for l in self.all_variables()]
        all_names = alphabet_names + variable_names
        all_alphabet_no_uppercase = all(map(noupper, alphabet_names))
        all_variables_have_uppercase = all(map(hasupper, variable_names))
        if all_alphabet_no_uppercase and all_variables_have_uppercase:
            all_names_are_one_char = all(map(lambda n: len(n) == 1, all_names))
            if all_names_are_one_char:
                return "char"
            else:
                return "spaced"
        else:
            return "spaced!"

    def to_latex(self) -> str:
        def letter_to_latex(l):
            if len(l.name) == 1:
                return l.name
            elif len(l.name) == 2:
                return l.name[0] + "_" + l.name[1]
            else:
                return l.name[0] + "_{" + l.name[1:] + "}"

        def word_to_latex(w):
            return word_to_str(w, letter_to_latex, r"\epsilon", " ")

        content = self.to_string(
            word_to_latex,
            r"&\rightarrow",
            r"\mid",
            newline=" \\\\\n",
            start_variable=False,
        )
        output = "$$\\begin{aligned}\n" + content + " \\\\\n\\end{aligned}$$"
        return output

    def to_format(self, format):
        if format == "min":
            min_format = self.min_format()
            return self.to_format(min_format)

        elif format == "char":

            def word_converter(w):
                return word_to_str(w, letter_converter=lambda l: l.name, separator="")

        elif format == "spaced":

            def word_converter(w):
                return word_to_str(w, letter_converter=lambda l: l.name)

        elif format == "spaced!":

            def word_converter(w):
                return word_to_str(w)

        else:
            raise Exception(f"Unknown format {format}!")

        return self.to_string(word_converter, "->", "|", "\n")


def quick_word(string: str) -> tuple[Letter]:
    word = []
    for char in string:
        if char.isupper():
            letter = Letter(char, True)
        else:
            letter = Letter(char, False)
        word.append(letter)
    return tuple(word)


def quick_rule(input_letter: str, output_word: str) -> Rule:
    return Rule(Letter("S", True), quick_word(output_word))

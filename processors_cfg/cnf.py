if __name__ == "__main__":
    import sys, os

    sys.path.insert(1, os.path.join(sys.path[0], ".."))

from obj.cfg import CFG, Letter, Rule, rule_to_str
from pathlib import Path
from tools.common import path_with_suffix, write_to_path
import re
from textwrap import indent


def increment_name(variable_name: str):
    """increment a given letter name

    - S -> S0
    - S3 -> S4
    """
    ending_digits_match = re.search(r"\d+$", variable_name)
    if ending_digits_match:
        base_name = variable_name[: ending_digits_match.span()[0]]
        number = int(ending_digits_match.group())
        return f"{base_name}{number + 1}"
    else:
        return variable_name + "0"


def unique_incremented_letters(
    input_letter: Letter, cfg: CFG, amount: str
) -> list[Letter]:
    new_letters = []
    all_names = [l.name for l in cfg.all_letters()]
    previous_name = input_letter.name
    for _ in range(amount):
        new_name = increment_name(previous_name)
        while new_name in all_names:
            new_name = increment_name(new_name)
        new_letters.append(Letter(new_name, input_letter.is_variable))
        previous_name = new_name
    return new_letters


def process(cfg: CFG, original_path: Path, text_format: str = None):
    output_texts = []

    def add_to_text(name: str):
        output_texts.append(name)
        min_format = cfg.to_format("min")
        min_format = f"```\n{min_format}\n```"
        output_texts.append(min_format)

    def export():
        process_text = "\n\n".join(output_texts)
        process_path = path_with_suffix(original_path, "cnf_process")
        final_text = cfg.to_format("min") + "\n\n" + cfg.to_latex()
        final_path = path_with_suffix(original_path, "cnf")
        write_to_path(process_path, process_text)
        write_to_path(final_path, final_text)

    if not cfg.start_variable:
        print("Start variable required for this action!")
        print("Please define `start xxx` in the input file")
        return

    add_to_text("Initial CFG")
    print("Doing START...")

    while need_start(cfg):
        cfg = cnf_start(cfg)
    print(cfg)

    add_to_text("START")
    print("Doing BIN...")

    while need_bin(cfg):
        cfg = cnf_bin(cfg)
    print(cfg)

    add_to_text("BIN")
    print("Doing DEL...")

    while need_del(cfg):
        cfg = cnf_del(cfg)
    print(cfg)

    add_to_text("DEL")
    print("Doing UNIT...")

    while need_unit(cfg):
        cfg = cnf_unit(cfg)
    print(cfg)

    add_to_text("UNIT")
    print("Doing TERM...")

    while need_term(cfg):
        cfg = cnf_term(cfg)
    print(cfg)

    add_to_text("TERM")

    export()


def need_start(cfg: CFG):
    for r in cfg.rules:
        if cfg.start_variable in r.output_word:
            return True
    return False


def cnf_start(input_cfg: CFG):
    cfg = input_cfg.clone()
    # create new start variable
    old_start_var = cfg.start_variable
    new_start_var = unique_incremented_letters(old_start_var, cfg, 1)[0]
    cfg.set_start_variable(new_start_var)
    # create new start rule
    start_rule = Rule(new_start_var, (old_start_var,))
    cfg.add_rule(start_rule)
    return cfg


def need_bin(cfg: CFG):
    for r in cfg.rules:
        if len(r.output_word) > 2:
            return True
    return False


def cnf_bin(input_cfg: CFG):
    def shorten_rule(rule: Rule):
        starting_variable = rule.input_letter
        output_word = tuple(rule.output_word)
        output_word_length = len(output_word)
        assert output_word_length > 2
        working_variables = [starting_variable] + unique_incremented_letters(
            rule.input_letter, input_cfg, output_word_length - 2
        )
        new_rules = []
        for i in range(output_word_length - 1):
            if i == output_word_length - 2:
                new_rules.append(
                    Rule(working_variables[i], tuple(output_word[i : i + 2]))
                )
            else:
                new_rules.append(
                    Rule(
                        working_variables[i], (output_word[i], working_variables[i + 1])
                    )
                )
        return new_rules

    cfg = input_cfg.clone()
    to_remove = []
    to_add = []
    for input_rule in cfg.rules:
        if len(input_rule.output_word) <= 2:
            continue
        to_remove.append(input_rule)
        new_rules = shorten_rule(input_rule)
        for rule in new_rules:
            to_add.append(rule)
        break  # stop loop immediately.
        # we need to add the new rules to the cfg before continuing
        # otherwise unique_incremented_letters may generate duplicate names
        # example cfg: S → aaaS | aab | b
    for rule in to_remove:
        cfg.remove_rule(rule)
    for rule in to_add:
        cfg.add_rule(rule)

    return cfg


def need_del(cfg: CFG):
    for r in cfg.rules:
        if r.input_letter == cfg.start_variable:
            continue
        if len(r.output_word) == 0:
            return True
    return False


def cnf_del(input_cfg: CFG):
    def new_rule_without_letter(rule: Rule, letter: Letter) -> Rule:
        new_output = list(rule.output_word)
        new_output.remove(var)
        return Rule(rule.input_letter, tuple(new_output))

    cfg = input_cfg.clone()
    # find variables to replace
    epsilon_variables = set()
    to_remove = []
    for r in cfg.rules:
        if r.input_letter == cfg.start_variable:
            continue
        if len(r.output_word) == 0:
            epsilon_variables.add(r.input_letter)
            to_remove.append(r)
    for rule in to_remove:
        cfg.remove_rule(rule)
    nonempty_variables = set(cfg.rules_map().keys())
    evar_with_other_rules = epsilon_variables & nonempty_variables
    evar_without_other_rules = epsilon_variables - evar_with_other_rules
    # create new rule with no epsilon
    to_add = []
    to_remove = []
    for input_rule in cfg.rules:
        for var in evar_with_other_rules:
            try:
                to_add.append(new_rule_without_letter(input_rule, var))
            except ValueError:
                continue
        for var in evar_without_other_rules:
            try:
                to_add.append(new_rule_without_letter(input_rule, var))
            except ValueError:
                continue
            to_remove.append(input_rule)
    for rule in to_remove:
        cfg.remove_rule(rule)
    for rule in to_add:
        cfg.add_rule(rule)

    return cfg


def need_unit(cfg: CFG):
    for r in cfg.rules:
        if len(r.output_word) == 1 and r.output_word[0].is_variable:
            return True
    return False


def cnf_unit(input_cfg: CFG):
    cfg = input_cfg.clone()
    to_add = []
    to_remove = []
    for r in cfg.rules:
        if not (len(r.output_word) == 1 and r.output_word[0].is_variable):
            continue
        to_remove.append(r)
        if len(r.output_word) == 1 and r.output_word[0] == r.input_letter:
            # skip adding rules for rules like S -> S, X -> X etc
            continue
        for external_rule in cfg.rules_map()[r.output_word[0]]:
            new_rule = Rule(r.input_letter, external_rule.output_word)
            to_add.append(new_rule)
    for rule in to_remove:
        cfg.remove_rule(rule)
    for rule in to_add:
        cfg.add_rule(rule)
    return cfg


def need_term(cfg: CFG):
    for r in cfg.rules:
        if len(r.output_word) == 2 and any(
            [True for letter in r.output_word if not letter.is_variable]
        ):
            return True
    return False


def cnf_term(input_cfg: CFG):
    cfg = input_cfg.clone()
    letter_map = dict()

    to_add = []
    to_remove = []

    def letter_to_variable(letter: Letter) -> Letter:
        # rule already found
        if letter in letter_map:
            return letter_map[letter]
        # try finding existing rule
        applicable_rules = [
            r
            for r in cfg.rules
            if len(r.output_word) == 1 and r.output_word[0] == letter
        ]
        rules_map = cfg.rules_map()
        applicable_rules = [
            r for r in applicable_rules if len(rules_map[r.input_letter]) == 1
        ]
        if applicable_rules:
            letter_map[letter] = applicable_rules[0].input_letter
            return letter_map[letter]
        # create new rule
        new_variable = Letter(f"U{letter.name}", True)
        if new_variable in cfg.all_letters():
            new_variable = unique_incremented_letters(new_variable, cfg, 1)[0]
        letter_map[letter] = new_variable
        new_rule = Rule(new_variable, (letter,))
        to_add.append(new_rule)
        return new_variable

    for input_rule in cfg.rules:
        if not len(input_rule.output_word) == 2:
            continue
        to_remove.append(input_rule)
        new_output_word = list(input_rule.output_word)
        for i, letter in enumerate(new_output_word):
            if not letter.is_variable:
                new_output_word[i] = letter_to_variable(letter)
        new_rule = Rule(input_rule.input_letter, tuple(new_output_word))
        to_add.append(new_rule)
    for rule in to_remove:
        cfg.remove_rule(rule)
    for rule in to_add:
        cfg.add_rule(rule)
    return cfg

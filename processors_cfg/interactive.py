# if __name__ == "__main__": import sys, os ; sys.path.insert(1, os.path.join(sys.path[0], '..'))

from collections import namedtuple
from pathlib import Path

from anytree.render import RenderTree
from tools.common import path_with_suffix, write_to_path
from obj.cfg import CFG, Letter, Rule, rule_to_str, word_to_str
from tools.cfg_parse import spaced_exclam_to_word
from anytree import Node, PreOrderIter
from anytree.exporter import UniqueDotExporter


class CFGParseTree:
    LetterData = namedtuple("LetterData", ["order", "letter"])

    LETTER, META = range(2)
    ROOT_NAME = "root"

    def __init__(self, starting_word: tuple[Letter]) -> None:
        self.root = Node(self.ROOT_NAME, type=self.META)
        # store the last-added nodes
        self.last_added_stack = list()
        self.tl_root_node = None
        self.branch_word(self.root, starting_word, add_to_stack=False)

    @classmethod
    def termination_node(cls, parent=None):
        """create new node indicating end of expansion

        used when a rule produces epsilon"""
        name = "ε"
        return Node(name, type=cls.META, parent=parent)

    @classmethod
    def new_letter_node(cls, letter: Letter, parent=None) -> Node:
        """create a new node given the letter and the sort order

        sort order is needed because the tree is based on `dict`s, which are unordered"""
        name = str(letter)
        return Node(name, type=cls.LETTER, letter=letter, parent=parent)

    @classmethod
    def new_word_nodes(cls, word: tuple[Letter], parent=None) -> tuple[Node]:
        if len(word) == 0:
            return [cls.termination_node(parent=parent)]
        return [cls.new_letter_node(letter, parent=parent) for letter in word]

    def expand_tree_nodes(self, *args, **kwargs):
        for n in PreOrderIter(self.root):
            yield n

    def leaves(self) -> list[Node]:
        return [n for n in self.root.leaves if n.type == self.LETTER]

    def variable_leaves(self):
        return [
            n for n in self.leaves() if n.type == self.LETTER and n.letter.is_variable
        ]

    def branch_word(self, node: Node, word: tuple[Letter], add_to_stack=True):
        """branch a node to the given word"""
        word_nodes = self.new_word_nodes(word, parent=node)
        if add_to_stack:
            self.last_added_stack.append(word_nodes)

    def show(self):
        print(RenderTree(self.root).by_attr())

    def undo(self):
        newest_nodes = self.last_added_stack.pop()
        for n in newest_nodes:
            n.parent = None

    def render(self, filename="temp.png"):
        def nodeattrfunc(node):
            if node.type == CFGParseTree.META:
                return f'shape=plain, label="{node.name}"'
            else:
                return f'shape=plain, label="{node.letter.name}"'

        num_root_children = len(self.root.children)
        if num_root_children == 1:
            starting_node = self.root.children[0]
        elif num_root_children > 1:
            starting_node = self.root
        else:
            raise Exception("Root has no children!")
        de = UniqueDotExporter(
            starting_node,
            nodeattrfunc=nodeattrfunc,
        )
        de.to_picture(filename)

    def indexed_state(self) -> str:
        """return a string representing the leaves of the parse tree, with variables numbered
        ```
        a b C d E f
            0   1
        ```
        """
        letters = [n.letter for n in self.leaves()]
        names = list()
        labels = list()
        var_index = 0
        for letter in letters:
            name = letter.name
            if letter.is_variable:
                label = str(var_index)
                var_index += 1
            else:
                label = ""
            width = max(len(name), len(label))
            names.append(name.rjust(width))
            labels.append(label.rjust(width))
        line_names = " ".join(names)
        line_labels = " ".join(labels)
        return line_names + "\n" + line_labels

    def node_derivation(self) -> list[list[Node]]:
        """create leftmost derivation of the parsetree as a list of Nodes"""

        def expand_first_variable(node_list: list[Node]):
            new_node_list = node_list.copy()
            for i, node in enumerate(new_node_list):
                children = node.children
                if len(children) != 0:
                    new_node_list[i : i + 1] = children
                    return new_node_list
            return None

        steps = []
        steps.append(list(self.root.children))
        while True:
            new_step = expand_first_variable(steps[-1])
            if new_step == None:
                return steps
            steps.append(new_step)

    def letter_derivation(self) -> list[tuple[Letter]]:
        """create leftmost derivation of the parsetree as a list of Letters"""

        def node_list_to_word(nodes) -> tuple[Letter]:
            return tuple(n.letter for n in nodes if n.type == self.LETTER)

        derivation = self.node_derivation()
        return [node_list_to_word(nodes) for nodes in derivation]

    def str_derivation(self) -> str:
        ld = self.letter_derivation()
        str_steps = [" ".join([l.name for l in w]) for w in ld]
        return " -> ".join(str_steps)


class CFGConsole:
    def __init__(self, cfg: CFG, pt: CFGParseTree) -> None:
        self.cfg = cfg
        self.rules = cfg.rules_map()
        self.pt = pt

    def ask_choice(self):
        """return a variable number, or 'u' / 'q'"""
        state = self.pt.indexed_state()
        var_count = len(self.pt.variable_leaves())
        while True:
            print(state)
            print("Select a variable: (undo with 'u', quit with 'q')")
            choice = self.input().lower()

            if choice in ("u", "q"):
                return choice

            try:
                var_num = int(choice)
            except ValueError:
                print("    Invalid input.")
                continue
            if not (0 <= var_num < var_count):
                print("   Number out of range!")
                continue
            return var_num

    def perform_choice(self, choice):
        """return true/false indicating whether to exit"""
        if isinstance(choice, int):
            self.expand_variable(choice)
        else:
            if choice == "u":
                try:
                    self.pt.undo()
                except IndexError:
                    print("Cannot undo!")
            elif choice == "q":
                return True
        return False

    def expand_variable(self, variable_index: int):
        variable_node = self.get_variable(variable_index)
        variable_letter = variable_node.letter
        var_rules = self.rules.get(variable_node.letter, list())
        if len(var_rules) == 0:
            print(f"No rules found for {variable_letter}")
            return
        elif len(var_rules) == 1:
            print(f"Only 1 rule for {variable_letter}. Applying...")
            rule = var_rules[0]
        else:
            var_rules = sorted(var_rules, key=lambda r: rule_to_str(r))
            rule = self.ask_rule(var_rules)
        self.pt.branch_word(variable_node, rule.output_word)

    def get_variable(self, variable_index: int):
        return self.pt.variable_leaves()[variable_index]

    def ask_rule(self, rules: list[Rule]) -> Rule:
        num_rules = len(rules)
        print("Select a rule:")
        for i, rule in enumerate(rules):
            print(str(i).rjust(3) + ". " + rule_to_str(rule))
        rule_num = self.get_input_range(0, num_rules - 1)
        return rules[rule_num]

    @staticmethod
    def input():
        return input("  > ")

    @classmethod
    def get_input_choice(cls, *args: str):
        while True:
            input_str = cls.input()
            if input_str in args:
                return input_str
            print(f"Invalid choice! {args}")

    @classmethod
    def get_input_range(cls, min, max):
        while True:
            try:
                input_num = int(cls.input())
                if min <= input_num <= max:
                    return input_num
                print(f"   Invalid number, must be in range: {min} <= x <= {max}")
            except ValueError:
                print("   Invalid input, please input a number!")

    @classmethod
    def get_input_word(cls):
        stop = False
        while not stop:
            print(
                "Input a word to start from: (format is 'spaced!', include '!' for variables)"
            )
            str_word = cls.input()
            word = spaced_exclam_to_word(str_word)
            print("Is this word ok? (y/n)")
            print("    " + word_to_str(word))
            stop = cls.get_input_choice("y", "n") == "y"
        return word


def process(cfg: CFG, original_path: Path):
    if cfg.start_variable:
        start_word = (cfg.start_variable,)
    else:
        print("You didn't define a start variable, so enter a starting variable now:")
        start_word = CFGConsole.get_input_word()
    ptree = CFGParseTree(start_word)
    console = CFGConsole(cfg, ptree)
    while True:
        choice = console.ask_choice()
        stop = console.perform_choice(choice)
        if stop:
            break
    derivation_path = path_with_suffix(original_path, "interactive_derivation")
    diagram_path = path_with_suffix(original_path, "interactive_diagram").with_suffix(
        ".png"
    )
    derivation = ptree.str_derivation()
    write_to_path(derivation_path, derivation)
    ptree.render(diagram_path)

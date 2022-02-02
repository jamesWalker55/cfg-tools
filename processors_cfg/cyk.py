from tools.cfg_parse import spaced_exclam_to_word
from processors_cfg.interactive import CFGParseTree
from obj.table import CYKItem, CYKTable
from pathlib import Path
from tools.common import path_with_suffix, write_to_path
from obj.cfg import CFG, Letter, quick_word, rule_to_str
import itertools


def ask_yes_no():
    while True:
        choice = input("  > ").strip().lower()
        if choice in ("y", "n"):
            return choice == "y"
        print("    Invalid choice, input 'y' or 'n'")


def process(cfg: CFG, original_path: Path):
    while True:
        print("Input the word to test: (Format is 'spaced!')")
        word_str = input("  > ")
        word = spaced_exclam_to_word(word_str)
        print("Is this correct?")
        print(word)
        if ask_yes_no():
            break

    cyktable = make_cyk_table(cfg, word)

    print("Processed CYK table!")
    pretty = cyk_table_to_pretty(cyktable)
    print(pretty)

    has_start_state = cfg.start_variable in cyktable.get_letters(cyktable.final_pos())
    if has_start_state:
        print(
            f"Start variable {cfg.start_variable} is in the final cell, creating parse tree..."
        )
        tree = cyk_table_to_tree(cyktable, cfg)
        print("Parse tree created!!!")
    else:
        print(
            f"Start variable {cfg.start_variable} is missing from the final cell! Did you run CNF on the CFG yet?"
        )
        tree = None

    output_table = path_with_suffix(original_path, "cyk_table")
    output_tree = path_with_suffix(original_path, "cyk_tree").with_suffix(".png")
    write_to_path(output_table, pretty)
    if tree:
        tree.render(output_tree)
    # content = cfg.to_latex()
    # write_to_path(output_path, content)


def make_cyk_table(cfg: CFG, word: tuple[Letter]):
    cyktable = CYKTable(word)
    # do stuff for each cell in table
    for pos in cyktable.iter_positions():
        dest_pos_pairs = cyktable.generate_dest_pairs(pos)
        for dest_pos_pair in dest_pos_pairs:
            # for each cell's possible destination
            # this part is looped for each pair of destinations
            if pos[0] == 1:
                # first row, only single 1-destination, returns letters
                dest_pos = dest_pos_pair[0]
                dest = cyktable[dest_pos]
                dest: Letter  # a letter from the header
                for rule in cfg.rules:
                    if tuple(rule.output_word) != (dest,):
                        continue
                    # found rule that produces the letter in header
                    cyktable.mark_cell(pos, rule.input_letter, dest_pos, dest)

            else:
                # other rows, multiple 2-destinations, returns CYKItem instances, extract Letter from them first
                destA_pos, destB_pos = dest_pos_pair
                destA: set[CYKItem]
                destB: set[CYKItem]
                destA = cyktable[destA_pos]
                destB = cyktable[destB_pos]
                # skip if one of the dest has no variables / is empty
                if len(destA) == 0 or len(destB) == 0:
                    continue
                # each dest can have multiple CYKItems, e.g. A = (X), b = (S, Y)
                for item_pair in itertools.product(destA, destB):
                    required_word = tuple(i.var for i in item_pair)
                    for rule in cfg.rules:
                        if tuple(rule.output_word) != required_word:
                            continue
                        # found rule that produces the letter in header
                        cyktable.mark_cell(
                            pos,
                            rule.input_letter,
                            destA_pos,
                            required_word[0],
                            destB_pos,
                            required_word[1],
                        )
    return cyktable


def cyk_table_to_tree(cyktable: CYKTable, cfg: CFG):
    tree = CFGParseTree((cfg.start_variable,))
    # find the starting CYKItem
    start_item: CYKItem
    start_item = next(
        item
        for item in cyktable[cyktable.final_pos()]
        if item.var == cfg.start_variable
    )
    # find the start node
    start_node = tree.leaves()[0]
    node_item_pairs = [(start_node, start_item)]

    def debug():
        for node, item in node_item_pairs:
            print(node, "==>", item.details())

    for node, item in node_item_pairs:
        output_word = tuple(x[1] for x in item.dest if x[1] is not None)
        tree.branch_word(node, output_word)
        if len(output_word) == 1 and not output_word[0].is_variable:
            # we reached row 1, we should terminate
            continue
        last_added_nodes = tree.last_added_stack[-1]
        # last added nodes should correspond exactly to item.dest
        for new_node, new_tup in zip(last_added_nodes, item.dest):
            # new_tup is a tuple with position and destination letter
            # we need to convert it to a CYK item with its own destination data
            new_pos, new_letter = new_tup
            new_item = next(
                item for item in cyktable[new_pos] if item.var == new_letter
            )
            node_item_pairs.append((new_node, new_item))

    # debug()
    tree.show()
    return tree


# def justify_cyk_table(cyktable: CYKTable):
#     output = []
#     for pos in cyktable.iter_positions():
#         cell = cyktable[pos]
#         if len(cell) == 0:
#             continue
#         output.append(f"Row {pos[0]}, cell {pos[1] + 1}:")
#         messages = set()
#         for item in cell:
#             dest_letters = [x[1] for x in item.dest if x[1] is not None]
#             line = f"  {item.var.name} produces {' '.join(x.name for x in dest_letters)}"
#             messages.add(line)
#         output += sorted(messages)
#     [print(x) for x in output]


def cyk_table_to_pretty(cyktable: CYKTable):
    def value_to_pretty(value):
        if isinstance(value, set):
            if len(value) == 0:
                return "--"
            reduced = set(e.var.name for e in value)
            return ", ".join(sorted(reduced))
        elif isinstance(value, Letter):
            return value.name
        elif value == None:
            return ""
        else:
            raise Exception(f"Unknown shit passed to `value_to_pretty`: {value}")

    pretty_table = []
    for i, row in enumerate(cyktable.rows):
        row_num = cyktable.num_columns - i
        pretty_row = [str(row_num)]
        for element in row:
            pretty_row.append(value_to_pretty(element))
        pretty_table.append(pretty_row)
    pretty_table.append([""] + [x.name for x in cyktable.labels])

    column_widths = []
    for i in range(len(pretty_table[0])):
        column = [row[i] for row in pretty_table]
        column_width = max([len(x) for x in column])
        column_widths.append(column_width)

    output = []
    for row in pretty_table:
        to_join = []
        for width, text in zip(column_widths, row):
            to_join.append(f" {text.rjust(width)} ")
        output.append("|".join(to_join))
    output.insert(len(output) - 1, "=" * len(output[0]))
    return "\n".join(output)

from collections import defaultdict
from treelib import Tree
from anytree import Node, RenderTree, PreOrderIter


def quick_treelib(string_tree: str):
    tree = Tree()
    last_indentation = -1
    parent_map = defaultdict(None)
    last_content = ""
    for line in string_tree.split("\n"):
        if line.strip() == "":
            continue
        this_content = line.strip()
        this_indentation = (len(line) - len(line.lstrip())) // 4
        if this_indentation == 0:
            # root
            tree.create_node(this_content, this_content)
        elif this_indentation == last_indentation + 1:
            # children start
            parent_map[this_indentation] = last_content
            tree.create_node(
                this_content, this_content, parent=parent_map[this_indentation]
            )
        elif this_indentation == last_indentation:
            # same level
            tree.create_node(
                this_content, this_content, parent=parent_map[this_indentation]
            )
        elif this_indentation < last_indentation:
            # end children
            tree.create_node(
                this_content, this_content, parent=parent_map[this_indentation]
            )
        else:
            print(f"{last_content=}")
            print(f"{last_indentation=}")
            print(f"{parent_map=}")
            print(f"{this_content=}")
            print(f"{this_indentation=}")
            raise Exception("Invalid tree!")
        last_content = this_content
        last_indentation = this_indentation
    return tree


def quick_anytree(string_tree: str):
    root_node = Node("Root")
    parent_map = dict()
    last_content = ""
    last_indentation = -1
    last_node = None
    for line in string_tree.split("\n"):
        if line.strip() == "":
            continue
        this_content = line.strip()
        this_indentation = (len(line) - len(line.lstrip())) // 4
        this_node = Node(this_content)
        if this_indentation == 0:
            # root
            root_node = this_node
        elif this_indentation == last_indentation + 1:
            # children start
            parent_map[this_indentation] = last_node
            this_node.parent = parent_map[this_indentation]
        elif this_indentation == last_indentation:
            # same level
            this_node.parent = parent_map[this_indentation]
        elif this_indentation < last_indentation:
            # end children
            this_node.parent = parent_map[this_indentation]
        else:
            print(f"{last_content=}")
            print(f"{last_indentation=}")
            print(f"{last_node=}")
            print(f"{parent_map=}")
            print(f"{this_content=}")
            print(f"{this_indentation=}")
            print(f"{this_node=}")
            raise Exception("Invalid tree!")
        last_content = this_content
        last_indentation = this_indentation
        last_node = this_node
    return root_node

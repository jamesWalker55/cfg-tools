from typing import NamedTuple, Union
from obj.cfg import Letter


# table implementation stolen from fsa-tools-2
class Table:
    def __init__(self, headers: list[str]):
        self.labels = headers
        self.num_columns = len(headers)
        self.rows: list[list]
        self.rows = []
        self.label_index = None  # initialized later
        self._labels_to_index()

    def _labels_to_index(self):
        self.label_index = {}
        for i, label in enumerate(self.labels):
            self.label_index[label] = i

    def __getitem__(self, arg):
        """table lookup, return all matching rows

        table[column name, value] -> list of rows"""
        assert len(arg) == 2
        label, value = arg
        index = self.index_of(label)
        matches = []
        for row in self.rows:
            if row[index] == value:
                matches.append(row)
        if matches:
            return tuple(matches)
        else:
            raise KeyError(f"Can't find value {value} in column {label}.")

    def __repr__(self) -> str:
        return self.__str__()

    def _column_widths(self):
        """return tuple of string width of each column"""
        widths = [0] * self.num_columns
        for row in [list(self.labels)] + self.rows:
            for i in range(self.num_columns):
                width = len(str(row[i]))
                widths[i] = max(width, widths[i])
        return widths

    def __str__(self) -> str:
        CELL_PADDING = " "
        widths = self._column_widths()
        pretty_rows = []

        def generate_pretty(row):
            cells = []
            for width, content in zip(widths, row):
                pretty = str(content).rjust(width)
                cells.append(CELL_PADDING + pretty + CELL_PADDING)
            return "|".join(cells)

        pretty_rows.append(generate_pretty(self.labels))
        pretty_rows.append("=" * len(pretty_rows[0]))
        for row in self.rows:
            pretty_rows.append(generate_pretty(row))
        return "\n".join(pretty_rows)

    def add_row(self, row):
        if len(row) != self.num_columns:
            raise Exception("Given row doesn't have same number of columns as table!")
        self.rows.append(list(row))

    def index_of(self, label):
        """return index of given label"""
        return self.label_index[label]

    def copy_column(self, label=None, index=None):
        """input either column name or column index"""

        def row_get_val(row, index):
            return row[index]

        if label:
            index = self.index_of(label)
        return tuple(map(lambda row, i=index: row_get_val(row, i), self.rows))


class CYKItem(NamedTuple):
    """stores information about a variable, including variable name, destination cells, destination variables

    - var: this variable
    - dest: contains 2 destination data, format for each of them is:

    ```
    (
        table position tuple, e.g. (2, 1),
        variable at that position, e.g. <Letter: U0!>
    )
    ```
    """

    var: Letter
    lookup_args: tuple[int, int]
    dest: tuple[tuple[tuple[int, int], Letter], tuple[tuple[int, int], Letter]]

    def details(self) -> str:
        return f"""<{self.var.name}->{self.dest}>"""

    def __repr__(self) -> str:
        return self.var.name


class CYKTable(Table):
    def __init__(self, word: tuple[Letter]):
        headers = [l for l in word]
        super().__init__(headers)
        num_columns = len(headers)
        for i in range(num_columns):
            new_row = [set() for _ in range(i + 1)] + [None] * (num_columns - i - 1)
            new_row: list[set[CYKItem]]
            self.add_row(new_row)

    @classmethod
    def _value_to_str(cls, value):
        if isinstance(value, set):
            return ", ".join([cls._value_to_str(x) for x in value])
        elif isinstance(value, CYKItem):
            return value.var.name
        elif value is None:
            return "--"
        else:
            return str(value)

    def _column_widths(self):
        """return tuple of string width of each column"""
        widths = [0] * self.num_columns
        for row in [list(self.labels)] + self.rows:
            for i in range(self.num_columns):
                width = len(self._value_to_str(row[i]))
                widths[i] = max(width, widths[i])
        return widths

    def __str__(self) -> str:
        CELL_PADDING = " "
        widths = self._column_widths()
        pretty_rows = []

        def generate_pretty(row, first_col_str):
            cells = []
            for width, content in zip(widths, row):
                pretty = self._value_to_str(content).rjust(width)
                cells.append(CELL_PADDING + pretty + CELL_PADDING)
            return "|".join([first_col_str] + cells)

        for i, row in enumerate(self.rows):
            row_num = self.num_columns - i
            pretty_rows.append(generate_pretty(row, str(row_num).rjust(4)))
        pretty_rows.append("=" * len(pretty_rows[0]))
        pretty_rows.append(generate_pretty(self.labels, "    "))
        return "\n".join(pretty_rows)

    def _lookup_args_to_row_col(self, lookup_args):
        """given the arg (a 2-tuple of str), return the row and column index

        returns "header" as row index if first arg is 0 (getting values from the header)

        also checks for invalid input"""
        assert len(lookup_args) == 2
        assert all(isinstance(x, int) for x in lookup_args)
        row_num, letter_idx = lookup_args
        if row_num == 0:
            assert 0 <= letter_idx < self.num_columns
            return "header", letter_idx
        else:
            row_index = self.num_columns - row_num
            assert 0 <= row_index < self.num_columns
            assert 0 <= letter_idx <= self.num_columns - row_num
            return row_index, letter_idx

    def __getitem__(self, lookup_args) -> Union[set[CYKItem], Letter]:
        """table lookup, return the cell

        table[row number, letter index] -> a cell"""
        row_idx, col_idx = self._lookup_args_to_row_col(lookup_args)
        if row_idx == "header":
            return self.labels[col_idx]
        else:
            return self.rows[row_idx][col_idx]

    def __setitem__(self, lookup_args, value):
        """table lookup, set the cell

        table[row number, letter index] = cell value"""
        row_idx, col_idx = self._lookup_args_to_row_col(lookup_args)
        if row_idx == "header":
            raise Exception("Attempted to set value at header!")
        else:
            self.rows[row_idx][col_idx] = value

    def generate_dest_pairs(self, lookup_args):
        """given a cell, return a generator that gives all possible pairs of destinations below its row

        ```
        >>> list(_generate_dests([3, 1]))  # for a table with at least 4 columns/rows
        [ ((1, 1), (2, 2)),
          ((2, 1), (1, 3)) ]
        >>> list(_generate_dests([4, 1]))  # for a table with at least 5 columns/rows
        [ ((1, 1), (3, 2)),
          ((2, 1), (2, 3)),
          ((3, 1), (1, 4)) ]
        ```
        """
        # check input for errors
        self._lookup_args_to_row_col(lookup_args)
        row_num, letter_idx = lookup_args
        assert row_num != 0  # header row doesn't have destinations
        if row_num == 1:
            yield ((0, letter_idx),)
        else:
            for i in range(1, row_num):
                yield (i, letter_idx), (row_num - i, letter_idx + i)

    def final_pos(self):
        return (self.num_columns, 0)

    def mark_cell(
        self,
        pos: tuple[int, int],
        variable: Letter,
        dest_pos_1: tuple[int, int],
        dest_var_1: Letter,
        dest_pos_2: tuple[int, int] = None,  # for first row, they have 1 dest only
        dest_var_2: Letter = None,
    ):
        assert all(isinstance(x, Letter) for x in (variable, dest_var_1)) and all(
            isinstance(x, tuple) for x in (pos, dest_pos_1)
        )
        if dest_var_2 or dest_pos_2:
            assert isinstance(dest_var_2, Letter)
            assert isinstance(dest_pos_2, tuple)
        item = CYKItem(
            var=variable,
            lookup_args=pos,
            dest=(
                (dest_pos_1, dest_var_1),
                (dest_pos_2, dest_var_2),
            ),
        )
        self[pos].add(item)

    def iter_positions(self):
        """return an iterator that iterates through all positions in the table, starting from bottom left"""
        for row_num in range(1, self.num_columns + 1):
            for letter_idx in range(self.num_columns - row_num + 1):
                yield row_num, letter_idx

    def get_letters(self, pos: tuple[int, int]):
        cell = self[pos]
        cell_letters = set(item.var for item in cell)
        return cell_letters

# CFG Tools

A set of tools for processing context-free grammars.

Required modules:

- `anytree`

## How to use

```
main.py INPUT_FILE
main.py examples/cfg03.txt
```

This tool takes a single text file as input. The text file describes the CFG and lists actions to perform on the CFG. An input file looks like this:

```
# this is a comment

# state the input format with "format INPUT_FORMAT"
# we will use the "char" format to describe our CFG

format char

# state the actions to perform with "action ACTION1 ACTION2 ..."
# "cnf" - convert the input CFG into CNF (Chomsky normal form)

action cnf

# begin describing the CFG, we're using the "char" format

start S

S -> X
X -> e | 0X1
```

After running the above file, it generates two text files for the `cnf` action:

> The final CNF:
> 
> ```
> start S
> 
> U1 -> 1
> X0 -> X U1 | 1
> U0 -> 0
> X -> U0 X0
> S -> U0 X0 | e
> 
> ... (truncated for brevity)
> ```
> 
> The steps taken to produce the CNF:
> 
> ~~~
> Initial CFG
> 
> ```
> start S
> 
> X -> 0X1 | e
> S -> X
> ```
> 
> START
> 
> ```
> start S
> 
> X -> 0X1 | e
> S -> X
> ```
> 
> ... (truncated for brevity)
> 
> TERM
> 
> ```
> start S
> 
> U1 -> 1
> X0 -> X U1 | 1
> U0 -> 0
> X -> U0 X0
> S -> U0 X0 | e
> ```
> ~~~

Another example:

```
# using the "spaced" input format
format spaced

# use cyk to check if a word is accepted by this cfg
action cyk

# describe the cfg
start S

U1 -> 1
X0 -> X U1 | 1
U0 -> 0
X -> U0 X0
S -> U0 X0 | e
```

When running this file, the console prompts you to input a word to test:

```
(pda-tools) PS D:\Programming\pda-tools> ./main.py .\examples\test_cnf.txt

Parsing input file... 
Parsing success! 
Cyk: Starting...
Input the word to test: (Format is 'spaced!')
  > 0 0 1 1 
Is this the word you want to test? (y/n) 
(<0>, <0>, <1>, <1>)
  > y 
Processed CYK table! 
 4 | S, X |      |        |
 3 |   -- |   X0 |        |
 2 |   -- | S, X |     -- |
 1 |   U0 |   U0 | U1, X0 | U1, X0
===================================
   |    0 |    0 |      1 |      1
Start variable S! is in the final cell, creating parse tree...
root
└── S!
    ├── U0!
    │   └── 0
    └── X0!
        ├── X!
        │   ├── U0!
        │   │   └── 0
        │   └── X0!
        │       └── 1
        └── U1!
            └── 1
Parse tree created!!!
Warning: using box for unknown shape plain
Cyk: Success!
```

This produces two files:

> The CYK table:
> 
> ```
>  4 | S, X |      |        |        
>  3 |   -- |   X0 |        |        
>  2 |   -- | S, X |     -- |        
>  1 |   U0 |   U0 | U1, X0 | U1, X0 
> ===================================
>    |    0 |    0 |      1 |      1 
> ```
> 
> Diagram of the parse tree:
> 
> - TODO: Add image of the parse tree here

## Implemented actions

These are the actions I implemented:

- `latex`: Express the input CFG using LaTeX math symbols.
- `cnf`: Convert the input into Chomsky normal form, output the final CFG and the steps taken.
- `pda`: Convert the input into a pushdown automata for use in [FSA Tool 2](https://github.com/jamesWalker55/fsa-tools-2).
- `interactive`: Interactively apply rules to the starting variable. A parse tree diagram is generated upon exiting.
- `cyk`: Check if a word is accepted by the input CFG using the CYK algorithm. Produces a CYK table and a parse tree image.
  - Note: The input must be in Chomsky normal form (use the `cnf` action for this).
- `clone`: Clone the input to a new file.
- `clone_char`: Clone the input to a new file, using the "char" format.
- `clone_spaced`: Clone the input to a new file, using the "spaced" format.
- `clone_spaced!`: Clone the input to a new file, using the "spaced!" format.

## Input format

The input format is as follows:

- one line stating the starting variable (optional, only required for certain actions)
  - `start STARTING_VARIABLE`
- all other lines are CFG rules, the formats `char`, `spaced`, `spaced!` interpret these lines differently
  - `VARIABLE -> WORD1 | WORD2 | WORD3 | ...`

There are 3 input formats: `char`, `spaced`, `spaced!`. They affect how an input word split into **letters** and **variables**.

_(see `tools/cfg_parse.py` for their implementation)_

- `char`: The input word is split by character; uppercase letters are treated as variables, all other characters are treated as letters.
  - e.g. `abXab` is parsed into the letters `a` and `b`, the variable `X`, then the letters `a` and `b`.
- `spaced`: The input word is split by spaces; any string that contains uppercase letters is treated as a variable, all other strings are treated as letters.
  - e.g. `lo X1 lo hi` is parsed into the letter `lo`, the variable `X1`, then the letters `lo` and `hi`.
- `spaced!`: The input word is split by spaces; any string that ends with an exclamation mark `!` is treated as a variable, all other strings are treated as letters.
  - e.g. `lo! X1! lo hi` is parsed into the variables `lo` and `X1`, then the letters `lo` and `hi`.

The distinction between letters are variables is important.

- Variables exist on the left-hand side of a rule `X -> 10X0 | 0`, and can be replaced with a sequence of letters or variables.
- Letters are final, they cannot be replaced with anything.
- Most of the actions like `cnf`, `pda`, `interactive`, `cyk` treat variables and letters differently

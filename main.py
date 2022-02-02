import argparse
import tools.fromtext
import tools.cfg_parse
import processors_cfg.clone
import processors_cfg.latex
import processors_cfg.interactive
import processors_cfg.cnf
import processors_cfg.pda
import processors_cfg.cyk
from pathlib import Path

# get cmd arguments
ap = argparse.ArgumentParser(
    description="Processes a *.txt file containing graph information."
)
ap.add_argument(
    "path", metavar="txt_path", type=Path, help="Path to the *.txt file to process"
)
cmd_args = ap.parse_args()

# load file
with open(cmd_args.path, encoding="utf8") as f:
    full_text = f.read()

parse_lines, meta_lines = tools.fromtext.text_to_lines_lists(full_text)
meta_data = tools.fromtext.parse_meta_lines(meta_lines)

# quit if meta data isn't enough
if len(meta_data["format"]) == 0:
    print(f"Format is unspecified! Include `format xxx` in the text file.")
    quit()

# define parsers and processors
if meta_data["mode"][0] == "cfg":
    parsers = {
        "char": lambda pl: tools.cfg_parse.lines_to_cfg(
            pl, tools.cfg_parse.chars_to_word
        ),
        "spaced": lambda pl: tools.cfg_parse.lines_to_cfg(
            pl, tools.cfg_parse.spaced_to_word
        ),
        "spaced!": lambda pl: tools.cfg_parse.lines_to_cfg(
            pl, tools.cfg_parse.spaced_exclam_to_word
        ),
    }
    processors = {
        "clone": processors_cfg.clone.process,
        "clone_char": lambda cfg, path: processors_cfg.clone.process(cfg, path, "char"),
        "clone_spaced": lambda cfg, path: processors_cfg.clone.process(
            cfg, path, "spaced"
        ),
        "clone_spaced!": lambda cfg, path: processors_cfg.clone.process(
            cfg, path, "spaced!"
        ),
        "latex": processors_cfg.latex.process,
        "interactive": processors_cfg.interactive.process,
        "cnf": processors_cfg.cnf.process,
        "pda": processors_cfg.pda.process,
        "cyk": processors_cfg.cyk.process,
    }
elif meta_data["mode"][0] == "pda":
    parsers = {}
    processors = {}
else:
    raise tools.fromtext.MetaError(f"Unknown mode {meta_data['mode']}")

# parse input lines
print("Parsing input file...")
try:
    parse_fn = parsers[meta_data["format"][0]]
except KeyError:
    raise tools.fromtext.MetaError(
        f"Unknown format {meta_data['format'][0]} for mode {meta_data['mode']}"
    )

parsed_thing = parse_fn(parse_lines)
print("Parsing success!")

for action in meta_data["action"]:
    action = action.lower()
    try:
        action_fn = processors[action]
    except KeyError:
        print(f"Unknown action '{action}' for mode {meta_data['mode']}")
        continue
    action: str
    print(f"{action.capitalize()}: Starting...")
    action_fn(parsed_thing, cmd_args.path)
    print(f"{action.capitalize()}: Success!")

# print(parsed_thing)
# print(parsed_thing.rules)

# print(parsed_thing.min_format())
# print(parsed_thing.to_latex())
# a = parsed_thing

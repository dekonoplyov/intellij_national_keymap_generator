import argparse
import json
from typing import Dict
from xml.etree import ElementTree
import os


def get_keymap(path_to_file: str) -> ElementTree:
    print("parsing keymap:", path_to_file)
    return ElementTree.parse(path_to_file)


class Replacement:
    def __init__(self, replacement: str, add_modifiers: str):
        self.replacement = replacement
        self.add_modifiers = add_modifiers.lower()  # modifiers should be in lower


def get_replacements(path_to_file: str) -> Dict[str, Replacement]:
    print("parsing replacement config:", path_to_file)
    with open(path_to_file) as json_file:
        config = json.load(json_file)
        replacements = {}
        for item in config:
            add_modifiers = item["add_modifiers"] if "add_modifiers" in item else ""
            replacements[item["key"]] = Replacement(item["replacement"],
                                                    add_modifiers)
        return replacements


def update_keymap(keymap: ElementTree, replacements: Dict[str, Replacement]):
    print("updating keymap")
    actions = keymap.getroot()
    updated_shortcuts_cnt = 0
    for action in actions:
        for shortcut in action:
            if shortcut.tag != "keyboard-shortcut":
                continue

            should_update = get_first_key(shortcut) in replacements
            if has_second_keystroke(shortcut):
                should_update = should_update or (get_second_key(shortcut) in replacements)

            if should_update:
                updated_shortcuts_cnt += 1
                update(shortcut, replacements)

    print(updated_shortcuts_cnt, "shortcuts were updated")


def update(shortcut: ElementTree.Element, replacements: Dict[str, Replacement]):
    if get_first_key(shortcut) in replacements:
        shortcut.attrib["first-keystroke"] = update_shortcut(shortcut.attrib["first-keystroke"],
                                                             replacements[get_first_key(shortcut)])

    if has_second_keystroke(shortcut) and (get_second_key(shortcut) in replacements):
        shortcut.attrib["second-keystroke"] = update_shortcut(shortcut.attrib["second-keystroke"],
                                                              replacements[get_second_key(shortcut)])


def update_shortcut(shortcut: str, replacement: Replacement) -> str:
    """
    >>> update_shortcut("meta control EQUALS", Replacement("SEMICOLON", "shift"))
    'meta control shift SEMICOLON'

    >>> update_shortcut("meta control EQUALS", Replacement("1", ""))
    'meta control 1'
    """
    tokens = shortcut.split()
    tokens.pop()  # remove key
    tokens = set(tokens)

    add_mods = replacement.add_modifiers.split(" ")

    for mod in add_mods:
        tokens.add(mod)

    result = []

    mods = ["meta", "control", "shift", "alt"]
    for mod in mods:
        if mod in tokens:
            result.append(mod)

    result.append(replacement.replacement)

    return " ".join(result)


def get_first_key(shortcut: ElementTree.Element) -> str:
    return shortcut.attrib["first-keystroke"].split()[-1]


def has_second_keystroke(shortcut: ElementTree.Element) -> bool:
    return "second-keystroke" in shortcut.attrib


def get_second_key(shortcut: ElementTree.Element) -> str:
    return shortcut.attrib["second-keystroke"].split()[-1]


def parse_arguments():
    parser = argparse.ArgumentParser()
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-k", "--keymap", type=str,
                             help="path to keymap to process")
    input_group.add_argument("-d", "--directory", type=str,
                             help="path to directory with keymaps")

    parser.add_argument("-r", "--replacements", type=str, required=True,
                        help="path to replacements config")

    parser.add_argument("-o", "--output", type=str, required=True,
                        help="path to output file or dir")
    return parser.parse_args()


def verify_and_create_output_dir(output: str):
    if not os.path.exists(output):
        print("creating output dir:", output)
        os.mkdir(output)
    if not os.path.isdir(output):
        raise RuntimeError("output should be dir path when processing whole dir")


def process_keymap(keymap: str, replacements: str, output: str):
    keymap = get_keymap(keymap)
    replacements = get_replacements(replacements)
    update_keymap(keymap, replacements)
    print("writing updated keymap to:", output)
    keymap.write(output)


def main():
    args = parse_arguments()
    if args.keymap is not None:
        process_keymap(args.keymap, args.replacements, args.output)
    else:
        print("start processing directory:", args.directory)
        verify_and_create_output_dir(args.output)
        for keymap in os.listdir(args.directory):
            if not keymap.endswith(".xml"):
                continue

            keymap_path = os.path.join(args.directory, keymap)
            output = os.path.join(args.output, keymap)
            process_keymap(keymap_path, args.replacements, output)


if __name__ == "__main__":
    main()

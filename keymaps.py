import argparse
import json
from typing import Dict
from xml.etree import ElementTree


def get_keymap(path_to_file: str) -> ElementTree:
    print("parsing keymap:", path_to_file)
    return ElementTree.parse(path_to_file)


class Replacement:
    def __init__(self, replacement: str, add_modifiers: str):
        self.replacement = replacement
        self.add_modifiers = add_modifiers.lower() # modifiers should be in lower


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
    tokens.pop() # remove key
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
    parser.add_argument("-k", "--keymap", type=str, required=True,
                        help="path to keymap to process")
    parser.add_argument("-r", "--replacements", type=str, required=True,
                        help="path to replacements config")
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="path to output file")
    return parser.parse_args()


def main():
    args = parse_arguments()
    keymap = get_keymap(args.keymap)
    replacements = get_replacements(args.replacements)
    update_keymap(keymap, replacements)
    print("writing updated keymap to:", args.output)
    keymap.write(args.output)

if __name__ == "__main__":
     main()

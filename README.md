# intellij_national_keymap_generator

```
python3 keymaps.py -k path/to/keymap.xml -r config/mac_german.json -o output.xml
```

### Options  
-k, --keymap path to keymap to process  
-r, --replacements path to replacements config  
-o, --output path to output file  

### Config structure
Json list with replacement dict:  
- "key": key to replace
- "replacement": replacement for key
- "add_modifiers": modifiers to add


```(json)
[
    {"key": "SEMICOLON", "add_modifiers": "shift", "replacement": "COMMA"},
    ...
]
```




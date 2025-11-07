[ ] CSVProcessor.process_file() account for different styles when rewriting files. check quotes + separators while parsing each file originally, and set write style accordingly? 

[ ] Have setup option booleans live in a single place. Decisions like falling back to a default set of columns if inputs were insufficient are definitely a config thing, but decisions like renaming hypenated names in 1 or 2 steps could be in the processor or continue to live in the config class. Seems like the decision is between keeping a DEFAULT_PREFIX and SELECTED_PREFIX field in config, or having a version in each, with the config handing off the input or None, and processor providing a default if needed. As i write it out, i like the first option more.

[ ] 


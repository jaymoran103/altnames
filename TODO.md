# LOGIC

[ ] Revisit the approach for handling buggy (CM Generated) headers

[ ] Check for file issues when processing arguments, maybe again right before using

[ ] Consider exempting titles and connecting words when tokenizing names.

[X] implement autocolumns feature from og version?

[X] case sensitivity for column names?

[X] CSVProcessor.process_file() account for different styles when rewriting files using csv.Sniffer

# DOCUMENTATION / REFACTORS

[ ] i'll want a better program name than main.py once this is a standalone tool

[ ] Add proper README

[ ] are docstrings crucial if my comments already do that? linter seems to think so

[ ] replace handler methods with lambda statements when possible, a majority are one line now anyway

# FUTURE FEATURES

[ ] down the road, could add a '--savemap/--usemap' feature to save name mappings for consistent mapping between runs, and undoing anonymization. Not relevant to my current use case

[ ] add --dryrun option? not critical since we're renaming new files anyway. Is it helpful to make direct renaming an option?
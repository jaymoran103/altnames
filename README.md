# NameSwap

NameSwap is a Python tool for anonymizing CSV data, replacing name strings with randomized alternatives. NameSwap maintains a map of renamings, ensuring that swaps are consistent across a data set, and cross-checking operations will peform as they would for the original data.

## Features

- **Batch Processing**: Process multiple files with a single command
- **Session Saving**: Save a mappings file to use the same renamings over multiple runs.
- **Flexible Parsing**: Tokenizes name strings, ensuring cells containing mutliple names will handle each individually. Can be toggled off
- **Format Preservation**: Maintains CSV structure, quoting style, and delimiters
- **Smart Name Detection**: Can automatically detects name columns, in addition to manually specified headers. Matches headers regardless of capitalization.
- **Deterministic Mapping**: Supports use of seeds for consistent name replacements across runs, regardless of mapping file use. See `Seed Selection` section for more detials.


## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/nameswap.git
cd nameswap

# Install dependencies. For a self-contained version that includes a name bank, contact me with the info below!
pip install faker
```

## Quick Start

```bash
# Basic usage: anonymize names in specific columns
python3 nameswap.py -f data.csv -c FirstName -c LastName

# Process multiple files at once
python3 nameswap.py -f file1.csv -f file2.csv -f file3.csv -c Name

# Specify a file to save or load mappings. 
python3 nameswap.py -f data.csv -c Name -m mappingfile.json

# Use auto-detection to find name columns
python3 nameswap.py -f data.csv --autocolumns


```

## Usage

### Basic Syntax

```bash
python3 nameswap.py [-f <file>] [-c <column>] [options]
```
### Input Flags

- `-f <file>` - Specify CSV file(s) to process (required, can use multiple times)
- `-c <column>` - Specify column(s) to anonymize (can use multiple times)
- `-p <prefix>` - Set output file prefix (default: "renamed")
- `-s <seed>` - Set seed for deterministic name generation
- `-m <mappings.json>` - Specify mapping file for saving and loading session data 

### Option Flags

- `--help` - Display basic help information
- `--menu` - Display detailed menu with all flags and options
- `--skip` - Skip user confirmation step before processing
- `--autocolumns` - Auto-detect columns containing "name"
- `--defaultcolumns` - Apply default column set
- `--renamewholecells` - Apply renaming to entire cells without parsing (use with caution)

## Advanced Usage

### Session Saving

By default, NameSwap picks new mappings for names each time it runs. Using -m <filename.json> saves mappings in a json file, allowing consistent use across any number of runs. If the specified file exists at runtime, the mappings and settings within will be applied to the run, with any new mappings appended to the file to keep it current. If the specified file does not exist at runtime, it is created after files are processed.

**Note**: If you're working with sensitive data, exercise caution while handling the mapping file. Possession of this file enables the reversal of the anonymization process, potentially exposing original names and relationships in your CSV files.

### Seed Selection

NameSwap picks names randomly by default. Using -s <seedtext> ensures a consistent queue of names to assign while processing a csv batch. If the same sequence of names is provided as input, the same name mappings will occur. This is helpful for comparing results across file batches, but relies on the same sequence of given inputs to generate consistent results.

### Whole Cell Renaming

By default, NameSwap parses names intelligently (handling spaces, commas, hyphens). This ensures cells containing multiple names ("Lastname, FirstName" or "Name Hypen-Ated") are handled accordingly, with syntax and contextual relationships preserved.

To disable this feature, use `--renamewholecells`. 

```bash
python3 nameswap.py -f data.csv -c "Name" --renamewholecells
```
**Note**: Use this feature with caution. This flag treats entire cells as single names, and may mean the loss of internal syntax or relationships between name components, depending on your use case.

### File Naming

Nameswap adds the prefix "renamed-" to output files by default. Using -p <prefixtext> results in output

data.csv -> prefixtext-data.csv 

The hyphen is added automatically, so a file can't be overwritten by itself, but repeated use will mean overwriting the renamed version as long as the prefix and filename remain the same.
```bash
python3 nameswap.py -f data.csv -c "Name" --skip
```
**Note**: Use this feature with caution. The confirmation step prints the files and columns set to be processed, and skipping could lead to the overwriting or problematic modification of output files. As renamed files are written as copies with a prefix, original files should be difficult to overwrite by accident.

### Skipping Confirmation

By default, NameSwap prints its configration information and waits for manual approval to execute. Using --skip makes execution happen as soon as inputs are verified, only stopping if inputs are insufficient or a file exception occurs. Use with caution if you need to keep recent outputs.

## Author

Created by Jay Moran in November 2025.
jaymorandev@gmail.com
github.com/jaymoran103
linkedin.com/in/jaymorandev
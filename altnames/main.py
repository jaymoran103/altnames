import sys
import time
import csv
import random
from typing import Dict,Set,TextIO
from textwrap import dedent
from faker import Faker


#Help text for command line usage
HELP_TEXT = dedent("""
    This program renames names in specified columns of CSV files, generating safe alternatives for demos. 
    It requires command line arguments to specify the target files and columns for renaming.
    Each input requires a preceding flag to indicate its type.
    
    Basic usage: main.py [-f <file>] [-c <column>]
    (Extra -f and -c flags can be provided to add more flags and columns)
    
    For more options: main.py --menu 
""")

# Detailed menu text for command line usage
MENU_TEXT = dedent("""
    Usage: main.py [-f <file>] [-c <column>] [other flags] [options]
    Note: Each input requires a preceding flag to indicate its type. 

    Input flags:
        [-f <file>]   - file(s) to process. Requires at least one file
        [-c <column>] - column(s) to rename. If none are provided, a default set is applied.
        [-p <prefix>] - optionally specify the prefix for renamed files. defaults to 'renamed-')
        [-s <seed>]   - optionally specify a seed for deterministic mappings. (same inputs with same seed yield same outputs)

    Option flags:
        [--help]             - display basic help information
        [--menu]             - display this menu information
        [--skip]             - skip confirmation step before processing (use with caution)
        [--defaultcolumns]   - apply default columns if none were specified
        [--renamewholecells] - apply renaming to entire cells, instead of splitting by spaces and commas. (use with caution)
        [--warnmaxattempts]  - warn if max attempts to generate unique names is reached (may indicate high name collision rate)

        see documentation for more details on each flag and option, especially -s and --renamewholecells
""")

# Renamer class for generating and storing safe names
class Renamer:

    # Initializes the Renamer with a seed for deterministic name generation.
    def __init__(self, seed: str, max_attempts: int = 25, warn_on_max_attempts: bool = False):
        self.max_attempts = max_attempts
        self.warn_on_max_attempts = warn_on_max_attempts
        self.mappings: Dict[str, str] = {}
        self.used_names: Set[str] = set()

        # Generate random seed if none specified
        if seed is None:
            seed = random.randint(0,100)
            #print(f"generating seed in Renamer: {seed}")
            
        # Set up Faker with seed
        self.fake = Faker()
        Faker.seed(seed)

    # Generates or retrieves a safe name for the given original name.
    def get_safe_name(self, original:str):

        # Return empty or whitespace-only names.
        if not original or not original.strip() or original is None:
            return original
            
        # Strip whitespace for consistent mapping, return existing mapping if present
        original = original.strip()
        if original in self.mappings:
            return self.mappings[original]
        
        # Try to generate a unique name.
        for attempt in range(self.max_attempts):

            # Generate a name, storing the mapping if its unique. Otherwise 
            candidate = self.fake.first_name()
            if candidate not in self.used_names:
                self.mappings[original] = candidate
                self.used_names.add(candidate)
                return candidate

        # If attempts fail, add number suffix to ensure uniqueness
        base_name = self.fake.first_name()
        counter = len(self.used_names)
        candidate = f"{base_name}{counter}"
        
        # Store new mapping
        self.mappings[original] = candidate
        self.used_names.add(candidate)

        # Warn user if max attempts were reached
        if self.warn_on_max_attempts:
            print(f"Max attempts reached ({attempt}). Assigned unique name '{candidate}' for original name '{original}'.")

        return candidate


# Configuration class to handle command-line arguments for inputs and options
class Configuration:

    # Initializes the Configuration with default settings, and maps flags and options to their handling functions.
    def __init__(self):
        self.argument_count = -1 # Sentinel value, set whenever processing occurs

        #Inputs to collect
        self.files = set()
        self.columns = set()
        self.selected_prefix = None
        self.selected_seed = None

        #Booleans, some settable by option flags
        self.skip_confirmation_step = False
        self.use_default_columns_if_none_specified = True
        self.auto_detect_columns = False
        self.rename_whole_cells = False  #Applies renaming function to whole cells. For formats with multiple names in a cell ("First Last", "Last, First" "Hyphen-ated") this can lead to inconsistent outputs, and should be applied with caution
        self.warn_max_attempts = False
        self.applied_default_columns = False #Toggled for accurate print confirmation of what happens during config

        #Default values, to apply as needed
        self.default_prefix = "renamed"
        self.default_columns = ["First Name","Last Name","Preferred Name","Camper"]
        #self.generic_default_columns = ["Name","Full Name","First Name","Last Name","Preferred Name","Nickname"] #Truly generic version for defaults. Not relevant to my use case

        # Map command-line flags to their handler functions
        self.flag_mappings = {
            "-f" : self.handle_flag_file,
            "-c" : self.handle_flag_column,
            "-p" : self.handle_flag_prefix,
            "-s" : self.handle_flag_seed
        } 
        
        # Map command-line options to their handler functions
        self.option_mappings = {
            "--help" : self.handle_option_help,
            "--menu" : self.handle_option_menu,
            "--skip" : self.handle_option_skip, 
            "--defaultcolumns" : self.handle_option_defaultcolumns,
            "--renamewholecells" : self.handle_option_renamewholecells,
            "--warnmaxattempts" : self.handle_option_warnmaxattempts,
            "--autocolumns" : self.handle_option_autocolumns
        }

    # Handler for the '-f' flag adds input files for processing
    def handle_flag_file(self,path:str):
        self.files.add(path) 
    
    # Handler for the '-c' flag adds target columns for renaming
    def handle_flag_column(self,col:str):
        self.columns.add(col) 
    
    # Handler for the '-p' flag sets the output file prefix. 
    def handle_flag_prefix(self,prefix:str):
        self.selected_prefix = prefix

    # Handler for the '-s' flag sets the name generation seed.
    def handle_flag_seed(self,seed:str):
        self.selected_seed = seed

    # Handler for the '--menu' option – prints usage information and exits.
    def handle_option_menu(self):
        print(MENU_TEXT)
        self.autostop_warning("--menu")
        exit(0)

    # Handler for the '--help' option to display help information and exit.
    def handle_option_help(self):
        print(HELP_TEXT)
        self.autostop_warning("--help")
        exit(0)

    # Warns user if extra arguments were provided when using a flag that stops execution
    def autostop_warning(self,flag:str):
        if self.argument_count > 1:
            extras = self.argument_count - 1
            plural = "s were" if extras != 1 else " was"
            print(f"Note: {extras} extra argument{plural} found, but {flag} stops execution.\nTo continue, remove {flag}.")
    
    # Handler for the '--skip' option to bypass confirmation step
    def handle_option_skip(self):
        self.skip_confirmation_step = True

    # Applies default columns to the configuration
    def handle_option_defaultcolumns(self):
        self.columns.update(self.default_columns)
        self.applied_default_columns = True

    # Applies renamer to whole name strings, not tokenizing to catch spaces or special characters.
    def handle_option_renamewholecells(self):
        self.rename_whole_cells = True
    
    # Enables warning when max attempts to generate unique names is reached
    def handle_option_warnmaxattempts(self):
        self.warn_max_attempts = True

    # Enables automatic detection of columns, based on common names
    def handle_option_autocolumns(self):
        self.auto_detect_columns = True

    # Processes command-line arguments to configure the application.
    def process_args(self,arg_queue:list):

        self.argument_count = len(arg_queue)

        # Pop arguments from queue, treating as flags, options, or inputs
        while len(arg_queue) > 0:
            current_arg = arg_queue.pop(0)

            #Catch input flags, using the following argument as their input
            if current_arg in self.flag_mappings:
                #If no argument follows the flag, reject
                if len(arg_queue) == 0:
                    print(f"caught input flag ({current_arg}) without an argument following. Exiting for safety")
                    exit(1)

                #If an argument follows the flag, pop it and use as input for the flag function
                next_arg = arg_queue.pop(0)
                self.flag_mappings[current_arg](next_arg)

            #Catch option flags, calling their relevant function
            elif current_arg in self.option_mappings:
                self.option_mappings[current_arg]()

            else:
                #Catch unrecognized inputs, defaulting to handling as input files
                #print(f"argument '{current_arg}' wasn't a recognized flag or option. Handling as input file (-f)")
                #self.flag_mappings["-f"](current_arg)

                print(f"currently no support for argument: '{current_arg}' without a preceding flag. Exiting for safety. run with flag --help or --menu for more information")
                exit(1)

    # Scans all headers in the input files, adding them to target columns if they match common name patterns
    def detect_columns(self,target_columns:set, input_files:set):
        detected_columns = set()
        #Iterate through input files
        for filepath in input_files:

            try:
                #Open file and read headers. skip if no headers found
                with open(filepath, 'r', newline='', encoding='utf-8-sig') as infile:
                    reader = csv.DictReader(infile)
                    if not reader.fieldnames:
                        continue

                    #Check each header for common name patterns
                    for header in reader.fieldnames:
                        l_header = header.lower()

                        #add matches to detected columns
                        #if l_header == "name" or "name" in l_header.split():
                        if "name" in l_header: #more aggressive check, risks catching false positives like 'tournament'
                            detected_columns.add(header)

            except FileNotFoundError:
                print(f"Warning: file '{filepath}' not found for auto column detection. Skipping.")
            except Exception as e:
                print(f"Warning: error reading '{filepath}' - {e}")

        return detected_columns


    #Finish setup step, applying defaults where relevant
    #TODO Check file validity here, reporting issues / removing references in advance
    def finish_setup(self):

        if self.default_columns:
            print(f"Added default columns: {sorted(self.default_columns)}")

        #Apply auto-detected columns if enabled
        if self.auto_detect_columns:
            detected_columns = self.detect_columns(self.columns,self.files)
            if detected_columns:
                print(f"Auto-detected columns: {sorted(detected_columns)}")
                self.columns.update(detected_columns)

        #Apply default columns if none were specified and fallback is enabled
        if not self.columns and self.use_default_columns_if_none_specified:
            print("No columns specified, applying default columns.")
            self.handle_option_defaultcolumns()

        #Apply default prefix if none was specified
        if self.selected_prefix is None:
            print(f"No prefix specified, applying default prefix '{self.default_prefix}'.")
            self.selected_prefix = self.default_prefix

    # Validates the current configuration to ensure inputs are valid and ready to use. 
    # This should either succeed or fail. Any amending of inputs should happen in the preceding setup step.
    def validateConfig(self):
        if not self.files:
            print("No files specified. Use -f <file> to add files.")
            return False
        if not self.columns:
            print("No columns specified. Use -c <column> to add columns.")
            return False
        return True

    # Reports the current configuration to the user, enabling them to confirm that the listed settings are correct
    def reportReady(self):
        print("\nReady to start with the following configuration:")
        print(f"Files: {sorted(self.files)}")
        print(f"Columns: {sorted(self.columns)}")
        print(f"Prefix: {self.selected_prefix}")
        if self.selected_seed is not None:
            print(f"Seed: {self.selected_seed}")
        print()

    # Enables the user to confirm
    def userConfirm(self):
        #Get user input, rejecting anything other than ""
        response = input("Press ENTER to continue, add any character and press ENTER to cancel: ")
        if response == "":
            return True
        else:
            print("Operation cancelled by user.")
            return False

# CSVProcessor class for processing CSV files and replacing names in specified columns.
class CSVProcessor:

    # Initializes the CSVProcessor with the given configuration and renamer.
    def __init__(self, config: Configuration, renamer: Renamer):
        self.renamer = renamer
        self.target_files = config.files
        self.given_prefix = config.selected_prefix
        self.lowercase_columns = {col.lower(): col for col in config.columns} #store columns in lowercase for standardized comparison
        self.rename_whole_cells = config.rename_whole_cells

    # Starts the processing of all target files.
    def start_processing(self):
        for input_file in sorted(self.target_files):
            output_file = f"{self.given_prefix}-{input_file}"
            print(f"Processing {input_file} -> {output_file}",end=" | ")#FUTURE - give a warning if file had no matching columns to rename?

            try:
                self.process_file(input_file, output_file)
                print("Success")
            except Exception as e:
                # print(f"Error: {e}. Skipping")
                print(f"Error: {e}")
            

    #Generate renamed row by applying renaming function to target columns
    def rename_row_columns(self,row:dict,target_columns:list[str]):
        for col in target_columns:
            #If row has a non-empty value for the target column, replace with output of renaming function
            if row[col]:
                row[col] = self.apply_renaming(row[col])

    #iterate through input file, replacing names in target columns and writing to output file.
    def process_file(self, input_path: str, output_path: str):
        try:
            with open(input_path, 'r', newline='', encoding='utf-8-sig') as infile:
                
                #Detect dialect for file writing
                detected_dialect = self.detect_dialect(infile)

                # Create CSV reader for input file
                reader = csv.DictReader(infile)

                #Skip files with no headers, something went wrong
                if not reader.fieldnames:
                    raise ValueError("No headers found.")

                # Write renamed file
                self.write_renamed_file(output_path,reader,detected_dialect)

        #Catch file errors to return a warning string, otherwise return None for success
        except FileNotFoundError:
            #return f"Error: file not found."
            raise FileNotFoundError(f"input file not found")

        except Exception as e:
            # return f"Error: {e}."
            raise RuntimeError(e)
        return None

    # Check input file dialect for proper writing
    def detect_dialect(self,infile: TextIO):
        #sample initial characters for dialect detection, then reset file pointer
        sample = infile.read(1024)
        infile.seek(0)  
        #Attempt to detect dialect, defaulting to excel if detection fails
        try:
            return csv.Sniffer().sniff(sample)
        except csv.Error:
            return csv.excel

    # Write the renamed CSV file to the output path. Returns str indicating warning, otherwise None for success
    def write_renamed_file(self,output_path:str, reader:csv.DictReader, detected_dialect:csv.Dialect) -> str:
        
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:

            #Compare present headers to config columns, building list of target columns to rename
            target_columns = self.detect_target_columns(reader)

            # If no columns matched, send a warning back instead of silently writing unmodified file
            if not target_columns:
                raise ValueError("No name columns to modify.") 

            #Set up writer with same fieldnames as reader, then write header
            writer = csv.DictWriter(
                outfile,
                fieldnames=reader.fieldnames,
                dialect=detected_dialect
            )
            writer.writeheader()
            
            #iterate through rows, applying renaming function
            for row in reader:
                self.rename_row_columns(row,target_columns)

                # Write row with replaced names
                writer.writerow(row)
        return None
            
 
    #Compare present headers to config columns, building list of target columns to rename
    def detect_target_columns(self,reader:csv.DictReader):
        target_columns = []
        for header in reader.fieldnames:
            if header.lower() in self.lowercase_columns: #checking in standardized lower case
                target_columns.append(header)
        return target_columns


    #Given a name string, returns a renamed, ready to use version
    def apply_renaming(self,name_string: str):

        #If rename_whole_cells is True, applies renamer to the whole string, rather than chunks split by designated characters
        #   ^For formats with multiple names in a cell ("First Last", "Last, First" "Hyphen-ated") this can lead to inconsistent outputs, and should be applied with caution
        if self.rename_whole_cells: 
            return self.renamer.get_safe_name(name_string)

        else:
            #splitting_strings = ["del","jr","sr"] #FUTURE - also exempt strings like titles and connecting words?
            splitting_characters = [' ','-','–','—',',']

            built_string = ""
            pending_chars = ""

            #Iterate through characters in string, pausing to rename and append recent characters whenever a splitting character is reached.
            for c in name_string:
                if c in splitting_characters:
                    renamed_string = self.renamer.get_safe_name(pending_chars)

                    #append renamed string and splitting token, then clear pendingChars
                    built_string += renamed_string
                    built_string += c
                    pending_chars = ""
                else:
                    pending_chars+=c
                    

            #if a remainder exists, rename and append
            if pending_chars != "":
                built_string += self.renamer.get_safe_name(pending_chars)

            return built_string

if __name__ == "__main__":

    #Set up config instance, process given arguments, finish setup
    config = Configuration()
    config.process_args(sys.argv[1:])
    config.finish_setup()

    # Early return if validation fails. otherwise report ready
    if not config.validateConfig():
        print("Validation failed, use flag --help or --menu for more information \nExiting")
        exit(1)
    
    # Print final configuration to console
    config.reportReady()
    
    #Early return if user does not confirm
    if not config.skip_confirmation_step and not config.userConfirm():
        print("Exiting")
        exit(0)

    if config.skip_confirmation_step:
        print("(User skipped confirmation, beginning processing step)")
    print()
    
    #Create renamer and processor instances
    renamer = Renamer(config.selected_seed,warn_on_max_attempts=config.warn_max_attempts)
    file_processor = CSVProcessor(config,renamer)

    #Start process, timing for user feedback
    start_time = time.perf_counter()
    file_processor.start_processing()
    end_time = time.perf_counter()

    #Determine elapsed time and print exit message
    elapsed_time = end_time - start_time
    print(f"Process finished in {elapsed_time:0.3f}s\n")


import sys
import time
import csv
from faker import Faker
from typing import Dict,Set



# Renamer class for generating and storing safe names
class Renamer:

    # Initializes the Renamer with a seed for deterministic name generation.
    def __init__(self, seed: str):
        self.mappings: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        #Generate random seed if none specified
        if seed is None:
            seed = hash("text") % (2**32)
            print(f"generating seed in Renamer: {seed}")
            
        # Use Faker to generate names
        self.fake = Faker()
        Faker.seed(seed)
        # Faker.seed(hash(seed) % (2**32))  # Future - add option to make names random or deterministic

    # Generates or retrieves a safe name for the given original name.
    # def get_safe_name(self, original: str) -> str: TODO enforce type?
    def get_safe_name(self, original):

        # Return empty or whitespace-only names. Future - handle pre-validation in separate method?
        if not original or not original.strip() or original is None:
            return original
            
        # Strip whitespace for consistent mapping, return existing mapping if present
        original = original.strip()
        if original in self.mappings:
            return self.mappings[original]
        
        # Try to generate a unique name. While building, capping attempts at 10/20 meant no collisions
        #max_attempts = GENERATION_ATTEMPT_LIMIT #Future - reimplement
        max_attempts = 20 #magic number - log curve flattens out around 15 attempts

        for attempt in range(max_attempts):
            candidate = self.fake.first_name()
            if candidate not in self.used_names:
                self.mappings[original] = candidate
                self.used_names.add(candidate)
                return candidate

        # If attempts fail, add number suffix to ensure uniqueness
        base_name = self.fake.first_name()
        counter = len(self.used_names)
        candidate = f"{base_name}{counter}"
        
        self.mappings[original] = candidate
        self.used_names.add(candidate)

        WARN_MAX_ATTEMPTS = True #Future - reimplement as config field
        if WARN_MAX_ATTEMPTS:
            print(f"Max attempts reached ({attempt}). Assigned unique name '{candidate}' for original name '{original}'.")

        return candidate


# Configuration class to handle command-line arguments for inputs and options
class Configuration:

    # Initializes the Configuration with default settings, and maps flags and options to their handling functions.
    def __init__(self):
        #Inputs to collect
        self.files = []
        self.columns = []
        self.selected_prefix = None
        self.selected_seed = None

        #Booleans, some settable by option flags
        self.skip_confirmation_step = False
        self.use_default_columns_if_none_specified = True
        self.tokenize_name_parts = True

        #Default values, to apply as needed
        self.default_prefix = "renamed"
        self.default_columns = ["First Name","Last Name","Preferred Name","Camper"]
        #self.default_seed = "safenames" default seed doesn't add much, currently interpreting no seed as user opting for non-deterministic naming
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
            "--menu" : self.handle_option_menu, #Future - implement a more detailed menu, with --help offering a more concise tip and reference to --menu for more
            "--skip" : self.handle_option_skip, 
            "--defaultcolumns" : self.handle_option_defaultcolumns, #Future - add default column set feature from original version
            # "--splitnames" : self.applySplitNames, #Future - make name splitting feature toggleable
            # "--autocolumns" : autoDetectColumns, #Future - add auto column detection feature from original version
        }


    # Handler for the '-f' flag adds input files for processing
    def handle_flag_file(self,path:str):
        if path not in self.files:
            self.files.append(path)
    
    # Handler for the '-c' flag adds target columns for renaming
    def handle_flag_column(self,col:str):
        if col not in self.columns:
            self.columns.append(col) 
    
    # Handler for the '-p' flag sets the output file prefix. 
    def handle_flag_prefix(self,prefix:str):
        self.selected_prefix = prefix

    # Handler for the '-s' flag sets the name generation seed.
    def handle_flag_seed(self,seed:str):
        self.selected_seed = seed

    # Handler for the '--menu' option – prints usage information. Future - spruce this up once planned features are implemented
    def handle_option_menu(self):
        print("""usage: main.py
              [-f <file>]   - program requires at least one file, each marked by this flag
              [-c <column>] - column(s)if none are provided, applies default set
              [-p <prefix>] - optionally specify the prefix for renamed files, replacing 'renamed-')
              [-s <seed>]   - optionally specify a seed for consistent name mappings.
              """)
        exit(1)
        #Future - if other arguments were provided, explain to user that menu/help was called and no further processing will occur?

    # Handler for the '--help' option to display help information. Future - spruce this up once planned features are implemented
    def handle_option_help(self):
        print("""This program requires arguments to specify the targets and methods for a renaming operation
                usage: main.py [-f <file>] [-c <column>]
                 \nfor more info, run main.py --menu """)
        exit(1)

    # Handler for the '--skip' option to bypass confirmation step
    def handle_option_skip(self):
        self.skip_confirmation_step = True

    # Applies default columns to the configuration
    def handle_option_defaultcolumns(self):
        for col in self.default_columns:
            self.handle_flag_column(col)
    
    # Processes command-line arguments to configure the application.
    def process_args(self,arg_queue:list):

        #Future - iterate over args rather than consuming a queue? since this isnt the original copy and is simple, im not concerned
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

                print(f"currently no support for argument: '{current_arg}' without a preceding flag. Exiting for safety")
                print()
                self.handle_option_menu() #not ideal to use this here, but avoids code duplication. FUTURE - tweak while implementing true menu/help prints

    #Finish setup step, applying defaults where relevant
    def finish_setup(self):

        #Apply default columns if none were specified and fallback is enabled
        if self.columns == [] and self.use_default_columns_if_none_specified:
            print("No columns specified, applying default columns.")
            self.handle_option_defaultcolumns()

        #Apply default prefix if none was specified
        if self.selected_prefix is None:
            print(f"No prefix specified, applying default prefix '{self.default_prefix}'.")
            self.selected_prefix = self.default_prefix

    # Validates the current configuration to ensure inputs are valid and ready to use
    def validateConfig(self):
        
        if self.files == []:
            print("No files specified. Use -f <file> to add files.")
            return False
        if self.columns == []:
            print("No columns specified. Use -c <column> to add columns.")
            return False
        return True
        #Future - check validity of input files, maybe offer fallbacks for columns?

    # Reports the current configuration to the user, enabling them to confirm that the listed settings are correct
    def reportReady(self):
        print("Ready to start with the following configuration:")
        print(f"Files: {self.files}")
        print(f"Columns: {self.columns}")
        print(f"Prefix: {self.selected_prefix}")
        print()

    # Enables the user to confirm
    def userConfirm(self):
        #Future - consider putting reportReady reference here, as its not super needed if confirmation step is skipped. Though its still goof for the record
        #Get user input, rejecting anything other than ""
        response = input("Press ENTER to continue, add any character and press ENTER to cancel: ")
        if response == "":
            return True
        else:
            print("Operation cancelled by user.")
            return False


# CSVProcessor class for processing CSV files and replacing names in specified columns.
# Future - add graceful handling somewhere for file issues
class CSVProcessor:

    def __init__(self, config: Configuration, renamer: Renamer):
        self.config = config
        self.renamer = renamer

        #Better practice to define each here, or pull from self.config.whatever each time? Values wont change at this point
        self.name_columns = config.columns
        self.target_files = config.files
        self.given_prefix = config.selected_prefix

    def start(self):
        for input_file in self.target_files:
            output_file = f"{self.given_prefix}-{input_file}"
            print(f"Processing {input_file} -> {output_file}",end="\n")
            self.processFile(input_file, output_file)
    
    #iterate through input file, replacing names in target columns and writing to output file
    def processFile(self, input_path: str, output_path: str):

        with open(input_path, 'r', newline='', encoding='utf-8-sig') as infile:
                    
            #TODO - settle on final approach for handling cm file bugs in header row. Use a first class function here? might make irrelevant by scanning the whole file first, then reproducing with more Dictwriter specifications
            #before setting up reader, read and store header (fixes DictWriter bug where irregular header lines would be recreated unfaithfully, rather than leaving headers untouched)
            #header_line = infile.readline() # Add this line to store the header before printing verbatim as output header
            reader = csv.DictReader(infile)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                # outfile.write(header_line)
                if reader.fieldnames:

                    writer = csv.DictWriter(
                        outfile, 
                        fieldnames=reader.fieldnames,
                        quoting=csv.QUOTE_ALL, # Ensures all fields are quoted, convention for CM files
                        # extrasaction='ignore'  # Add this to handle extra columns
                    )
                    writer.writeheader() #comment out if using the header_line bug fix
                    
                    #iterate through rows, replacing names when relevant
                    for row in reader:
                        for col in self.name_columns:
                            if col in row and row[col]:
                                
                                row[col] = self.renamingFunction(self.renamer,row[col])

                        # Write row with replaced names
                        writer.writerow(row)
 
    #Given a name string, returns a renamed, ready to use version 
    #Based on tokenize_name_parts status, will apply renamer to the whole string, or in chunks split by designated characters
    def renamingFunction(self,renamer_instance: Renamer,nameString: str):

        #Future - handle with first class function somewhere calling this function or get_safe_name directly?
        #Rename and return whole string if not tokenizing
        if not self.config.tokenize_name_parts: 
            return renamer_instance.get_safe_name(nameString)

        else:
            #splittingStrings = ["del","jr","sr"] #Future - also exempt strings like titles and connecting words?
            splittingCharacters = [' ','-','–','—',',']

            built_string = ""
            pending_chars = ""

            #Iterate through characters in string, pausing to rename and append recent characters whenever a splitting character is reached.
            for c in nameString:
                # if splittingCharacters.contains(c):
                if c in splittingCharacters:
                    
                    renamed_string = renamer_instance.get_safe_name(pending_chars)
                    #append renamed string and splitting token, then clear pendingChars
                    built_string += renamed_string
                    built_string += c
                    pending_chars = ""
                else:
                    pending_chars+=c
                    

            #if a remainder exists, rename and append
            if pending_chars != "":                
                # built_string += renamer_instance.get_safe_name(pending_chars)
                # built_string += renamer_instance.get_safe_name(pending_chars)
                built_string += renamer_instance.get_safe_name(pending_chars)

            return built_string

if __name__ == "__main__":

    #Set up config instance, process given arguments, finish setup
    config = Configuration()
    config.process_args(sys.argv[1:])
    config.finish_setup()

    # Exit if validation fails. otherwise report ready
    if not config.validateConfig():
        print("Validation failed, use flag --help or --menu for more information \nExiting")
        exit(0)
    else:
        config.reportReady() #Future: consider only 'reporting' here skipping isn't enabled. or call report from the userconfirm step
    
    if config.skip_confirmation_step or config.userConfirm():

        #Create renamer and processor instances
        renamer = Renamer(config.selected_seed)
        file_processor = CSVProcessor(config,renamer)

        #Start process, timing for user feedback
        start_time = time.perf_counter()
        file_processor.start()
        end_time = time.perf_counter()

        #Determine elapsed time and print exit message
        elapsed_time = end_time - start_time
        print(f"Process finished in {elapsed_time:0.3f}s\n")

    else:
        print("Exiting")
        exit(1)


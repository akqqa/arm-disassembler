# arm-disassembler
CS4099 Project - A program to disassemble arm instructions given the official specification

## How to run:

First, ensure that this directory contains a folder called arm-files, containing the official Arm MRS for the A64 Instruction Set. The 2023-12 version of these files comes zipped with these files, and should be extracted.

1. Run the command "pip install -r requirements.txt"
2. Generate and store the data structure required for disassembling by running the command "python pickler.py". This should create a file named "data.pkl"
3. Once generated, the disassembler can be run with the command "python main.py <file/to/disassemble>"


## Running Accuracy Evaluation

1. Run the command "aarch64-linux-gnu-objdump -D -m aarch64 -j .text testFiles/allTest.elf > objdump.out"
2. Run the command "python main.py testFiles/allTest.elf > myOutput.out"
3. Run the command "python objdumpCompare.py"

This will display the accuracy of this project compared to objdump


## Running Unit Tests

1. Run the command "python tests.py"



## Files:
- capstoneDisassembler.py - the implementation of Capstone in Python, used to compare performance with this project.

- common.py - the common and helper methods used by other files throughout the project.

- decoder.py - the file containing all classes and methods for supporting the decoding phase of the disassembler.

- main.py - the main file used to run the disassembler. Reads the contents of a given binary or ELF file and uses the data structures produced by pickler.py to disassemble the machine code.

- disassembler.py - the file containing all classes and methods for supporting the disassembling phase of the disassembler.

- objdumpCompare.py - the file used to transform objdump outputs into a format equivalent to this project, and compare both outputs to obtain statistics about the accuracy of this project.

- pickler.py - the file that generates all necessary data structures for disassembling based on the provided Arm MRS, and serialises them to a file for the main.py file to use.

- tests.py - the unit tests developed for this project.

- outputs/ - a folder containing various outputs of this project on the allTest.elf file, from previous versions of the disassembler.

- testFiles/ - a folder containing various files used while testing and debugging the disassembler. Most notably, the allTest files, as well as performanceTest1/2/3.

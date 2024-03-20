# arm-disassembler
CS4099 Project - A program to disassemble arm instructions given the official specification

How to run:

First, ensure that this directory contains a folder called arm-files, containing the official Arm MRS for the A64 Instruction Set

1. Run the command "pip install -r requirements.txt"
2. Generate and store the data structure required for disassembling by running the command "python pickler.py". This should create a file named "data.pkl"
3. Once generated, the disassembler can be run with the command "python main.py <file/to/disassemble>"


Runnning Accuracy Evaluation

1. Run the command "aarch64-linux-gnu-objdump -D -m aarch64 -j .text testFiles/allTest.elf > objdump.out"
2. Run the command "python main.py testFiles/allTest.elf > myOutput.out"
3. Run the command "python objdumpCompare.py"

This will display the accuracy of this project compared to objdump


Running Unit Tests

1. Run the command "python tests.py"
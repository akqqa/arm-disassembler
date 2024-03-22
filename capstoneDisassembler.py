# A script to disassemble a given file using the Capstone Library

from capstone import *
import sys
import pickle
from common import *
import elftools
from elftools.elf.elffile import ELFFile

def capstoneDisassemble(line):
    """
    Disassembles a line of machine code using the Capstone API

    :param line: the line of machine code to disassemble
    """

    # Code snippet adapted directly from https://www.capstone-engine.org/lang_python.html
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for i in md.disasm(line, 0):
        print("%s\t%s" %(i.mnemonic, i.op_str))

def disassemble(filename):
    """
    Disassembles a given machine code file

    :param filename: the file to disassemble
    """

    # Checks if file is binary or elf
    if (filename[-4:] == ".bin"):
        file = open(filename, "rb")
        bs = file.read(4)
        # Read every 4 bytes and use capstone to disassemble
        while (bs):
            try:
                capstoneDisassemble(bs)
            except:
                print("Error - could not translate line") # If fatal crash, worst case is instruction is not translated
            bs = file.read(4)
    elif (filename[-4:] == ".elf"):
        with open(filename, "rb") as f:
            elfFile = ELFFile(f)
            textSection = elfFile.get_section_by_name(".text")
            data = textSection.data()
            # Read every 4 bytes and use capstone to disassemble
            for i in range(0, len(data), 4):
                instructionBytes = data[i:i+4]
                try:
                    capstoneDisassemble(instructionBytes)
                except:
                    print("Error - could not translate line") # If fatal crash, worst case is instruction is not translated

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Incorrect number of arguments")
        print("Format: python capstoneDisassembler.py <path_to_file>")
        quit()

    # Disassemble the given file using Capstone
    disassemble(sys.argv[1])

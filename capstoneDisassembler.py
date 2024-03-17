from capstone import *
import sys
import pickle
from common import *
import elftools
from elftools.elf.elffile import ELFFile

# Code snippet adapted directly from https://www.capstone-engine.org/lang_python.html
def capstoneDisassemble(line):
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for i in md.disasm(line, 0):
        print("%s\t%s" %(i.mnemonic, i.op_str))

# Add check for less than 4 bytes read!
def disassemble(filename):
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
        # Will likely have to check whether the file is big or little endian
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

    disassemble(sys.argv[1])

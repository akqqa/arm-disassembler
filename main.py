# A file to run the disassembler on a given file

import sys
import pickle
from common import *
import elftools
from elftools.elf.elffile import ELFFile

# Add check for less than 4 bytes read!
def disassemble(filename, encodingTable):
    """
    Disassembles a given machine code file

    :param filename: the file to disassemble
    :param encodingTable: the root node of the encodingTable, which gives access to the entire data structure used to encode the Arm Specification
    """

    # Checks file extension and handles it accordingly
    if (filename[-4:] == ".bin"):
        file = open(filename, "rb")
        bs = file.read(4)
        # For each 32-bit/4-byte instruction in the file
        while (bs):
            # reverse the array, for endianness
            bs = bs[::-1]
            # Convert to binary
            bs = [bin(x) for x in bs]
            # Remove the 0b's
            bs = [x[2:] for x in bs]
            # finally, pad with leading 0's
            bs = [addLeadingZeroes(x) for x in bs]
            # Add all bytes, then decode the instruction
            instruction = "".join(bs)
            try:
                print(encodingTable.decode(instruction))
            except:
                print("Error - could not translate line") # If fatal crash, worst case is instruction is not translated
            bs = file.read(4)
    elif (filename[-4:] == ".elf"):
        with open(filename, "rb") as f:
            elfFile = ELFFile(f)
            textSection = elfFile.get_section_by_name(".text")
            data = textSection.data()
            # For each 32-bit/4-byte instruction in the file
            for i in range(0, len(data), 4):
                instructionBytes = data[i:i+4]
                # reverse the array, for endianness
                instructionBytes = instructionBytes[::-1]
                # Convert to binary
                instructionBytes = [bin(x) for x in instructionBytes]
                # Remove the 0b's
                instructionBytes = [x[2:] for x in instructionBytes]
                # finally, pad with leading 0's
                instructionBytes = [addLeadingZeroes(x) for x in instructionBytes]
                # Add all bytes, then decode the instruction
                instruction = "".join(instructionBytes)
                try:
                    print(encodingTable.decode(instruction))
                except:
                    print("Error - could not translate line") # If fatal crash, worst case is instruction is not translated

if __name__ == "__main__":

    if (len(sys.argv) != 2):
        print("Incorrect number of arguments")
        print("Format: python disassembler.py <path_to_file>")
        quit()

    # Unpickle the previously created data structure that represents the Arm Specification
    file = open('data.pkl', 'rb')
    table = pickle.load(file)

    # Start the disassembly process
    disassemble(sys.argv[1], table)

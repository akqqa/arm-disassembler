# Decodes the machine code based on a given specification

import xml.etree.ElementTree as et

# Class to store the variable encoding of a binary instruction
# Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
# Perhaps change this to simply return the values dict, instead of tying it inherently to the object for better representation of what is actually being done
class InstructionEncoding():

    # Default example encoding - [start position, length(inclusive)]
    encodings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    values = {}

    def __init__(self, encodings=encodings):
        self.encodings = encodings

    def assignValues(self, instruction):
        if len(instruction) != 32:
            return False
        for var in self.encodings:
            start = 31 - self.encodings[var][0] # 31 - as the encoding is done 31-0 whereas arrays are 0-31
            end = start + self.encodings[var][1]
            value = instruction[start:end]
            self.values[var] = value
        return True


class EncodingTable():

    # Entries - a mapping of the variable values to either an instruction name or nested encoding table - effectively a node of the decode tree
    # Key: an instructionencoding
    # Value: either an instruction name or a further entry

    entries = {}

    # Initialises with xml, which starts at the root node of the encoding table that will be converted to this class
    def __init__(self, hierarchy):
        # Use regdiagram to create the isntructionencoding for this table
        nodes = hierarchy.iterfind("node")
        # If a groupname, create an instructionencoding for the decode, then add to entires, with the value being a newly defined encodingtable with the xml parsed
        # If an iclass, create an instructionencoding for the decode, then add the name as the value





xml = et.parse("encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")
print(hierarchy)

table = EncodingTable(hierarchy)
    


# test = InstructionEncoding()
# print(test.encodings)
# test.assignValues("10100101001101001010110101011001")
# print(test.values)

# Decoding process:
# Parse each table in the index by encoding section, storing each in a data structure
# start at top level, assign values to instructionencoding, then use this to match with row of table,
# then get up pointed to table, and assign the instruction encoding, repeating until instruction found

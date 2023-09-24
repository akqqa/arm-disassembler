# Decodes the machine code based on a given specification

import xml.etree.ElementTree as et
import sys

sys.setrecursionlimit(10000)

# Class to store the variable encoding of a binary instruction
# Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
# Perhaps change this to simply return the values dict, instead of tying it inherently to the object for better representation of what is actually being done
class InstructionEncoding():

    # Default example encoding - [start position, length(inclusive)]
    encodings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    def __init__(self, encodings=encodings):
        self.encodings = encodings

    def assignValues(self, instruction):
        if len(instruction) != 32:
            return False
        for var in self.encodings:
            values = {}
            start = 31 - self.encodings[var][0] # 31 - as the encoding is done 31-0 whereas arrays are 0-31
            end = start + self.encodings[var][1]
            value = instruction[start:end]
            values[var] = value
        return values


class EncodingTable():

    # Entries - a mapping of the variable values to either an instruction name or nested encoding table - effectively a node of the decode tree
    # Key: a flatted map of variable names to the matching pattern
    # Value: either an instruction name or a further encodingtable

    entries = {}

    # Initialises with xml, which starts at the root node of the encoding table that will be converted to this class
    def __init__(self, hierarchy, debug=False):
        self.entries = {}
        variables = {}
        # Use regdiagram to create the isntructionencoding for this table
        regdiagram = hierarchy.find("regdiagram")
        boxes = regdiagram.findall("box")
        for box in boxes:
            if "name" in box.attrib:
                variables[box.attrib["name"]] = [int(box.attrib["hibit"]), int(box.attrib["width"])]
        self.instructionEncoding = InstructionEncoding(variables)

        # Iterate through each node, adding their entry to the table
        nodes = hierarchy.findall("node")
        # If a groupname, create an dict of the mapping from the decode, then add to entires, with the value being a newly defined encodingtable with the xml parsed
        # If an iclass, create an dict of the mapping from the decode, then add the name as the value
        for node in nodes:
            mapping = []
            decode = node.find("decode")
            boxes = decode.findall("box")
            for box in boxes:
                name = box.attrib["name"]
                value = box.find("c").text
                mapping += (name, value)
            if "groupname" in node.attrib:
                self.entries[tuple(mapping)] = EncodingTable(node)
            elif "iclass" in node.attrib:
                self.entries[tuple(mapping)] = node.attrib["iclass"]

    def print(self):
        print(len(self.entries.values()))
        for entry in self.entries.values():
            print(entry)
        for entry in self.entries.values():
            if type(entry) is EncodingTable:
                print("")
                entry.print()

xml = et.parse("encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")
#print(hierarchy)


table = EncodingTable(hierarchy)
#print(table.instructionEncoding.encodings)
table.print()

# print(table.entries)

# print(table.entries[('op0', '0', 'op1', '0000')].entries)
    
# # !!!
# print(table.entries[('op0', '0', 'op1', '0000')].entries == table.entries)

# test = InstructionEncoding()
# print(test.encodings)
# test.assignValues("10100101001101001010110101011001")
# print(test.values)

# Decoding process:
# Parse each table in the index by encoding section, storing each in a data structure
# start at top level, assign values to instructionencoding, then use this to match with row of table,
# then get up pointed to table, and assign the instruction encoding, repeating until instruction found

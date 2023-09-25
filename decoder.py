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
        print(self.encodings)
        values = []
        if len(instruction) != 32:
            return False
        for var in self.encodings.keys():
            start = 31 - self.encodings[var][0] # 31 - as the encoding is done 31-0 whereas arrays are 0-31
            end = start + self.encodings[var][1]
            value = instruction[start:end]
            values.append((var, value))
        print("values: " + str(values))
        return tuple(values)


class EncodingTable():

    # Entries - a mapping of the variable values to either an instruction name or nested encoding table - effectively a node of the decode tree
    # Key: a flatted map of variable names to the matching pattern
    # Value: either an instruction name or a further encodingtable

    # Initialises with xml, which starts at the root node of the encoding table that will be converted to this class
    # instructionEncoding - the instruction encoding to map variables on incoming instructions
    # entries - the table, with keys being tuples of variable values to match, and values either being instructions or nested EncodingTables
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
        # If a groupname, create an dict of the mapping from the decode, then add to entries, with the value being a newly defined encodingtable with the xml parsed
        # If an iclass, create an dict of the mapping from the decode, then add the name as the value
        for node in nodes:
            mapping = []
            decode = node.find("decode")
            boxes = decode.findall("box")
            for box in boxes:
                name = box.attrib["name"]
                value = box.find("c").text
                mapping.append((name, value))
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

    def decode(self, instruction):
        # Extract variables from the instruction
        values = self.instructionEncoding.assignValues(instruction)
        

        # Rules: patterns match if 1's and 0's match exactly, or != applies
        # For each row of the encoding table, checks if each variable assignment of the row matches a variable in the instruction being matched
        for row in self.entries.keys():
            print("row being checked: " + str(row))
            print("variable values: " + str(values))
            matches = True
            for tup in row:
                if not self.matchVar(values, tup):
                    matches = False
            if matches:
                print("matched!")
                # This is the correct row
                if type(self.entries[row]) is EncodingTable:
                    return self.entries[row].decode(instruction)
                else:
                    return self.entries[row]
        return None

    def matchVar(self, vars, tup):
        for var in vars:
            if var[0] == tup[0]:
                print(var[0])
                print(tup[0])
                # Check if var[1] matches tup[1]
                if var[1] == None:
                    return True
                elif tup[1][0] != "!":
                    for i in range(0, len(var[1])):
                        if var[1][i] == tup[1][i] or tup[1][i] == "x":
                            continue
                        else:
                            break
                    return True # All characters in var and tup match so correctly matching
                else:
                    # Case with != at the start
                    splitted = tup[1].split()
                    if var[1] != splitted[1]:
                        return True
        return False        

xml = et.parse("encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")

table = EncodingTable(hierarchy)
#table.print()

print(table.decode("11011010110000000010001010010110"))
# current issue, incorrectly matches things!!

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

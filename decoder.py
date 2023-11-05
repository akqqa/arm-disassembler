# Decodes the machine code based on a given specification

import xml.etree.ElementTree as et
import sys
from common import *
from instruction import *

class EncodingTable():

    # Entries - a mapping of the variable values to either an instruction name or nested encoding table - effectively a node of the decode tree
    # Key: a flatted map of variable names to the matching pattern
    # Value: either an instruction name or a further encodingtable

    # Initialises with xml, which starts at the root node of the encoding table that will be converted to this class
    # instructionEncoding - the instruction encoding to map variables on incoming instructions
    # entries - the table, with keys being tuples of variable values to match, and values either being instructions or nested EncodingTables
    def __init__(self, root, hierarchy, sect=False):
        self.directname = None # Used only in cases where an iclass_sect has no table and is just one instruction name
        # Handles regular tables and iclass_sects differently
        if sect:
            self.entries = {}
            variables = {}
            # Use the regdiagram to create instructionencoding for this table
            regdiagram = hierarchy.find("regdiagram")
            boxes = regdiagram.findall("box")
            for box in boxes:
                if "name" in box.attrib:
                    if "width" in box.attrib:
                        varWidth = box.attrib["width"]
                    else:
                        varWidth = 1 #For some reason doesnt declare 1 width if the width is 1
                    variables[box.attrib["name"]] = [int(box.attrib["hibit"]), int(varWidth)]
            self.instructionEncoding = InstructionEncoding(variables)
            #print(variables)

            instructiontable = hierarchy.find("instructiontable")

            tableVars = []
            headers = instructiontable.find("thead").findall("tr")

            # Special case if the table only has one row - just set a directname
            if len(headers) == 1:
                # Go into tbody, go into first tr, then first td. This contains the iformid!
                instr_name = instructiontable.find("tbody").find("tr").attrib["encname"]
                #print("directname")
                self.directname = instr_name
                return
            # Otherwise, get the tableVars in order by reading the text of headings2's
            ths = headers[1].findall("th") 
            for th in ths:
                tableVars.append(th.text)

            # Next, go into the tbody. For each tr, select the first n td's where n is len(tableVars), get text 
            # Then, each in a tuple with its expected value (the text), and push each of these into a mapping array
            # Finally, append the tuple of this array as a key to the entires, with the encname as the value mapped
            body = instructiontable.find("tbody")
            for tr in body.findall("tr"):
                mapping = []
                #print(tableVars)
                tds = tr.findall("td")
                for i in range(0, len(tableVars)):
                    mapping.append((tableVars[i], tds[i].text))
                # If a file exists, set the mapping to the filename, otherwise encname
                if "iformfile" in tr.attrib:
                    #print(tr.attrib["iformfile"])
                    self.entries[tuple(mapping)] = InstructionPage("arm-files/" + tr.attrib["iformfile"])
                else:
                    self.entries[tuple(mapping)] = tr.attrib["encname"]


        else:
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
                    self.entries[tuple(mapping)] = EncodingTable(root, node)
                elif "iclass" in node.attrib:
                    iclass_sects = root.findall(".//iclass_sect")  # very inefficient, can cache for better performance
                    found = False
                    for sect in iclass_sects:
                        if sect.attrib["id"] == node.attrib["iclass"]:
                            found = True
                            self.entries[tuple(mapping)] = EncodingTable(root, sect, True)
                            continue
                    # If not found, no sect for this iclass
                    if not found:
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

        # If there is no table, just return the name of the instruction
        if self.directname != None:
            return self.directname
        
        #print("entries")
        #print(self.entries)

        # Rules: patterns match if 1's and 0's match exactly, or != applies
        # For each row of the encoding table, checks if each variable assignment of the row matches a variable in the instruction being matched
        for row in self.entries.keys():
            #print("row being checked: " + str(row))
            #print("variable values: " + str(values))
            matches = True
            for tup in row:
                if not self.matchVar(values, tup):
                    matches = False
            if matches:
                #print("matched!")
                # This is the correct row
                if type(self.entries[row]) is EncodingTable:
                    return self.entries[row].decode(instruction)
                elif type(self.entries[row]) is InstructionPage:
                    # Return either name or the matched InstructionPage
                    return self.entries[row].disassemble(instruction)
                else:
                    return self.entries[row]
        #print("none found")
        return None

    def matchVar(self, vars, tup):
        for var in vars:
            if var[0] == tup[0]:
                # Check if var[1] matches tup[1]
                if tup[1] == None:
                    return True
                elif tup[1][0] != "!": # this wont catch all cases, see https://developer.arm.com/documentation/ddi0602/2023-09/Index-by-Encoding/SME-encodings?lang=en#mortlach_multi_indexed_3
                    matches = True
                    for i in range(0, len(var[1])):
                        if var[1][i] == tup[1][i] or tup[1][i] == "x":
                            continue
                        else:
                            matches = False
                    if matches:
                        return True # All characters in var and tup match so correctly matching
                else:
                    # Case with != at the start
                    splitted = tup[1].split()
                    if var[1] != splitted[1]:
                        return True
        return False        

xml = et.parse("arm-files/encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")

table = EncodingTable(root, hierarchy)


print(table.decode("00000000000000000000000000000000"))
print()
# ABS
print(table.decode("11011010110000000010001010010110"))
print()
# HINT (YIELD) - this works, but slight complexity, as the first row defines everything as being hint
# And then in the hint there is the pseudocode for figuring out which hint, dspite this also being in the table..
# Perhaps implement a system so it first finds all matches, and then uses the one with the least Nones - aka closest match
print(table.decode("11010101000000110010000000111111"))
print()
# FEXPA
print("decoding 00000100011000001011100000000000: ")
print(table.decode("00000100011000001011100000000000"))
print()
# FDOT (2-way, multiple and indexed vector, FP8 to FP16) - this ones weird - the docs dont match the xml perfectly
print(table.decode("11000001000101011011100001000101"))
print()
# SQDMULH (multiple vectors)
print(table.decode("11000001111000001011010000000000"))
print()
# FDOT (2-way, multiple and single vector, FP8 to FP16) - this again is unallocated, yet switching final 01 to 10 gives correct bfdot, maybe fdot not supported?
print(table.decode("11000001001000000111000101001111"))
print()
# BFDOT
print(table.decode("11000001001000000111000101010111"))
print()

# https://developer.arm.com/documentation/ddi0602/2023-09/Base-Instructions/LDR--immediate---Load-Register--immediate--
print("Wt ldr preindex:")
print(table.decode("10111000010011010101110011010101"))
print("Xt ldr preindex:")
print(table.decode("11111000010011010101110011010101"))

print("Wt LDR unsigned offset:")
print(table.decode("10111001011010101010111010100101"))
print("Xt LDR unsigned offset:")
print(table.decode("11111001011010101010111010100101"))
print()

#F2CVTL{2} - apparently unallocated??? weird - OH cause its a feat
print(table.decode("01101110011000010111100101010101"))

# Instead try FCVTN
print(table.decode("01001110011000010110100101010101"))

print(table.decode("11110000000000000001010000010010"))
#Works!!

# Example program (GENERATED WITH CHATGPT):
# mov x0, #5 
# mov x1, #7 
# add x2, x0, x1
# mov x8, #93 
# svc #0  
# Which in machine code is (according tohttps://armconverter.com/ )
# A00080D2 - 10100000000000001000000011010010
# E10080D2 - 11100001000000001000000011010010
# 0200018B - 00000010000000000000000110001011
# A80B80D2 - 10101000000010111000000011010010
# 010000D4 - 00000001000000000000000011010100

# D28000A0 - 11010010100000000000000010100000
# D28000E1 - 11010010100000000000000011100001
# 8B010002 - 10001011000000010000000000000010
# D2800BA8 - 11010010100000000000101110101000
# D4000001 - 11010100000000000000000000000001

print()
print("Decoding example program:")
print(table.decode("11010010100000000000000010100000"))
print(table.decode("11010010100000000000000011100001"))
print(table.decode("10001011000000010000000000000010"))
print(table.decode("11010010100000000000101110101000"))
print(table.decode("11010100000000000000000000000001"))

# IT WORKS!! important note - is big endian!
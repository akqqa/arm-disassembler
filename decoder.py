# Decodes the machine code based on a given specification

import xml.etree.ElementTree as et
import sys
from common import *
from instruction import *
import pickle
import elftools # pip install pyelftools
from elftools.elf.elffile import ELFFile


class EncodingTable():

    # Entries - a mapping of the variable values to either an instruction name or nested encoding table - effectively a node of the decode tree
    # Key: a flattened map of variable names to the matching pattern
    # Value: either an instruction name or a further encodingtable

    # Initialises with xml, which starts at the root node of the encoding table that will be converted to this class
    # instructionEncoding - the instruction encoding to map variables on incoming instructions
    # entries - the table, with keys being tuples of variable values to match, and values either being instructions or nested EncodingTables
    def __init__(self, root, hierarchy, sect=False):
        self.entries = {}
        self.instructionEncoding = None
        self.directFile = None # Used only in cases where an iclass_sect has no table and is just one instruction name
        # Handles regular tables and iclass_sects differently
        # sect: this Encoding Table is a table where each entry links to the iformfile of a specific instruction.
        if sect:
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

            instructiontable = hierarchy.find("instructiontable")

            tableVars = []
            headers = instructiontable.find("thead").findall("tr")

            # Special case if the table only has one row - just set a directFile
            if len(headers) == 1:
                tr = instructiontable.find("tbody").find("tr")
                # Go into tbody, go into first tr, then first td. This contains the iformid!
                if "iformfile" in tr.attrib:
                    self.directFile = InstructionPage("arm-files/" + tr.attrib["iformfile"])
                else:
                   self.directFile = tr.attrib["encname"]
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
                    self.entries[tuple(mapping)] = InstructionPage("arm-files/" + tr.attrib["iformfile"])
                else:
                    self.entries[tuple(mapping)] = tr.attrib["encname"]
        # a node, not an iclass_sect. so handle accoridngly, creating further encodingtable objects in the entries
        else:
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

        # If there is no table, handle special case and directly assign directFile
        if self.directFile is not None:
            if type(self.directFile) is EncodingTable:
                return self.directFile.decode(instruction)
            elif type(self.directFile) is InstructionPage:
                # Return either name or the matched InstructionPage
                return self.directFile.disassemble(instruction)
            else:
                return self.directFile
        

        # Rules: patterns match if 1's and 0's match exactly, or != applies
        # For each row of the encoding table, checks if each variable assignment of the row matches a variable in the instruction being matched
        for row in self.entries.keys():
            matches = True
            # Check if every variable in the instruction matches an instructon in the table entry
            for tup in row:
                if not self.matchVar(values, tup): # Checks if any of the values (variable values extracted from the instruction based on the encoding) match the number in the row tuple
                    matches = False
            if matches:
                # This is the correct row
                if type(self.entries[row]) is EncodingTable:
                    return self.entries[row].decode(instruction)
                elif type(self.entries[row]) is InstructionPage:
                    # Return either name or the matched InstructionPage
                    return self.entries[row].disassemble(instruction)
                else:
                    return self.entries[row]
        return None

    # vars = all variables extracted from the endcoding
    # tup = a single number
    # This method finds if the variable with the same name as this tuple has the same values
    def matchVar(self, vars, tup):
        # Check each var
        for var in vars:
            if var[0] == tup[0]:
                # Check if var[1] matches tup[1]
                if tup[1] == None:
                    return True
                # Check if each element matches. If a != is present, make sure the remainder of the string is not equal to the rest of it.
                if "!=" in tup[1]:
                    splitEncoding = tup[1].replace(" ", "").split("!=")
                    if len(splitEncoding[0]) == 0:
                        return not compareWithXs(splitEncoding[1], var[1])
                    else: # Compare the first and second halves, the first matching exactly, the second not matching exactly
                        splitPoint = len(splitEncoding[0])
                        firstHalf = var[1][:splitPoint]
                        secondHalf = var[1][splitPoint:]
                        # Return the first half of the encoding (before the !=) with the equivalent first half of the variable value, logically ANDed with the inverse of the second etc.
                        return (compareWithXs(splitEncoding[0],firstHalf)) and (not (compareWithXs(splitEncoding[1], secondHalf)))
                else:
                    # Compare the two strings
                    return compareWithXs(tup[1], var[1])
        return False




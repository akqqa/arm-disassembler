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
                    #print(i)
                    #print(tds)
                    mapping.append((tableVars[i], tds[i].text))
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
                    iclass_sects = root.findall(".//iclass_sect") 
                    i = 0
                    if (node.attrib["iclass"] == "dp_1src"):
                        print(len(iclass_sects)) 
                    else:
                        print(node.attrib["iclass"]) # FOR SOME REASON, NOT PROPERLY WORKING, doesnt go thru all of the iclasses? idk why. only 93 of them.. hmm.
                    for sect in iclass_sects:
                        #print (i)
                        i += 1
                        # if (sect.attrib["id"] == "dp_1src"):
                        #     print(sect.attrib["id"])
                        #     print(node.attrib["iclass"])
                        if sect.attrib["id"] == node.attrib["iclass"]:
                            # print(i)
                            # print(sect.attrib["id"])
                            if (sect.attrib["id"]) == "dp_1src":
                                print("exiting")
                                quit()
                            self.entries[tuple(mapping)] = EncodingTable(root, sect, True)
                            return
                    # If reached, no sect for this iclass
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
        
        print("entries")
        print(self.entries)

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
        print("none found")
        return None

    def matchVar(self, vars, tup):
        for var in vars:
            if var[0] == tup[0]:
                # Check if var[1] matches tup[1]
                if tup[1] == None:
                    return True
                elif tup[1][0] != "!":
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

xml = et.parse("encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")

table = EncodingTable(root, hierarchy)
#table.print()

# print("TEST")
# iclass_sects = root.findall(".//iclass_sect")
# i = 0
# for sect in iclass_sects:
#     i+=1
#     if (sect.attrib["id"]) == "dp_1src":
#         print(sect.attrib["id"])

#print(table.decode("00000000000000000000000000000000"))
#print(table.decode("11011010110000000010001010010110"))
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

# OKAY theres a whole nother section - the isects, which are a further encoding table for each iclass but in a different format. sigh
from common import *
from encodingDetails import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys

# The class of an instruction - corresponds to each individual iclass in an xml file
class InstructionClass():

    def __init__(self, root):
        # Parse the regdiagram. Creating an instruction encoding for mapping variables, as well as an Instruction description to match instructions with the right class
        self.root = root
        self.instructionDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Will result in a string that matches the given instruction
        self.instructionEncoding = None # The encoding of the instruction - a.k.a the variables derived from the description
        self.encodingSections = None # The list of possible encodings - as in the encoding xml tags.
        
        variables = {}
        # Use the regdiagram to create instructionencoding for this table - IS THIS EVEN NEEDED?> DONT THINK SO~!!! YS IT IS - FOR GETTING THE VARIABLES FOR EXPLANATIONS!!
        # At the same time, get the details to create the instructiondescription
        regdiagram = root.find("regdiagram")
        boxes = regdiagram.findall("box")
        for box in boxes:
            # Encoding logic
            if "name" in box.attrib:
                if "width" in box.attrib:
                    varWidth = box.attrib["width"]
                else:
                    varWidth = 1 #For some reason doesnt declare 1 width if the width is 1
                variables[box.attrib["name"]] = [int(box.attrib["hibit"]), int(varWidth)]
            # Instruction form logic
            if "settings" in box.attrib:
                index = 31 - int(box.attrib["hibit"])
                # Create a string corresponding to the digits in this box
                instructionSection = ""
                characters = box.findall("c")
                for char in characters:
                    if char.text == "0" or char.text == "1":
                        instructionSection += char.text
                    else:
                        instructionSection += "x"
                # Replace the characters at the index in the instructionDescription with this section
                self.instructionDescription = self.instructionDescription[:index] + instructionSection + self.instructionDescription[index + len(instructionSection):]
        self.instructionEncoding = InstructionEncoding(variables)

        # Encoding section - contains the asm isntruction based on certain conditions
        encodingSect = root.findall("encoding")
        # For now, just getting the mnemonics
        self.possibleAsm = []
        # Code for each encoding section
        self.encodingSections = []
        for e in encodingSect:
            self.encodingSections.append(EncodingDetails(e))

    def matchEncoding(self, instString):
        # For each encoding, check if the encodingDescription matches the instString!
        for e in self.encodingSections:
            matches = True
            encoding = e.encodingDescription
            for i in range(0, len(encoding)):
                if instString[i] == encoding[i] or encoding[i] == "x":
                    continue
                else:
                    matches = False
                    break
            if matches:
                return e # Will return the correct encoding
        return None


    def print(self):
        print(self.root.attrib["name"])
        print(self.instructionDescription)
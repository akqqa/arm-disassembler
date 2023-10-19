from common import *
import xml.etree.ElementTree as et

# Class for storing instruction info - based on each instructions' xml file
# Due to nature of instructions, should have one class for the xml, then contains many objects that are classes iclass

# Superclass will contain:
# aliases
# list of class objects
# PERHAPS store the explanations section here too

# Subclasses will contain:
# the regdiagram as an instruction encodding?
# the different asmtemplates based on the ecndogins
# pseudocode

# When an instructon is matched:
# superclass goes through each class, matches the instructionencodings
# once correct iclass found, can get an object of the correct symbols
# use pseudocode to map symbols
# superclass can map these to the symbols, then the asmtemplate used!



# The page for an intstruction - corresponds to an xml file on a particular instruction
class InstructionPage():

    def __init__(self, file):
        self.classes = []
        root = et.parse(file).getroot()
        #Aliases - for now just store the alias xml element, can work on aliases later as less priority
        self.aliaslist = root.find("alias_list")
        #Class list
        classesSect = root.find("classes")
        classes = classesSect.findall("iclass")
        for c in classes:
            # add to self.classes the InstructionClass constructed from it
            self.classes.append(InstructionClass(c))

    def matchClass(self, instString):
        for c in self.classes:
            matches = True
            encoding = c.instructionDescription
            for i in range(0, len(encoding)):
                if instString[i] == encoding[i] or encoding[i] == "x":
                    continue
                else:
                    matches = False
            if matches:
                return c
        return None

    def print(self):
        for c in self.classes:
            c.print()


# The class of an instruction - correspodns to each individual iclass in an xml file
class InstructionClass():

    def __init__(self, root):
        # Parse the regdiagram. Creating an instruction encoding for mapping variables, as well as an Instruction description to match instructions with the right class
        self.root = root
        variables = {}
        self.instructionDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # Use the regdiagram to create instructionencoding for this table
        # At the same time, get the details to create the 
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
                    instructionSection += char.text
                # Replace the characters at the index in the instructionDescription with this section
                self.instructionDescription = self.instructionDescription[:index] + instructionSection + self.instructionDescription[index + len(instructionSection):]
        self.instructionEncoding = InstructionEncoding(variables)

        # Encoding section - contains the asm isntruction based on certain conditions
        encodingSect = root.findall("encoding")
        # For now, just getting the mnemonics
        self.possibleAsm = []
        for e in encodingSect:
            asm = e.find("asmtemplate")
            mnemonic = asm.find("text").text # finds first instance of text- should be the mnemonic
            self.possibleAsm.append(mnemonic)

            # NOTE THE ENCODINGS USE A SIMILAR TECNNIQUE TO THE ISNTRUCTIONENCODING, MATCHING THE DIFFERENT VARS, REUSE THIS TO MATCH THE CORRECT ENCODING!


    def print(self):
        print(self.root.attrib["name"])
        print(self.instructionDescription)



i1 = InstructionPage("arm-files/abs.xml")

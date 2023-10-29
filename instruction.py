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
                return c # Will return the correct class
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
        self.instructionDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Will result in a string that matches the given instruction
        # Use the regdiagram to create instructionencoding for this table - IS THIS EVEN NEEDED?> DONT THINK SO~!!!
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
            if matches:
                return e # Will return the correct encoding
        return None


    def print(self):
        print(self.root.attrib["name"])
        print(self.instructionDescription)

# Contains infor to match encodiong within a class, as well as the asmtemplate matching
class EncodingDetails():
    
    def __init__(self, root):
        # Create encodingDescription similar to instructionDescription in above class
        boxes = root.findall("box")
        self.encodingDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        for box in boxes:
            if "name" in box.attrib:
                index = 31 - int(box.attrib["hibit"])
                # Create a string corresponding to the digits in this box
                encodingSection = ""
                characters = box.findall("c")
                for char in characters:
                    if char.text == "0" or char.text == "1":
                        encodingSection += char.text
                    else:
                        encodingSection += "x"
                # Replace the characters at the index in the encodingDescription with this section
                self.encodingDescription = self.encodingDescription[:index] + encodingSection + self.encodingDescription[index + len(encodingSection):]


        self.asmTemplate = getASM(root.find("asmtemplate"))
        #print(self.encodingDescription)
        return
    
    # # Checks if given instruction corresponds to this encoding, returning true or false
    # def matchInstruction(self, instruction):
    #     incomingValues = self.instructionEncoding.assignValues(instruction) # The values of the given instruction
    #     existingValues = self.values # The values these should match






#Helper function to output the ASM template
def getASM(asmelement):
    output = ""
    for child in asmelement:
        output += child.text
    return output

# In an encoding, there will be boxes with var names and <c>s similar to in decoding - how is it different?

if __name__ == "__main__":
    i1 = InstructionPage("arm-files/abs.xml")
    instruction = "11011010110000000010001010010110"
    print(i1.matchClass(instruction).matchEncoding(instruction).asmTemplate)



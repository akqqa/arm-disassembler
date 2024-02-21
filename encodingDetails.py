from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys
from explanation import *

# Contains infor to match encodiong within a class, as well as the asmtemplate matching
class EncodingDetails():
    
    def __init__(self, root):
        # Create encodingDescription similar to instructionDescription in above class
        self.explanations = [] # List of explanations needed to fill the asm template
        self.asmTemplate = None # The asm template associated with this encoding
        self.name = root.attrib["name"] # The name of this encoding
        boxes = root.findall("box")
        self.encodingDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # The format of the instruction this encoding matches

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

#Helper function to output the ASM template
def getASM(asmelement):
    output = ""
    for child in asmelement:
        output += child.text
    return output
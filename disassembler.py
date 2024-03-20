# A file containing all classes required to create the data structures that allow for disassembly based on the Arm Specification

from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys
import os
from dotenv import load_dotenv

class InstructionPage():
    """
    The top level class of the disassembly process. Corresponds to an XML file for a particular instruction/family of instructions.

    Attributes:
        file - the file that this class represents
        classes - a list of classes contained within this page
        aliaslist - a list of possible aliases that this instruction can be replaced with
        encodings - all encodings in the XML file corresponding with this instruction
    """

    def __init__(self, file):
        """
        Initialises the class
        Constructs InstructionClass objects for each class in the file, and attaches each explanation in the file to their respective Encodings.

        :param file: the file that this class represents
        """

        self.file = file # The file this class represents
        self.classes = [] # The classes contained in this page
        self.aliaslist = None # The aliaslist node of the page
        self.encodings = []

        root = et.parse(file).getroot()
        #Aliases
        self.aliaslist = root.find("alias_list")
        #Class list
        classesSect = root.find("classes")
        classes = classesSect.findall("iclass")
        for c in classes:
            # add to self.classes the InstructionClass constructed from it
            self.classes.append(InstructionClass(c))
        # Add explanations to each encoding!
        # Get all encodings
        for c in self.classes:
            for e in c.encodingSections:
                self.encodings.append(e)
        explanations = root.find("explanations")
        for expXml in explanations:
            # create explanation, search all subclasses and encodings for names, append to encodings with the right names
            explanation = Explanation(expXml)
            for e in self.encodings:
                if e.name in explanation.enclist:
                    # add this explanation to this encoding
                    e.explanations.append(explanation)

    def matchClass(self, instString):
        """
        Given a binary string, finds the class that this string matches based on characteristics of each class.

        :param instString: The binary string of the instruction being matched with
        """
        for c in self.classes:
            matches = True
            description = c.instructionDescription
            matches = True
            # Extract all ZN strings alongside their starting indices in the string
            znStrings = re.finditer("[ZN]+", description)
            for match in znStrings:
                znString = match.group()
                startindex = match.start()
                # Convert zs and ns to 1s and 0s
                znString = znString.replace("Z", "0")
                znString = znString.replace("N", "1")
                # Check if the znString matches the substring from startindex to endindex. if so, this encoding is not correct
                if compareWithXs(znString, instString[startindex:startindex+len(znString)]):
                    matches = False # String wont match regardless of next part
            # Replaces all z's and n's with x, as already exited if invalid
            description = description.replace("Z", "x")
            description = description.replace("N", "x")
            # Checks each value in the description, and if they dont match, return false
            for i in range(0, len(description)):
                if instString[i] == description[i] or description[i] == "x":
                    continue
                else:
                    matches = False
            if matches:
                return c # Will return the correct class if all characters are equivalent

    def print(self):
        """ 
        Prints each class
        """
        for c in self.classes:
            c.print()

    def disassemble(self, instruction):
        """
        Takes an instruction and passes it to each subclass within the data structure, resulting in the correct assembly language instruction for the given binary instruction

        :param instruction: the machine code instruction to ddisassemble
        """
        # First, get correct class and encoding
        iClass = self.matchClass(instruction)
        encoding = iClass.matchEncoding(instruction)
        # Get values from instructionMapping
        values = iClass.instructionMapping.assignValues(instruction)
        # Check against aliases - if match, create instructionpage for the alias, then dissasemble that and return what it returns
        matchingAliases = self.matchAlias(values)
        # If any aliases match, create an instructionpage for the alias file, and disassemble that file and return that result
        # If there is an exception, try with the next alias in the list!
        # If whole list traversed without success, simply dont replace with an alias
        if len(matchingAliases) > 0:
            # Tries to traverse list, returning asm for each one. Every error, try the next one. If all error, simply dont use alias
            for matchingAlias in matchingAliases:
                try:
                    # Constructs new InstructionPage instead of using the ones already created, as the encodingIndex likely didnt create constructs for aliases!
                    aliasClass = InstructionPage(ARM_FILE_PATH + "/" + matchingAlias.attrib["aliasfile"])
                    asm = aliasClass.disassemble(instruction)
                    return asm
                except AttributeError:
                    # Match invalid but due to layout of table couldnt tell there was a different one to use
                    continue

        symbols = []
        # Get symbols from feeding values to each explanation
        for exp in encoding.explanations:
            symbols.append(exp.decodeSymbol(values))
        # Get asm, replace each symbol in the string with the binary value (for now)
        asm = encoding.asmTemplate

        # Optional section removal / retaining
        # If a bracketed section is found, and at least one of the symbols is non default, we keep this section
        matches = re.search("\{.*\}", asm)
        if matches:
            defaultSymbols = 0
            symbolsInBrackets = 0
            bracketed = matches.group(0)
            # Check if there is an <amount> in the symbols, and if it is 0
            for symbol in symbols:
                if symbol[0] in matches.group(0):
                    symbolsInBrackets += 1
                    # Here we define various default values and if any are non default we keep the bracketed section
                    # By default, show the extra info. if, however, it only these values, and they are all defaults, hide it
                    if symbol[0] == "<amount>" and symbol[1] == "0":
                        defaultSymbols += 1
                    if symbol[0] == "<pimm>" and symbol[1] == "0":
                        defaultSymbols += 1
                    if symbol[0] == "<simm>" and symbol[1] == "0":
                        defaultSymbols += 1
                    if symbol[0] == "<imm>" and symbol[1] == "0":
                        defaultSymbols += 1
                    if symbol[0] == "<Xn>" and symbol[1] == "x30":
                        defaultSymbols += 1
                    if symbol[0] == "<Xt>" and symbol[1] == "x31":
                        defaultSymbols += 1
                    if symbol[0] == "<shift>" and (symbol[1] == "0" or symbol[1] == "LSL #0"):
                        defaultSymbols += 1
            # Replace curly braces
            if defaultSymbols == symbolsInBrackets:
                asm = re.sub("\{.*\}", "", asm)
            else:
                asm = asm.replace("{", "")
                asm = asm.replace("}", "")

        # Replace each symbol with its corresponding value from the decodeSymbol() method
        for symbol in symbols:
            asm = asm.replace(symbol[0], symbol[1])
        return asm.lower()

    def matchAlias(self, values):
        """
        Given a tuple of values ((name, value),...), return a list of all matching aliases based on the condiitons within the aliaslist of this class
        
        :param values: the variables and values of each to use to check which alias conditions match
        """
        aliases = []
        if self.aliaslist is not None:
            aliasrefs = self.aliaslist.findall("aliasref")
            # Iterates through all possible aliases
            for aliasref in aliasrefs:
                aliasprefs = aliasref.findall("aliaspref")
                if aliasprefs is not None:
                    for aliaspref in aliasprefs:
                        # If aliaspref has an <a> tag, it is pseudocode, so skip
                        anchor = aliaspref.find("a")
                        if anchor is not None:
                            continue
                        # If the condition matches the values, append to the list that is returned
                        if aliaspref.text is not None:
                            if aliasCondCheck(aliaspref.text, values):
                                aliases.append(aliasref) 
        return aliases


class InstructionClass():
    """
    The class representing an individual instruction. Corresponds to each individual iclass in an XML file

    Attributes:
        root - the root of the iclass xml element being converted into this class
        instructionDescription - a string that describes the bit-pattern that this instruction matches. Used when comparing to an instruction to disassemble
        instructionMapping - the InstructionMapping used to extract variable values from any instructions being disassembled
        encodingSections - the possible encodings for this instruction, as a list of Encoding objects
    """

    def __init__(self, root):
        """
        Initialises the class
        Parses the regdiagram. Creating an instruction mapping for mapping variables, as well as an Instruction description to match instructions with the right class
        
        :param root: the root of the iclass xml element being converted into this class
        """

        self.root = root
        self.instructionDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Will result in a string that matches the given instruction
        self.instructionMapping = None # The mapping of the instruction - a.k.a the variables derived from the description
        self.encodingSections = None # The list of possible encodings - as in the encoding xml tags.
        
        variables = {}
        # Use the regdiagram to create instructionMapping for this table
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
            # Instruction form logic - accounts for != with larger colspans
            if "settings" in box.attrib:
                index = 31 - int(box.attrib["hibit"])
                # Create a string corresponding to the digits in this box
                instructionSection = ""
                characters = box.findall("c")
                for char in characters:
                    # If the c has colspan, find the characters it shouldnt be, convert them to Zs and Ns, then add to instructionSection
                    if "colspan" in char.attrib:
                        split = char.text.replace(" ", "").split("!=") # Like in decoding string of form 00 != 110, splits the string
                        # In the second half, replace 1's with Ns and 0's with Zs
                        split[1] = split[1].replace("1", "N")
                        split[1] = split[1].replace("0", "Z")
                        instructionSection += "".join(split)
                    else: # If the c is regular, and just contains one digit
                        if char.text == "0" or char.text == "1":
                            instructionSection += char.text
                        else:
                            instructionSection += "x"
                # Replace the characters at the index in the instructionDescription with this section
                self.instructionDescription = self.instructionDescription[:index] + instructionSection + self.instructionDescription[index + len(instructionSection):]
        self.instructionMapping = InstructionMapping(variables)

        # Encoding section - contains the asm isntruction based on certain conditions
        encodingSect = root.findall("encoding")
        # For now, just getting the mnemonics
        self.possibleAsm = []
        # Code for each encoding section
        self.encodingSections = []
        for e in encodingSect:
            self.encodingSections.append(EncodingDetails(e))

    def matchEncoding(self, instString):
        """
        Given an instruction, returns the correct encoding that corresponds to it

        :param instString: the binary string of the instruction to find the encoding for
        """

        # For each encoding, check if the encodingDescription matches the instString!
        # Must account for ZNN strings
        for e in self.encodingSections:
            matches = True
            encoding = e.encodingDescription
            # Extract all ZN strings alongside their starting indices in the string
            znStrings = re.finditer("[ZN]+", encoding)
            for match in znStrings:
                znString = match.group()
                startindex = match.start()
                # Convert zs and ns to 1s and 0s
                znString = znString.replace("Z", "0")
                znString = znString.replace("N", "1")
                # Check if the znString matches the substring from startindex to endindex. if so, this encoding is not correct
                if compareWithXs(znString, instString[startindex:startindex+len(znString)]):
                    matches = False # String wont match regardless of next part
            # Replaces all z's and n's with x, as already exited if invalid
            encoding = encoding.replace("Z", "x")
            encoding = encoding.replace("N", "x")
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
        """
        Prints information about the encoding
        """
        print(self.root.attrib["name"])
        print(self.instructionDescription)

class EncodingDetails():
    """
    A class to store the information about an encoding of an instruction. 

    Attributes:
        explanations - a list of the explanations that are required in order to replace the symbols in the corresponding assembly template with the correct values
        asmTemplate - the assembly template associated with this encoding
        name - the name of this encoding (for debugging purposes)
        encodingDescription - a string that describes the bit-pattern that this encoding matches. Used when comparing to an instruction to disassemble
    """
    
    def __init__(self, root):
        """
        Creates the class

        :param root: - the root xml element of the encoding being used
        """
        # Create encodingDescription similar to instructionDescription in above class
        self.explanations = [] # List of explanations needed to fill the asm template
        self.asmTemplate = None # The asm template associated with this encoding
        self.name = root.attrib["name"] # The name of this encoding
        boxes = root.findall("box")
        self.encodingDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # The format of the instruction this encoding matches

        # Formats the encodingDescription 
        for box in boxes:
            if "name" in box.attrib:
                index = 31 - int(box.attrib["hibit"])
                # Create a string corresponding to the digits in this box
                encodingSection = ""
                characters = box.findall("c")
                for char in characters:
                    if char.text == "0" or char.text == "1":
                        encodingSection += char.text
                    elif char.text == "Z" or char.text == "N":
                        encodingSection += char.text
                    else:
                        encodingSection += "x"
                # Replace the characters at the index in the encodingDescription with this section
                self.encodingDescription = self.encodingDescription[:index] + encodingSection + self.encodingDescription[index + len(encodingSection):]


        self.asmTemplate = getASM(root.find("asmtemplate"))
        return

class Explanation():
    """
    Class to store each explanation given in the XML files. An explanation is a description of how to retrieve the value of a specific symbol from an instruction for the assembly template

    Attributes:
        enclist - the list of encodings that this explanation is for
        symbol - the symbol that this explanation is for
        table - the table that the explanation might be formatted as
        encodedIn - the variables of the instruction that this symbol is encoded with
        bitmaskImmediate - whether this explanation is encoded as a bitmask immediate
        bitmaskSize - the size of the bitmask immediate (if applicable)
        implicitValue - the implict value of this explanation if one is given
        signed - whether this explanation is for a signed integer
        multipleOf - if this explanation requires a multiplcation, the value to multiply by
        equation - if this explanation contains an equation, the equation to use to get the symbols value
        stackPoints - whether this symbol is referring to a stack pointer instead of a regular register
    """

    def __init__(self, root):
        """
        Creates the class
        Determines whether the explanation is encoded in a table or text. If a table, constructs that table as a 2d array. If text, parses the text to extract relevant information to be used when decoding

        :param root: the root xml element of the explanation used to create this class
        """

        self.enclist = root.attrib["enclist"].replace(" ", "").split(",")
        self.symbol = root.find("symbol").text
        self.table = []
        self.bitmaskImmediate = False
        self.bitmaskSize = None
        self.implicitValue = None
        self.signed = False
        self.multipleOf = None
        self.equation = None
        self.stackPointer = False
        # If no account, then is a table as non-tables use definition instead
        if root.find("account") == None:
            # If the first col is size, and the last includes M:Rm, encodedIn is size:M:Rm
            self.encodedIn = html.unescape(root.find("definition").attrib["encodedin"])

            # create table - row by row as a 2d array in self.table
            tableRoot = root.find("definition").find("table")
            tableHead = tableRoot.find("tgroup").find("thead")
            headEntries = tableHead.find("row").findall("entry")
            currentRow = []
            # Create header row
            for entry in headEntries:
                currentRow.append(entry.text)
            self.table.append(currentRow)
            tableBody = tableRoot.find("tgroup").find("tbody")
            rows = tableBody.findall("row")
            # Create each row of the table from the xml
            for row in rows:
                currentRow = []
                entries = row.findall("entry")
                for entry in entries:
                    currentRow.append(entry.text)
                self.table.append(currentRow)
            # Create a variable storing the index of the row that the results reside in (not always the last, as sometimes describes features)
            self.tableResultIndex = -1
            for i in range(0, len(headEntries)):
                if headEntries[i].attrib["class"] == "symbol":
                    self.tableResultIndex = i
                    break # line 221 of msr_imm.xml has an error where architectural features should be class feature not symbol, but in any case, default to the first symbol
        # Not a table, so parse the text
        else:
            # Uses https://stackoverflow.com/a/11122355 for getting quote indices
            symbolEncodingText = root.find("account").find("intro").find("para").text
            # Check if bitmask immediate - -usually says "bitmask immediate", but in some cases such as eor_z_zi_ it just has "bitmask"
            if "bitmask" in symbolEncodingText:
                self.bitmaskImmediate = True
                if "64-bit" in symbolEncodingText:
                    self.bitmaskSize = 64
                elif "32-bit" in symbolEncodingText:
                    self.bitmaskSize = 32
            # Check if implicit value
            implicit = re.search("implicit value (\d+)\.", symbolEncodingText)
            if implicit is not None:
                self.implicitValue = implicit.group(1)
            # Check if signed - space beforehand to exlcude "unsigned"
            if " signed immediate" in symbolEncodingText:
                self.signed = True
            # Check if multiple of - checks for both "multiple of" and the "/" symbol - both are used to mean multiple by the following number, but not used consistently
            multiple = re.search("multiple of (\d+)", symbolEncodingText)
            divide = re.search("\>/(\d+)", symbolEncodingText)
            if multiple is not None:
                self.multipleOf = int(multiple.group(1))
            elif divide is not None:
                self.multipleOf = int(divide.group(1))

            quoteIndicies = [i for i, ltr in enumerate(symbolEncodingText) if ltr == "\""]
            # Further special case if no encoding - for not just assume it will always be zero - case fo the mova.. instructions for 128 bits
            # this was originally erroneously made to ignore encodedIn. possibly due to an issue with the xml formatting not sensing multiple " in text. preferred fallback is to the encodedin.
            if len(quoteIndicies) != 2:
                self.encodedIn = html.unescape(root.find("account").attrib["encodedin"])
                return
            self.encodedIn = symbolEncodingText[quoteIndicies[0]+1:quoteIndicies[1]]

            # Furthermore, for possible mathematical operations, grab all text between "encoded as" and "." if present
            match = re.search("encoded as (.*)\.", symbolEncodingText)
            self.equation = None
            if match: # transform and save the resulting equation
                # replace the symbol (in quotes), with the variable x
                self.equation = re.sub("\".*\"", "x", match.group(1)).replace("field", "")

            # Check if contains a stack pointer
            if "stack pointer" in symbolEncodingText:
                self.stackPointer = True

    def decodeSymbol(self, values):
        """
        Takes a list of values, and from this calculates what this classes' symbol should be replaced with. Returns a tuple of the form 

        :param values: a tuple of tuples the same format output by the InstructionMapping class
        """
        # special case for mova on 128 bits, return 0 for an encoding of ""
        if self.encodedIn == "":
            return (self.symbol, "0")

        # If the explanation uses a table, search the stored table to find the mapping
        if self.table != []:
            rowLength = len(self.table[0])
            values = list(values)
            # Using the header row, create a list matching the variables in the columns to match
            matchList = []
            for i in range(0, len(self.table[0])-1):
                var = self.table[0][i]
                match = [tup[1] for tup in values if tup[0] == var]
                matchList = matchList + match
            # Then iterate through each row, matching the list of expected values
            matchingRow = None
            for row in self.table:
                rowVars = row[:self.tableResultIndex]
                if (all([compareWithXs(fst, snd) for fst, snd in zip(rowVars, matchList)])): #zips rowVars and matchList, then compares each element accounting for xs to check if the lists match
                    matchingRow = row
            if matchingRow == None:
                return (self.symbol, "") # Cannot find a matching row. This occurs when the assembly is referencing a label that this program has no knowledge about. For now, it simply gives a blank symbol.
            
            # Once found, get the final result

            # Intead of getting the last in the row, get the one that is actually the symbol - see arm-files/msr_imm.xml
            # Result is stored in the nth element, where n is the tableResultIndex constructed when the table was built
            result = matchingRow[self.tableResultIndex]

            # Handle things such as H<4:3>:imm4. Unlike in non-table, sometimes doesnt convert to integers, therefore uses the UInt method.
            if "UInt(" in result:
                # Finds all UInt() sections in the asm, and handles their inner elements, replacing them with the final value
                functions = re.finditer("UInt\\((.*)\\)", result)
                # If none, just caclulateConcatSymbols normally, as can assume its across the whole element
                for m in functions:
                    replacement = calculateConcatSymbols(m.group(1), values) # Only does this in a table as in non-table it always treats it as separated by brackets.
                    # Convert to decimal if possible
                    replacement = str(int(replacement, 2))
                    result = result.replace(m.group(0), replacement)

            # Account for #uimm5 and #uimm4 referring to their own pattern
            # Assumptions : always uimm4 or uimm5, and only has one other row in the table
            # Not very robust, but since theres no documentation cant really tell what its meant to mean!
            if "uimm5" in result:
                result = result.replace("uimm5", str(int(calculateConcatSymbols(self.encodedIn, values),2)))
            if "uimm4" in result:
                result = result.replace("uimm4", str(int(calculateConcatSymbols(self.encodedIn, values),2)))

            # Handle special case of [absent] and [present]
            if result == "[absent]":
                result = ""
            elif result == "[present]":
                result = self.symbol

            # Handle potential subtraction (if form digits - digits perform the subtraction)
            subtraction = re.match("(\d+) - (\d+)", result)
            if subtraction is not None:
                result = str(int(subtraction.group(1)) - int(subtraction.group(2)))

            # Checks the prefix of the symbol to tell if it requires a register prefix or not
            registerPrefixTest = re.search("([WXVQDSHBZCP]|PN|ZA)[nmdtasgv]", self.symbol)
            if registerPrefixTest is not None:
                # Handles special case of w31 or x31 referring to a zero register or stack pointer
                if (("W" in self.symbol or "X" in self.symbol) and result == "31"):
                    if self.stackPointer:
                        return (self.symbol, "sp")
                    else:
                        result = "zr"
                if not ("Va" in self.symbol) and not ("Vb" in self.symbol): # These were the only two outliers found for tables compared to text encodings
                    # Add register prefix to result
                    result = registerPrefixTest.group(1).lower() + result
                return (self.symbol, result)

            return (self.symbol, result)

        # If no table, simply find the variable the symbol is encoded in, and return this (taking into account indexing with <> after symbol)
        else:
            result = ""
            result = calculateConcatSymbols(self.encodedIn, values) # Calculates the base value from the variables that it is encoded in

            # Check if bitmask immediate, and if so decode the result as a bitmask immediate
            if self.bitmaskImmediate:
                result = decodeBitmaskImmediate(result, self.bitmaskSize)

            # Convert binary to int - if it is signed, use twos complement, otherwise directly translate to binary
            if self.signed:
                result = str(twosComplement(result))
            else:
                result = str(int(result, 2))

            if self.multipleOf:
                result = str(self.multipleOf * int(result))

            #if equation not None, use own stack method to calcuate what the true result should be
            if self.equation is not None:
                # Uses the result calculated to be the value of the encoded symbol
                result = str(evaluateEquation(self.equation, result))
            
            # if implicit value was given, result is this
            if self.implicitValue is not None:
                result = self.implicitValue

            # Originally simply assumed if starting with capital WXVQDSHBZCP would be a register prefix. using this, foudn the regex ([WXVQDSHBZCP]|PN)[nmdtasgv] by refining until the difference between it and the original were nonexistant
            registerPrefixTest = re.search("([WXVQDSHBZCP]|PN)[nmdtasgv]", self.symbol)
            if registerPrefixTest is not None:
                # Handles special case of w31 or x31 referring to a zero register or stack pointer
                if (("W" in self.symbol or "X" in self.symbol) and result == "31"):
                    if self.stackPointer:
                        return (self.symbol, "sp")
                    else:
                        result = "zr"
                # Add register prefix to result
                result = registerPrefixTest.group(1).lower() + result

            return (self.symbol, result)
from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys

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
# superclass goes through each class, matches the instructionMappings
# once correct iclass found, can get an object of the correct symbols
# use pseudocode to map symbols
# superclass can map these to the symbols, then the asmtemplate used!

#explanation class
# created per explanation xml, stores symbol, encoded in and potentialy table
# created by instructionpage, put into every relevant encoding
# method to take in an encoding map, and return the symbol and value!


# HOW TO WORK - updated
# When an instruction is receieved to be decoded, perform the following, in the instructionpage class:
# match the instruction class the instruction is a part of
# get the isntruction encoding of this instruction, to extract the variables
# match the encoding the instruction belongs to
# get a lisdt of the variables / map or whatever it is
# for each explanation in the encoding, use the variable map to get the correct value
# place these values in the asmtemplate of the encoding
# return this template with values substituted in :)

# The page for an intstruction - corresponds to an xml file on a particular instruction
class InstructionPage():

    def __init__(self, file):
        self.file = file # The file this class represents
        self.classes = [] # The classes contained in this page
        self.aliaslist = None # The aliaslist node of the page

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
        self.encodings = []
        # Get all encodings
        for c in self.classes:
            for e in c.encodingSections:
                self.encodings.append(e)
        explanations = root.find("explanations")
        for expXml in explanations:
            #print(file)
            # create explanation, search all subclasses and encodings for names, append to encodings with the right names
            explanation = Explanation(expXml)
            for e in self.encodings:
                if e.name in explanation.enclist:
                    # add this explanation to this encoding
                    e.explanations.append(explanation)

    def matchClass(self, instString):
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
            for i in range(0, len(description)):
                #print(instString[i])
                if instString[i] == description[i] or description[i] == "x":
                    continue
                else:
                    matches = False
            if matches:
                return c # Will return the correct class

    def print(self):
        for c in self.classes:
            c.print()

    # Should have a diassemble method, which performs all steps in subclasses it contains to decode and disassemble a given binary instruction
    def disassemble(self, instruction):
        # First, get correct class and encoding
        iClass = self.matchClass(instruction)
        encoding = iClass.matchEncoding(instruction)
        # Get values from instructionMapping
        values = iClass.instructionMapping.assignValues(instruction)
        # CHECK AGAINST ALIASES - IF MATCH, CREATE INSTRUCTIONPAGE FOR THE ALIAS, THEN DISSASEMBLE THAT AND RETURN WHAT IT RETURNS
        matchingAliases = self.matchAlias(values)
        # If any aliases match, create an instructionpage for the alias file, and disassemble that file and return that result
        # If there is an exception, try with the next alias in the list!
        # If whole list traversed without success, simply dont replace with an alias
        if len(matchingAliases) > 0:
            # Tries to traverse list, returning asm for each one. Every error, try the next one. If all error, simply dont use alias
            for matchingAlias in matchingAliases:
                try:
                    aliasClass = InstructionPage("arm-files/" + matchingAlias.attrib["aliasfile"])
                    asm = aliasClass.disassemble(instruction)
                    return asm
                except AttributeError:
                    print("error")
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
            #print(matches.group(0))
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
            if defaultSymbols == symbolsInBrackets:
                asm = re.sub("\{.*\}", "", asm)
            else:
                asm = asm.replace("{", "")
                asm = asm.replace("}", "")

        for symbol in symbols:
            asm = asm.replace(symbol[0], symbol[1])
        return asm

    # Given the tuple of values ((name, value),...), return a list of all matching aliases
    def matchAlias(self, values):
        aliases = []
        if self.aliaslist is not None:
            aliasrefs = self.aliaslist.findall("aliasref")
            #print(self.file)
            for aliasref in aliasrefs:
                aliasprefs = aliasref.findall("aliaspref")
                if aliasprefs is not None:
                    for aliaspref in aliasprefs:
                        # If aliaspref has an <a> tag, it is pseudocode, so skip
                        anchor = aliaspref.find("a")
                        if anchor is not None:
                            continue
                        if aliaspref.text is not None:
                            if aliasCondCheck(aliaspref.text, values):
                                aliases.append(aliasref) 
        return aliases


# The class of an instruction - corresponds to each individual iclass in an xml file
class InstructionClass():

    def __init__(self, root):
        # Parse the regdiagram. Creating an instruction mapping for mapping variables, as well as an Instruction description to match instructions with the right class
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
            # Instruction form logic - ACCOUNTS FOR != WITH LARGER COLSPANS
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
        print(self.root.attrib["name"])
        print(self.instructionDescription)

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
                    elif char.text == "Z" or char.text == "N":
                        encodingSection += char.text
                    else:
                        encodingSection += "x"
                # Replace the characters at the index in the encodingDescription with this section
                self.encodingDescription = self.encodingDescription[:index] + encodingSection + self.encodingDescription[index + len(encodingSection):]


        self.asmTemplate = getASM(root.find("asmtemplate"))
        #print(self.encodingDescription)
        return



# Class to store each explanation. Has a symbol, encodedin, and potentially a table.
# give a method that takes in an encoding map, and returns the correct symbol and value!
class Explanation():

    # Here, root is <explanation>
    def __init__(self, root):
        self.enclist = root.attrib["enclist"].replace(" ", "").split(",")
        self.symbol = root.find("symbol").text
        self.table = []
        self.bitmaskImmediate = False
        self.implicitValue = None
        self.signed = False
        self.multipleOf = None
        self.equation = None
        # If no account, then is a table as uses definition instead
        if root.find("account") == None:
            # If the first col is size, and the last includes M:Rm, encodedIn is size:M:Rm
            self.encodedIn = html.unescape(root.find("definition").attrib["encodedin"])
            # From reading over various xml files, gathered that tables always use encodedIn, if find something contrary, adjust as in the account version below

            # create table - row by row as a 2d array in self.table
            tableRoot = root.find("definition").find("table")
            tableHead = tableRoot.find("tgroup").find("thead")
            headEntries = tableHead.find("row").findall("entry")
            currentRow = []
            for entry in headEntries:
                currentRow.append(entry.text)
            self.table.append(currentRow)
            tableBody = tableRoot.find("tgroup").find("tbody")
            rows = tableBody.findall("row")
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
        else:
            # UNFORTUNATELY - as seen in umov_advsimd.xml under index, encodedin can give the wrong thing, in the case of e.g subindexing the endcoded in, as it is only given in para. must instead parse para for it when no table
            # luckily, this is just found by what is in the "" in the para
            #self.encodedIn = root.find("account").attrib["encodedin"]
            # Uses https://stackoverflow.com/a/11122355 for getting quote indices
            symbolEncodingText = root.find("account").find("intro").find("para").text
            # Check if bitmask immediate
            if "bitmask immediate" in symbolEncodingText:
                self.bitmaskImmediate = True
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

            # REDUNDANT NOTES NEEDED IF TURNS OUT THAT THERE ARE CASES WHERE NO INTRO PRESENT FOR NON-TABLE EXPLANATIONS
            # slightly more complex, as in cases of size:Q, only encoding, no para with "encoded in" message
            # solution: check for para with "", if so encodedIn is in these quotes, otherwise is the encodedIn attrib :)
            # so: search for intro then para, then get text, parse out "" if exists
            # otherwise use encodedin attrib


    # Values is a tuple of tuples ((imm, 01001), (Rn, 1101), ...)
    # Returns a tuple - (the symbol the value has been found for, and the resulting value)

    # explanation on calculateconcat vs splitwithbrackets. if not in a table, never uses uint as it is implied to be converted to numbers always. therefore can just straight split based on colons
    # however, tables use both alphanumeric values AND unit conversions depending on the table values, so this uses splitwithbrackets
    def decodeSymbol(self, values):
        # special case for mova on 128 bits, return 0 for an encoding of ""
        if self.encodedIn == "":
            return (self.symbol, "0")

        # SPECIAL CASE: https://developer.arm.com/documentation/ddi0602/2023-12/SIMD-FP-Instructions/UMOV--Unsigned-Move-vector-element-to-general-purpose-register-
        # <row>
        #     <entry class="bitfield">xxxx1</entry>
        #     <entry class="symbol">imm5&lt;4:1&gt;</entry>
        # </row>
        # believe that imm5<4:1> is stating to get the 5th (from the end) and 2nd (from the end) bit of imm5?
        # so do an additional check for <>'s, if so handle accordingly separate to other : splits

        # Search the stored table to find the mapping
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
                print(self.enclist,file=sys.stderr)
                print("Error: could not match the table - invalid machine code given OR unknown label present", file=sys.stderr)
                print(values, file=sys.stderr)
                return (self.symbol, "") # For now, just return it as empty. However, this occurs when https://developer.arm.com/documentation/ddi0602/2023-12/Base-Instructions/LDRB--register---Load-Register-Byte--register--?lang=en
                # basically some encoding is used when option != 011, another when option == 011. This is jusut always doing the first, so error when it is 011 and nothing defined for it!
            # Once found, get the final result
            # NOTE FINAL RESULT COULD BE OF FORM IMM5<4:1> SO TAKE THIS INTO ACCOUNT TOO

            # Intead of getting the last in the row, get the one that is actually the symbol - see arm-files/msr_imm.xml
            # Result is stored in the nth element, where n is the tableResultIndex constructed when the table was built
            result = matchingRow[self.tableResultIndex]

            # Handle things such as H<4:3>:imm4. Unlike in non-table, sometimes doesnt convert to integers
            if "UInt(" in result:
                # Finds all UInt() sections in the asm, and handles their inner elements, replacing them with the final value
                functions = re.finditer("UInt\\((.*)\\)", result)
                # If none, just caclulateConcatSymbols normally, as can assume its across the whole element
                for m in functions:
                    replacement = calculateConcatSymbols(m.group(1), values) # ONLY DOES THIS IN TABLE AS IN NON-TABLE IT ALWAYS JUST TREATS IT AS separated by brackets. this assumes that 
                    # Convert to decimal if possible
                    replacement = str(int(replacement, 2))
                    result = result.replace(m.group(0), replacement)
            #else: # Otherwise assumes the whole string is able to be split by colons - IF DOES THIS, ERROR WHEN USING A SYMBOL THAT ISNT CONVERTED TO ITS INT LIKE 1 AND H
            # why? because calculate concat symbols assumes that the H is the value of the variable, rather than simply the character "H". 
            # Simply have to make the assumption that colons will only be used in tables if integers, otherwise it makes zero sense. why would you say "H:B:S" instead of HBS?
            # and if you want H + the value imm4 you can do H:Uint(imm4). NON-TABLE ALWAYS ASSUMES CONVERSION TO NUMBERS, TABLE IS USED WHEN NOT NUMBERS - TAHTS THE WHOLE POINT
                #result = calculateConcatSymbols(result, values)

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

            # Unfortunately not consistent with the non-table forms. e.g Va and Vb in SQRSHRN describe the prefix rather than require it!!
            registerPrefixTest = re.search("([WXVQDSHBZCP]|PN)[nmdtasgv]", self.symbol)
            if registerPrefixTest is not None:
                if not ("Va" in self.symbol) and not ("Vb" in self.symbol): # These were the only two outliers found
                    # Add register prefix to result
                    result = registerPrefixTest.group(1).lower() + result
                return (self.symbol, result)
            
        
            return (self.symbol, result)
        # If no table, simply find the variable the symbol is encoded in, and return this (taking into account indexing with <> after symbol)
        else:
            result = ""
            result = calculateConcatSymbols(self.encodedIn, values)

            # Check if bitmask immediate, and if so decode the result as a bitmask immediate
            if self.bitmaskImmediate:
                result = decodeBitmaskImmediate(result)

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

            # Manually add X or W - note also V for vector? - should add a more complex check as can have V or Vd
            # https://valsamaras.medium.com/arm-64-assembly-series-basic-definitions-and-registers-ec8cc1334e40#:~:text=The%20AArch64%20architecture%20also%20supports,(using%20b0%20to%20b31).
            # ^ gives all possible register prefixes
            # maybe z as well?
            # Originally simply assumed if starting with capital WXVQDSHBZCP would be a register prefix. using this, foudn the regex ([WXVQDSHBZCP]|PN)[nmdtasgv] by refining until the difference between it and the original were nonexistant
            registerPrefixTest = re.search("([WXVQDSHBZCP]|PN)[nmdtasgv]", self.symbol)
            if registerPrefixTest is not None:
                # Add register prefix to result
                result = registerPrefixTest.group(1).lower() + result

            return (self.symbol, result)


if __name__ == "__main__":
    print(splitWithBrackets("imm5<4:3>:imm4<3>"))
    print(calculateConcatSymbols("imm5<4:3>:imm4<3>", [("imm5", "111111"), ("imm4", "1111111")]))
    match = re.search("encoded as (.*)\.", "this is encoded as \"rx\" plus 2 times 5.")
    print(match[1])
    print(evaluateEquation(re.sub("\".*\"", "x", "\"rx\" plus 5 minus 4").replace("field", ""), 8))
    # i1 = InstructionPage("arm-files/abs.xml")
    # instruction = "11011010110000000010001010010110"
    # print(i1.matchClass(instruction).matchEncoding(instruction).explanations[0].symbol)
    # print(i1.disassemble(instruction))
    print(aliasCondCheck("S == '1' && Pn == '10x' && (S != '1' || Pn == '1xx')", (("S", 1), ("Pn", "101"), ("Pm", 100))))
    print((boolean.BooleanAlgebra().parse("TRUE and TRUE AND ( FALSE or TRUE )")).simplify())
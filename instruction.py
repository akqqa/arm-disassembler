from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean

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
        self.file = file
        self.classes = []
        root = et.parse(file).getroot()
        #Aliases
        self.aliaslist = root.find("alias_list")
        #Class list
        classesSect = root.find("classes")
        classes = classesSect.findall("iclass")
        for c in classes:
            # add to self.classes the InstructionClass constructed from it
            self.classes.append(InstructionClass(c))
        # Add explanations to each encoding
        self.encodings = [] # Is there even a point in instruction class? is is not easier to just use the encodings stored here?
                            # YES! because it contains the regdiagram that will be needed for variable extraction :)
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

    # Should have a diassemble method, which performs all steps in subclasses it contains to decode and disassemble a given binary instruction
    def disassemble(self, instruction):
        # First, get correct class and encoding
        iClass = self.matchClass(instruction)
        encoding = iClass.matchEncoding(instruction)
        # Get values from instructionencoding
        values = iClass.instructionEncoding.assignValues(instruction)
        # CHECK AGAINST ALIASES - IF MATCH, CREATE INSTRUCTIONPAGE FOR THE ALIAS, THEN DISSASEMBLE THAT AND RETURN WHAT IT RETURNS
        matchingAlias = None
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
                                print("alias match!")
                                matchingAlias = aliasref
                                break
            # If any aliases match, create an instructionpage for the alias file, and disassemble that file and return that result
            if matchingAlias is not None:
                aliasClass = InstructionPage("arm-files/" + matchingAlias.attrib["aliasfile"])
                return aliasClass.disassemble(instruction)


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
            keep = False
            bracketed = matches.group(0)
            if "<amount>" in bracketed: #change this
                # Check if there is an <amount> in the symbols, and if it is 0
                for symbol in symbols:
                    # Here we define various default values and if any are non default we keep the bracketed section
                    # UPDATE FOR MORE NON-DEFAULT SYMBOLS TO BE FOUND
                    if symbol[0] == "<amount>" and symbol[1] != "0":
                        keep = True # Keep the brackets
                    if symbol[0] == "<pimm>" and symbol[1] != "0":
                        keep = True # Keep the brackets
                    if symbol[0] == "<simm>" and symbol[1] != "0":
                        keep = True # Keep the brackets
                    if symbol[0] == "<imm>" and symbol[1] != "0":
                        keep = True # Keep the brackets
                    if symbol[0] == "<Xn>" and symbol[1] != "x30":
                        keep = True # Keep the brackets
            if not keep:
                asm = re.sub("\{.*\}", "", asm)
            else:
                asm = asm.replace("{", "")
                asm = asm.replace("}", "")

        for symbol in symbols:
            asm = asm.replace(symbol[0], symbol[1])
        return asm




# The class of an instruction - correspodns to each individual iclass in an xml file
class InstructionClass():

    def __init__(self, root):
        # Parse the regdiagram. Creating an instruction encoding for mapping variables, as well as an Instruction description to match instructions with the right class
        self.root = root
        variables = {}
        self.instructionDescription = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Will result in a string that matches the given instruction
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
        self.explanations = []
        self.name = root.attrib["name"]
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

# Class to store each explanation. Has a symbol, encodedin, and potentially a table.
# give a method that takes in an encoding map, and returns the correct symbol and value!
class Explanation():

    # Here, root is <explanation>
    def __init__(self, root):
        self.enclist = root.attrib["enclist"].replace(" ", "").split(",")
        self.symbol = root.find("symbol").text
        self.table = []
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
        else:
            # UNFORTUNATELY - as seen in umov_advsimd.xml under index, encodedin can give the wrong thing, in the case of e.g subindexing the endcoded in, as it is only given in para. must instead parse para for it when no table
            # luckily, this is just found by what is in the "" in the para
            #self.encodedIn = root.find("account").attrib["encodedin"]
            # Uses https://stackoverflow.com/a/11122355 for getting quote indices
            encodingText = root.find("account").find("intro").find("para").text
            # if "encoded as" in encodingText and "vector" not in encodingText:
            #     print(encodingText)
            quoteIndicies = [i for i, ltr in enumerate(encodingText) if ltr == "\""]
            # Further special case if no encoding - for not just assume it will always be zero - case fo the mova.. instructions for 128 bits
            if len(quoteIndicies) != 2:
                self.encodedIn = ""
                return
            self.encodedIn = encodingText[quoteIndicies[0]+1:quoteIndicies[1]]

            # Furthermore, for possible mathematical operations, grab all text between "encoded as" and "." if present
            match = re.search("encoded as (.*)\.", encodingText)
            self.equation = None
            if match: # transform and save the resulting equation
                # replace the symbol (in quotes), with the variable x
                self.equation = re.sub("\".*\"", "x", match.group(1)).replace("field", "")
                # # replace mathematical words with symbols
                # match = match.replace("times", "*")
                # match = match.replace("plus", "+")
                # match = match.replace("modulo", "%")
                # match = match.replace("minus", "-")
                # # remove "field"
                # match = match.replace("field", "")
                # save equation
                #self.equation = match

            # REDUNDANT NOTES NEEDED IF TURNS OUT THAT THERE ARE CASES WHERE NO INTRO PRESENT FOR NON-TABLE EXPLANATIONS
            # slightly more complex, as in cases of size:Q, only encoding, no para with "encoded in" message
            # solution: check for para with "", if so encodedIn is in these quotes, otherwise is the encodedIn attrib :)
            # so: search for intro then para, then get text, parse out "" if exists
            # otherwise use encodedin attrib


    # Values is a tuple of tuples ((imm, 01001), (Rn, 1101), ...)
    # Returns a tuple - (the symbol the value has been found for, and the resulting value)
    def decodeSymbol(self, values):
        # special case for mova on 128 bits, return 0 for an encoding of ""
        if self.encodedIn == "":
            return (self.symbol, "0")
        # Must account for : - simply get each simple, and combine the values! - normal is just a special case of : where there are none to append
        encodedList = splitWithBrackets(self.encodedIn)

        # SPECIAL CASE: https://developer.arm.com/documentation/ddi0602/2023-12/SIMD-FP-Instructions/UMOV--Unsigned-Move-vector-element-to-general-purpose-register-
        # <row>
        #     <entry class="bitfield">xxxx1</entry>
        #     <entry class="symbol">imm5&lt;4:1&gt;</entry>
        # </row>
        # believe that imm5<4:1> is stating to get the 5th (from the end) and 2nd (from the end) bit of imm5?
        # so do an additional check for <>'s, if so handle accordingly separate to other : splits
        #print(encodedList)

        # If no table, simply find the variable the symbol is encoded in, and return this (taking into account indexing with <> after symbol)
        if self.table == []:
            result = ""
            for sym in encodedList:
                # Remove anything after < as this is ignored to match the possible symbols - https://stackoverflow.com/a/904756
                symStrip = sym.split("<", 1)[0]
                for tup in values:
                    if tup[0] == symStrip:
                        result += tup[1]
            # If has indices for parts of the binary, extract them and extract the correct ones from result
            if "<" in sym:
                indexes = sym.split("<",1)[1][:-1]
                # Split by colons
                indexes = indexes.split(":")
                # Get each digit from result and concatenate to get new result
                length = len(result)-1
                normIndexes = [length - int(x) for x in indexes]
                newResult = ""
                #slice using indicies
                newResult = result[normIndexes[0]:normIndexes[1]+1]
                result = newResult
            # Convert binary to int
            result = str(int(result, 2))

            #if equation not None, use own stack method to calcuate what the true result should be
            if self.equation is not None:
                # Uses the result calculated to be the value of the encoded symbol
                result = str(evaluateEquation(self.equation, result))

            # Manually add X or W - note also V for vector? - should add a more complex check as can have V or Vd
            # https://valsamaras.medium.com/arm-64-assembly-series-basic-definitions-and-registers-ec8cc1334e40#:~:text=The%20AArch64%20architecture%20also%20supports,(using%20b0%20to%20b31).
            # ^ gives all possible register prefixes
            # maybe z as well?
            if (len(self.symbol) > 1):
                if (self.symbol[1] == "W"):
                    result = "w" + result
                elif (self.symbol[1] == "X"):
                    result = "x" + result
                elif (self.symbol[1] == "V"):
                    result = "v" + result
                elif (self.symbol[1] == "Q"):
                    result = "q" + result
                elif (self.symbol[1] == "D"):
                    result = "d" + result
                elif (self.symbol[1] == "S"):
                    result = "s" + result
                elif (self.symbol[1] == "H"):
                    result = "h" + result
                elif (self.symbol[1] == "B"):
                    result = "b" + result
            return (self.symbol, result)

        # Search the stored table to find the mapping
        else:
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
                rowVars = row[:-1]
                if (all([compareWithXs(fst, snd) for fst, snd in zip(rowVars, matchList)])): #zips rowVars and matchList, then compares each element accounting for xs to check if the lists match
                    matchingRow = row
            if matchingRow == None:
                print("Error: could not match the table - invalid machine code given")
                print(values)
                quit()
            # Once found, get the final result
            # NOTE FINAL RESULT COULD BE OF FORM IMM5<4:1> SO TAKE THIS INTO ACCOUNT TOO
            result = matchingRow[-1]
            splitResult = splitWithBrackets(result) # This is the set of things to concatenate to get the result
            finalResult = ""
            for elem in splitResult: # Each elem is H, B, imm5 in H:B:imm5
                # Check if the element has <>
                # For each element, check if it is a name in values, and replace with that, otherwise leave alone
                val = [tup[1] for tup in values if tup[0] == elem.split("<", 1)[0]]
                if len(val) != 0:
                    if "<" in elem:
                        indexes = elem.split("<",1)[1][:-1]
                        # Split by colons
                        indexes = indexes.split(":")
                        # Get each digit from result and concatenate to get new result
                        length = len(val[0])-1
                        result = ""
                        for index in indexes:
                            result += val[0][length - int(index)]
                    finalResult += str(int(result, 2))
                else:
                    finalResult += elem
            # split by colons, replace with values in values, then concat and return
            return (self.symbol, finalResult)

#Helper function to output the ASM template
def getASM(asmelement):
    output = ""
    for child in asmelement:
        output += child.text
    return output

# Helper function to split a string by colons, not including any colons inside &lt/&rt (</>)
# e.g imm5<4:3>:imm4<3> = [imm5<4:3>, imm4<3>]
def splitWithBrackets(inputStr):
    # using https://stackoverflow.com/a/15599760
    # All < must have an associated > to be well formed in the specification. Using this we can find the indices of each and only split on colons not between these
    openingIndexes = [x.start() for x in re.finditer("<", inputStr)]
    closingIndexes = [x.start() for x in re.finditer(">", inputStr)]
    ranges = list(zip(openingIndexes, closingIndexes))
    toSplit = []
    splitList = []
    for i in range(0, len(inputStr)):
        char = inputStr[i]
        if char == ":":
            split = True # by default splits, unless found to be between brackets
            for group in ranges:
                if group[0] < i < group[1]: # colon shouldnt be split as between <>
                    split = False
            # Split if found to be in no groups
            if split:
                toSplit.append(i)
    # Now using toSplit, split string on each index
    start = 0
    for index in toSplit:
        splitString = inputStr[start:index]
        splitList.append(splitString)
        start = index+1
    # Finally add last substring to the list
    splitList.append(inputStr[start:])
    return splitList

# Helper method to evaluate equations of the form "x times 5 plus 2 modulo 3"
def evaluateEquation(equation, x):
    # Split by whitespace
    equation = equation.split()
    # Substitute x for the correct value
    equation = [x if z == "x" else z for z in equation]
    # Take every second value and place into an integer list
    numbers = [int(x) for x in equation[::2]]
    operations = equation[1::2]
    # For each operation, operate on the first two items of the list
    for op in operations:
        fst = numbers.pop(0)
        snd = numbers.pop(0)
        if op == "times":
            result = fst * snd
        elif op == "plus":
            result = fst + snd
        elif op == "minus":
            result = fst - snd
        elif op == "modulo":
            result = fst % snd
        numbers.insert(0, result)
    return numbers[0]

# Given an alias pref string and the values of symbols, checks if the condition string is valid with the given symbols
# Similar to the equation parsing but more complex as can have ==, !=, && and (||)
# Likely can use a premade boolean logic library. extract all x == y or x != y, replace them with True or False, then evaluatte logically!
def aliasCondCheck(condition, values):

    condition = condition.replace("'", "")
    condition = condition.replace("(", "( ")
    condition = condition.replace(")", " )")

    # Step 0: somehow detect if using pseudocode and dont evaluate if so, ignore these aliases
    # Easy to detect! just check if the aliaspref contains an <a> tag inside, do this before the condcheck
    
    # Step 1: replace all symbols with their corresponding values
    # Split by whitespace, to ensure doesnt replace part of substring with somthing. e,g a and Ra, could replace both a's
    splitCond = condition.split(" ")
    for i in range(0, len(splitCond)):
        for tup in values:
            if splitCond[i] == tup[0]:
                #print("HI")
                splitCond[i] = str(tup[1])
    condition = " ".join(splitCond)

    #print(condition)

    # Now have a string of form 1 == 1 && 101 == 100

    # Step 2: extract all x ==/!= y and evaluate each
    # Step 2.5: replace each instance of those with T or F dependeing on evaluation

    equalities = re.findall("[10x\\+ ]+ (?:==|!=) [10x\\+ ]+", condition)
    #print(equalities)
    for elem in equalities:
        originalElem = elem
        #print(originalElem)
        # Additional handling of the rare + - grep ensured there are no instances of other operators!
        addition = re.findall("[10]+ \\+ [10]+", elem)
        for eq in addition:
            # Each eq is of the form binary + binary
            originalEq = eq
            eqSplit = eq.split(" ")
            eqSum = bin(int(eqSplit[0], 2) + int(eqSplit[2], 2))
            eqSum = eqSum.strip("0b")
            # Add leading zeroes to match left sides length
            numZeroes = max(len(eqSplit[0]), len(eqSplit[2]))
            eqSum = eqSum.zfill(numZeroes)
            # Replace "eq" in the original elem with eqSum
            regex = eq.strip()
            regex = "\\b" + regex + "\\b"
            regex = regex.replace("+", "\\+")
            elem = re.sub(regex, eqSum, elem)
            #print(eqSum)


        # Evaluate the equality
        elem = elem.strip()
        splitElem = elem.split(" ")
        #print(splitElem)
        comparison = compareWithXs(splitElem[2], splitElem[0])

        if splitElem[1] == "==":
            result = comparison
        elif splitElem[1] == "!=":
            result = not comparison  

        if result:
            result = "TRUE"
        else:
            result = "FALSE"  
        # Add \b before and after the elem to ensure replacements are accurate
        regex = originalElem.strip()
        regex = regex.replace("+", "\\+")
        regex = "\\b" + regex + "\\b"
        condition = re.sub(regex, result, condition)
        
    # Step 3: use a parser library to evaluate the restuling logical expression (might have to replace && with "and" and so on)

    condition = condition.replace("&&", "and")
    condition = condition.replace("||", "or")

    #print("CONDITION:")
    #print(condition)

    evaluation = boolean.BooleanAlgebra().parse(condition).simplify()

    if evaluation == boolean.BooleanAlgebra().TRUE:
        return True
    else:
        return False



if __name__ == "__main__":
    splitWithBrackets("imm5<4:3>:imm4<3>")
    match = re.search("encoded as (.*)\.", "this is encoded as \"rx\" plus 2 times 5.")
    print(match[1])
    print(evaluateEquation(re.sub("\".*\"", "x", "\"rx\" plus 5 minus 4").replace("field", ""), 8))
    # i1 = InstructionPage("arm-files/abs.xml")
    # instruction = "11011010110000000010001010010110"
    # print(i1.matchClass(instruction).matchEncoding(instruction).explanations[0].symbol)
    # print(i1.disassemble(instruction))
    print(aliasCondCheck("S == '1' && Pn == '10x' && (S != '1' || Pn == '1xx')", (("S", 1), ("Pn", "101"), ("Pm", 100))))
    print((boolean.BooleanAlgebra().parse("TRUE and TRUE AND ( FALSE or TRUE )")).simplify())
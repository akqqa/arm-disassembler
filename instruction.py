from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys
from instructionClass import *
from encodingDetails import *
from explanation import *

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
            encoding = c.instructionDescription
            for i in range(0, len(encoding)):
                #print(instString[i])
                #print(encoding[i])
                if instString[i] == encoding[i] or encoding[i] == "x":
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
        # Get values from instructionencoding
        values = iClass.instructionEncoding.assignValues(instruction)
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



# Given an alias pref string and the values of symbols, checks if the condition string is valid with the given symbols
# Similar to the equation parsing but more complex as can have ==, !=, && and (||)
# Likely can use a premade boolean logic library. extract all x == y or x != y, replace them with True or False, then evaluatte logically!
def aliasCondCheck(condition, values):
    condition = condition.replace("'", "")
    condition = condition.replace("(", "( ")
    condition = condition.replace(")", " )")

    # With the latest version of the specification, the logic can now include IN statements. For now, these are unsupported as aliases
    if "IN" in condition:
        return False

    # Step 0: somehow detect if using pseudocode and dont evaluate if so, ignore these aliases
    # Easy to detect! just check if the aliaspref contains an <a> tag inside, do this before the condcheck
    
    # Step 1: replace all symbols with their corresponding values
    # Split by whitespace, to ensure doesnt replace part of substring with somthing. e,g a and Ra, could replace both a's
    splitCond = condition.split(" ")
    for i in range(0, len(splitCond)):
        for tup in values:
            if splitCond[i] == tup[0]:
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
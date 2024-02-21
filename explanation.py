from common import *
import xml.etree.ElementTree as et
import re
import html
import boolean
import sys

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
            encodingText = root.find("account").find("intro").find("para").text
            # Check if bitmask immediate
            if "bitmask immediate" in encodingText:
                self.bitmaskImmediate = True
            # Check if implicit value
            implicit = re.search("implicit value (\d+)\.", encodingText)
            if implicit is not None:
                self.implicitValue = implicit.group(1)

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
                if (len(normIndexes) == 1): # Can be slice<1>. so must account for only being on index
                    newResult = result[normIndexes[0]]
                else:
                    newResult = result[normIndexes[0]:normIndexes[1]+1]
                result = newResult

            # Check if bitmask immediate, and if so decode the result as a bitmask immediate
            if self.bitmaskImmediate:
                result = decodeBitmaskImmediate(result)

            # Convert binary to int
            result = str(int(result, 2))

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
                elif (self.symbol[1] == "Z"):
                    result = "z" + result
                elif (self.symbol[1] == "C"):
                    result = "c" + result
                elif (self.symbol[1] == "P"):
                    result = "p" + result
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
                rowVars = row[:self.tableResultIndex]
                if (all([compareWithXs(fst, snd) for fst, snd in zip(rowVars, matchList)])): #zips rowVars and matchList, then compares each element accounting for xs to check if the lists match
                    matchingRow = row
            if matchingRow == None:
                print("Error: could not match the table - invalid machine code given", file=sys.stderr)
                print(values, file=sys.stderr)
                return (self.symbol, "") # For now, just return it as empty. However, this occurs when https://developer.arm.com/documentation/ddi0602/2023-12/Base-Instructions/LDRB--register---Load-Register-Byte--register--?lang=en
                # basically some encoding is used when option != 011, another when option == 011. This is jusut always doing the first, so error when it is 011 and nothing defined for it!
            # Once found, get the final result
            # NOTE FINAL RESULT COULD BE OF FORM IMM5<4:1> SO TAKE THIS INTO ACCOUNT TOO

            # Intead of getting the last in the row, get the one that is actually the symbol - see arm-files/msr_imm.xml
            # Result is stored in the nth element, where n is the tableResultIndex constructed when the table was built
            result = matchingRow[self.tableResultIndex]

            # Handle things such as H<4:3>:imm4, 
            if "UInt(" in result:
                # Finds all UInt() sections in the asm, and handles their inner elements, replacing them with the final value
                functions = re.finditer("UInt\\((.*)\\)", result)
                # If none, just caclulateConcatSymbols normally, as can assume its across the whole element
                for m in functions:
                    replacement = calculateConcatSymbols(m.group(1), values)
                    result = result.replace(m.group(0), replacement)
           # else: # Otherwise assumes the whole string is able to be split by colons
                #result = calculateConcatSymbols(result, values)

            # Handle special case of [absent] and [present]
            if result == "[absent]":
                result = ""
            elif result == "[present]":
                result = self.symbol

            # CURRENT CAVEAT - SYMBOLS GIVEN BY TABLE CANNOT HAVE REGISTER PREFIX

            # split by colons, replace with values in values, then concat and return
            return (self.symbol, result)

# A technical improvement could be to only convert to integer if specified as UInt!!
def calculateConcatSymbols(result, values):
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
            else:
                result = val[0]
            finalResult += result
        else:
            finalResult += elem
    # Sometimes '0' is used, so strip any ' symbols
    finalResult = finalResult.replace("'", "")
    # Convert to decimal if possible
    try:
        convertedResult = str(int(finalResult, 2))
        return convertedResult
    except ValueError:
        return finalResult

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
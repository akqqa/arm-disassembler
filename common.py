import xml.etree.ElementTree as et
import re
import html
import boolean
import sys

ARM_FILE_PATH = "arm-files"

# Class to store the variable mapping of a binary instruction
# Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
# Perhaps change this to simply return the values dict, instead of tying it inherently to the object for better representation of what is actually being done
class InstructionMapping():

    # Default example mapping - [start position, length(inclusive)]
    mappings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    def __init__(self, mappings=mappings):
        self.mappings = mappings

    def assignValues(self, instruction):
        values = []
        if len(instruction) != 32:
            return False
        for var in self.mappings.keys():
            start = 31 - self.mappings[var][0] # 31 - as the mapping is done 31-0 whereas arrays are 0-31
            end = start + self.mappings[var][1]
            value = instruction[start:end]
            values.append((var, value))
        #print("values: " + str(values))
        return tuple(values)


# fst contains x's, snd does not
def compareWithXs(fst, snd):
    if len(fst) != len(snd):
        return False
    for i in range(0, len(fst)):
        if fst[i] == "x":
            continue
        elif fst[i] == "1" and snd[i] == "1":
            continue
        elif fst[i] == "0" and snd[i] == "0":
            continue
        else:
            return False
    return True

def addLeadingZeroes(num):
    leading = "0" * (8-len(num))
    return leading + num

#Helper function to output the ASM template
def getASM(asmelement):
    output = ""
    for child in asmelement:
        output += child.text
    return output

# Given an alias pref string and the values of symbols, checks if the condition string is valid with the given symbols
# Similar to the equation parsing but more complex as can have ==, !=, && and (||)
# Likely can use a premade boolean logic library. extract all x == y or x != y, replace them with True or False, then evaluatte logically!
def aliasCondCheck(condition, values):

    # Checks for never and unconditionally
    if condition == "Unconditionally":
        return True
    if condition == "Never":
        return False

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

# Helper function to split a string by colons, not including any colons inside &lt/&rt (</>)
# e.g imm5<4:3>:imm4<3> = [imm5<4:3>, imm4<3>]
# Returns the symbols divided by brackets
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

# Claculates the resulting value of concatendated symbols - e.g H:B:imm5 should combine the bits!
# Could perhaps improve / fix by making it only convert if uint is present? - ACTUALLY only ever called from a uint. assumes that these will only occur when a uint is used - otherwise doesnt make sense tbf
# Returns the bits concatenated! USES SPLITWITHBRACKETS to ensure correct splitting with <> present. can later be converted to an integer as returns binary that has been concatenated
def calculateConcatSymbols(result, values):
    splitResult = splitWithBrackets(result) # This is the set of things to concatenate to get the result
    finalResult = ""
    for elem in splitResult: # Each elem is H, B, imm5 in H:B:imm5. can even include <>
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
                # If only one index, get that bit, otherwise get substring between the two indicies
                if len(indexes) > 1:
                    result += val[0][length - int(indexes[0]) : length - int(indexes[1]) + 1]
                else:
                    result += val[0][length - int(indexes[0])]
            else:
                result = val[0]
            finalResult += result
        else:
            finalResult += elem
    # Sometimes '0' is used, so strip any ' symbols
    finalResult = finalResult.replace("'", "")
    return finalResult

# Helper method to evaluate equations of the form "x times 5 plus 2 modulo 3"
# The XML specification never contains instances of division, so not supported
def evaluateEquation(equation, x):
    try:
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
    except ValueError:
        return None
    except IndexError:
        return None

def rightRotateString(rotator, num):
    # Rotate by getting the last num digits, removing them from one side, then adding them to the front
    rightEnd = rotator[len(rotator)- num:]
    rightStart = rotator[0:len(rotator) - num]
    return rightEnd + rightStart

# Takes a bitmask immediate as a string, and returns the value as a number
def decodeBitmaskImmediate(bitmask, size):
    #Bitmask encoded as (N):imms:immr where imms and immr are 6 bits each, and N is 1
    # Add N character if not included in bitmask
    if len(bitmask) == 12:
        bitmask = "0" + bitmask
    
    if len(bitmask) != 13:
        return None

    # Using the table from https://dinfuehr.github.io/blog/encoding-of-immediate-values-on-aarch64/ to encode the bitmasks
    # If N = 1, handle as a 64 bit element
    patternBits = False
    if bitmask[0] == "1":
        patternBits = bitmask[1:7]
    elif bitmask[0] == "0":
        # Traverse imms bits until a 0 is found
        for i in range(1, 6):
            if bitmask[i] == "0":
                patternBits = bitmask[i+1:7]
                break
    # Pattern stores one less than the number of consecutive 1's
    consecutiveOnes = int(patternBits, 2) + 1

    # Elementsize is found by 2^(patternBits length)
    elementSize = pow(2, len(patternBits))

    # Built the binary string, by creating consecutive 1's then padding it with 0's at the head until it is elementSize long
    binaryString = "1"*consecutiveOnes
    # Pad with zeroes
    numZeroes = elementSize - consecutiveOnes
    binaryString = "0"*numZeroes + binaryString

    # Right rotate immr times
    immr = bitmask[7:]
    immr = int(immr, 2)
    binaryString = rightRotateString(binaryString, immr)

    # If under size, multiply until size or over
    if (size != None):
        original = binaryString
        while len(binaryString) < size:
            binaryString += original

    return binaryString

def twosComplement(binaryString):

    # If a single digit, just convert to binary
    if len(binaryString) == 1:
        return int(binaryString, 2)

    # convert binary string without first digit to int
    result = int(binaryString[1:], 2)
    # If the first bit is 1, subtract 2 to the power of the binaryString length - 1 from positiveInt
    if binaryString[0] == "1":
        result = result - 2**(len(binaryString)-1)
    return result


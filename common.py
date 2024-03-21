# A file containing common and helper methods for other files in this module

import xml.etree.ElementTree as et
import re
import html
import boolean
import sys

ARM_FILE_PATH = "arm-files" # The name of the directory that contains the arm specification. Can be modified

class InstructionMapping():
    """
    Class to store the variable mapping of a binary instruction
    Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
    
    Attributes:
        mappings - the names of each variable as well as the range of bits the variable spans
    """

    # Default example mapping - [start position, length(inclusive)]
    mappings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    def __init__(self, mappings=mappings):
        """
        Initialiases the class

        :param mappings: the mapping to use when assigning values for instructions
        """
        self.mappings = mappings

    def assignValues(self, instruction):
        """
        Returns a tuple in the form ((varname1, value1), (varname2, value2), ...) based on the given instruction and the mapping defined in this object

        :param instruction: the instruction to extract values from
        """

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


def compareWithXs(fst, snd):
    """
    Compares two binary strings to see if they are equivalent, with the rule that an 'x' in the first string can be either a 1 or 0 in the second

    :param fst: the first binary string, which can contain x characters
    :param snd: the second binary string, which cannot contain x characters
    """

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
    """
    Adds leading zeros to a given binary string to make it 8 bits long

    :param num: the number to pad
    """
    leading = "0" * (8-len(num))
    return leading + num

def getASM(asmelement):
    """
    Extracts the assembly template from an XML element

    :param asmelement: the element to extract the assembly template from
    """
    output = ""
    for child in asmelement:
        output += child.text
    return output

def aliasCondCheck(condition, values):
    """
    Given an alias pref string and the values of symbols, checks if the condition string is valid with the given symbols
    Similar to the equation parsing but more complex as can have ==, !=, && and (||)

    :param condition: the string describing the condition for the alias to match, e.g 'Rm == 10010 && Rn == 101'
    :param values: a tuple of tuples describing variables and their values extracted from the instruction being checked
    """

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

    # Step 0:  detect if using pseudocode and dont evaluate if so, ignore these aliases
    # this is done by checking if the aliaspref contains an <a> tag inside, before this method is called
    
    # Step 1: replace all symbols with their corresponding values
    # Split by whitespace, to ensure doesnt replace part of substring with somthing. e,g a and Ra, could replace both a's
    splitCond = condition.split(" ")
    for i in range(0, len(splitCond)):
        for tup in values:
            if splitCond[i] == tup[0]:
                splitCond[i] = str(tup[1])
    condition = " ".join(splitCond)


    # Now have a string of form 1 == 1 && 101 == 100

    # Step 2: extract all x ==/!= y and evaluate each
    # Step 2.5: replace each instance of those with T or F depending on evaluation

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
        
    # Step 3: use a parser library to evaluate the resulting logical expression (have to replace && with "and" and so on)

    condition = condition.replace("&&", "and")
    condition = condition.replace("||", "or")

    evaluation = boolean.BooleanAlgebra().parse(condition).simplify()

    if evaluation == boolean.BooleanAlgebra().TRUE:
        return True
    else:
        return False

def splitWithBrackets(inputStr):
    """
    Splits a string by colons, not including any colons inside angular brackets. Returns a list of the string split by colons
    e.g imm5<4:3>:imm4<3> = [imm5<4:3>, imm4<3>]

    :param inputStr: the string to split by colons
    """

    # using https://stackoverflow.com/a/15599760
    # All < must have an associated > to be well formed in the specification. Using this we can find the indices of each and only split on colons not between these
    openingIndexes = [x.start() for x in re.finditer("<", inputStr)]
    closingIndexes = [x.start() for x in re.finditer(">", inputStr)]
    ranges = list(zip(openingIndexes, closingIndexes))
    toSplit = []
    splitList = []
    # Constructs a list of indices that should be split on
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

def calculateConcatSymbols(inputStr, values):
    """
    Calculates the resulting value of concatendated symbols when given an inputString of the format imm5<4:3>:imm4<3>
    e.g imm5<4:3>:imm4<3>, with the values imm5=101010 and imm4 = 00101, will result in 010

    :param inputStr: the string to be replaced with the concatenated bit values of all variables and ranges
    :param values: the values of variables to replace
    """

    splitResult = splitWithBrackets(inputStr) # This is the set of things to concatenate to get the result
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

def evaluateEquation(equation, x):
    """
    Evaluates equations of the form 'x times 5 plus 2 modulo 3'. Each equation can have one 'x' value, which is replaced by the input variable x
    Note: Evaluates from left to right, rather than with the normal order of operations
    The XML specification never contains instances of division, so it is not supported

    :param equation: the string of an equation of the form 'x times 5 plus 2 modulo 3'
    :param x: the value to replace the 'x' character in the equation with
    """

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
    # Catch errors in case of malformed equation such as not having the right number of operators or operands
    except ValueError:
        return None
    except IndexError:
        return None

def rightRotateString(rotator, num):
    """
    Rotates a string right a given number of times

    :param rotator: the string to rotate
    :param num: the number of right rotations to perform
    """
    # Rotate by getting the last num digits, removing them from one side, then adding them to the front
    rightEnd = rotator[len(rotator)- num:]
    rightStart = rotator[0:len(rotator) - num]
    return rightEnd + rightStart

def decodeBitmaskImmediate(bitmask, size):
    """
    Given a bitmask immediate and a size, decodes the bitmask immediate into the correct bitmask pattern, and replicate it until it is a given size

    :param bitmask: the bitmask value to decode
    :param size: the size that the decoded bitmask should be
    """

    # Bitmask encoded as (N):imms:immr where imms and immr are 6 bits each, and N is 1
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
    """
    Given a binary string, translate it into an integer with twos complement

    :param binaryString: the binary string to convert into an integer
    """

    # If a single digit, just convert to binary
    if len(binaryString) == 1:
        return int(binaryString, 2)

    # convert binary string without first digit to int
    result = int(binaryString[1:], 2)
    # If the first bit is 1, subtract 2 to the power of the binaryString length - 1 from positiveInt
    if binaryString[0] == "1":
        result = result - 2**(len(binaryString)-1)
    return result


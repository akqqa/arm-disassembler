# Class to store the variable encoding of a binary instruction
# Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
# Perhaps change this to simply return the values dict, instead of tying it inherently to the object for better representation of what is actually being done
class InstructionEncoding():

    # Default example encoding - [start position, length(inclusive)]
    encodings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    def __init__(self, encodings=encodings):
        self.encodings = encodings

    def assignValues(self, instruction):
        #print(self.encodings)
        values = []
        if len(instruction) != 32:
            return False
        for var in self.encodings.keys():
            start = 31 - self.encodings[var][0] # 31 - as the encoding is done 31-0 whereas arrays are 0-31
            end = start + self.encodings[var][1]
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

# Takes a bitmask immediate as a string, and returns the value as a number
def bitmaskImmediateDecoder(bitmask):
    #Bitmask encoded as (N):imms:immr where imms and immr are 6 bits each, and N is 1
    # Add N character if not included in bitmask
    if len(bitmask) == 12:
        bitmask = "0" + bitmask


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

    return int(binaryString, 2)

def rightRotateString(rotator, num):
    # Rotate by getting the last num digits, removing them from one side, then adding them to the front
    rightEnd = rotator[len(rotator)- num:]
    rightStart = rotator[0:len(rotator) - num]
    return rightEnd + rightStart
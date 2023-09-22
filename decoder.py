# Decodes the machine code based on a given specification

# Class to store the variable encoding of a binary instruction
# Starts by being given the variable lengths and positions upon instantiation, then can be fed an actual binary string, where it will assign the variables to their actual values
class InstructionEncoding():

    # Default example encoding - [start position, length(inclusive)]
    encodings = {
        "op0": [31, 1],
        "op1": [28, 4]
    }

    values = {}

    def __init__(self, encodings=encodings):
        self.encodings = encodings

    def assignValues(self, instruction):
        if len(instruction) != 32:
            return False
        for var in self.encodings:
            start = 31 - self.encodings[var][0] # 31 - as the encoding is done 31-0 whereas arrays are 0-31
            end = start + self.encodings[var][1]
            value = instruction[start:end]
            self.values[var] = value
        return True



# test = InstructionEncoding()
# print(test.encodings)
# test.assignValues("10100101001101001010110101011001")
# print(test.values)

# Decoding process:
# Parse each table in the index by encoding section, storing each in a data structure
# start at top level, assign values to instructionencoding, then use this to match with row of table,
# then get up pointed to table, and assign the instruction encoding, repeating until instruction found

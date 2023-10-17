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

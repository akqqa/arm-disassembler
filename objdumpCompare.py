import re
# WITH V'S AND Z'S IT CAN HAVE THINGS SUCH AS {Z20.D-Z22.D} TO MEAN Z20.D, Z21.D, Z22.D ETC.
# TRANSFORM THIS WITH REGER WHENEVER ENCOUNTERED

# Also, need to convert 0x hex into decimal
# need to convert all white space to single spaces - in fact remove all whitespace in the operands!
# need to treat cases as the same - everything is tolower

# output we want to verify starts in line 8 of the objdump file
def transformObjdumpLine(line):
    line = line.replace("\t", " ")
    # Remove the first 20 characters as these are not relevant
    line = line[20:]
    
    # Replace hex with decimal
    hexMatches = re.finditer("0x[0-9abcdef]+", line)
    for match in hexMatches:
        value = str(int(match.group(0), 16))
        line = line.replace(match.group(0), value)

    # Replace substrings of the form {v22.d-v24.d} with v22.d, v23.d, v24.d
    listMatches = re.finditer("\{([a-z](\d+)\.[^-]+)-[a-z](\d+)\.[^-]+\}", line)
    for match in listMatches:
        # Group 1 = the first register
        # Group 2 = the first number
        # Group 3 = the last number
        registers = []
        for i in range(int(match.group(2)), int(match.group(3)) + 1):
            # Replace the number in group 1 with i
            register = re.sub("\d+", str(i), match.group(1))
            registers.append(register)
        registersAdded = ", ".join(registers)
        line = line.replace(match.group(0), registersAdded)

    # Remove everything after //
    commentMatches = re.finditer("//.*", line)
    for comment in commentMatches:
        line = line.replace(comment.group(0), "")

    # Remove everything between <>
    tagMatches = re.finditer("<.*>", line)
    for match in tagMatches:
        line = line.replace(match.group(0), "")

    # Remove all { and }
    line = line.replace("{", "")
    line = line.replace("}", "")

    line = line.replace("\n", "")

    return line.lower()

def transformMyLine(line):
    line = line.lower()
    line = re.sub("\s+", " ", line)

    return line

objdumpFile = open("objdump.out", "r")
lines = objdumpFile.readlines()
objdumpFile.close()

objdumpLines = lines[7:] # Removes unnecessary starting lines

myFile = open("myOutput.out", "r")
myLines = myFile.readlines()
myFile.close()

if len(objdumpLines) != len(myLines):
    print("output files not same length")
    print(len(objdumpLines))
    print(len(myLines))
    exit(1)

totalOpcodes = 0
opcodeMatches = 0

totalOperands = 0
operandMatches = 0

for i in range(0, len(myLines)):
    objdumpLine = transformObjdumpLine(objdumpLines[i])
    myLine = transformMyLine(myLines[i])
    # First, compare the opcode
    totalOpcodes += 1
    objdumpInstruction = objdumpLine.split(" ", 1)
    myInstruction = myLine.split(" ", 1)
    if objdumpInstruction[0] == myInstruction[0]:
        opcodeMatches += 1
        # Next, compare each operand - sometimes might not be any, so ignore if so
        try:
            # Eliminate whitespace in the operands - causes 30% loss in accuracy just due to inconsistent spacing!
            objdumpInstruction[1] = re.sub("\s+", "", objdumpInstruction[1])
            myInstruction[1] = re.sub("\s+", "", myInstruction[1])
            objdumpOperands = objdumpInstruction[1].split(",")
            myOperands = myInstruction[1].split(",")
        except IndexError:
            continue
        show = True
        for i in range(0, len(objdumpOperands)):
            totalOperands += 1
            if objdumpOperands[i] == myOperands[i]:
                operandMatches += 1
            elif show:
                print(objdumpLine)
                print(myLine)
                show = False
    else:
        print(objdumpLine)
        print(myLine)

print("Total instructions: " + str(totalOpcodes))
print("Total maching opcodes: " + str(opcodeMatches))
print("Percentage of opcodes correctly translated: " + str(100 * float(opcodeMatches) / float(totalOpcodes)) + "%")

print("Total operands out of instructions with matching opcodes: " + str(totalOperands))
print("Total maching operands: " + str(operandMatches))
print("Percentage of operands correctly translated: " + str(100 * float(operandMatches) / float(totalOperands)) + "%")

totalAccuracy = 100 * (float(operandMatches) / float(totalOperands)) * ( float(opcodeMatches) / float(totalOpcodes))
print("Total accuracy of the disassembler: " + str(totalAccuracy) + "%")
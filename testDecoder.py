from decoder import *

xml = et.parse("arm-files/encodingindex.xml")
root = xml.getroot()
hierarchy = root.find("hierarchy")

table = EncodingTable(root, hierarchy)

print(table.decode("00000000000000000000000000000000"))
print()
# ABS
print(table.decode("11011010110000000010001010010110"))
print()
# HINT (YIELD) - this works, but slight complexity, as the first row defines everything as being hint
# And then in the hint there is the pseudocode for figuring out which hint, dspite this also being in the table..
# Perhaps implement a system so it first finds all matches, and then uses the one with the least Nones - aka closest match
print(table.decode("11010101000000110010000000111111"))
print()
# FEXPA
print("decoding 00000100011000001011100000000000: ")
print(table.decode("00000100011000001011100000000000"))
print()
# FDOT (2-way, multiple and indexed vector, FP8 to FP16) - this ones weird - the docs dont match the xml perfectly
print(table.decode("11000001000101011011100001000101"))
print()
# SQDMULH (multiple vectors)
print(table.decode("11000001111000001011010000000000"))
print()
# FDOT (2-way, multiple and single vector, FP8 to FP16) - this again is unallocated, yet switching final 01 to 10 gives correct bfdot, maybe fdot not supported?
print(table.decode("11000001001000000111000101001111"))
print()
# BFDOT
print(table.decode("11000001001000000111000101010111"))
print()

# https://developer.arm.com/documentation/ddi0602/2023-09/Base-Instructions/LDR--immediate---Load-Register--immediate--
print("Wt ldr preindex:")
print(table.decode("10111000010011010101110011010101"))
print("Xt ldr preindex:")
print(table.decode("11111000010011010101110011010101"))

print("Wt LDR unsigned offset:")
print(table.decode("10111001011010101010111010100101"))
print("Xt LDR unsigned offset:")
print(table.decode("11111001011010101010111010100101"))
print()

#F2CVTL{2} - apparently unallocated??? weird - OH cause its a feat
print(table.decode("01101110011000010111100101010101"))

# Instead try FCVTN
print(table.decode("01001110011000010110100101010101"))

print(table.decode("11110000000000000001010000010010"))
#Works!!

# Example program (GENERATED WITH CHATGPT):
# mov x0, #5 
# mov x1, #7 
# add x2, x0, x1
# mov x8, #93 
# svc #0  
# Which in machine code is (according tohttps://armconverter.com/ )
# A00080D2 - 10100000000000001000000011010010
# E10080D2 - 11100001000000001000000011010010
# 0200018B - 00000010000000000000000110001011
# A80B80D2 - 10101000000010111000000011010010
# 010000D4 - 00000001000000000000000011010100

# D28000A0 - 11010010100000000000000010100000
# D28000E1 - 11010010100000000000000011100001
# 8B010002 - 10001011000000010000000000000010
# D2800BA8 - 11010010100000000000101110101000
# D4000001 - 11010100000000000000000000000001

print()
print("Decoding example program:")
print(table.decode("11010010100000000000000010100000"))
print(table.decode("11010010100000000000000011100001"))
print(table.decode("10001011000000010000000000000010"))
print(table.decode("11010010100000000000101110101000"))
print(table.decode("11010100000000000000000000000001"))

# IT WORKS!! important note - is big endian!
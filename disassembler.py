import sys
import pickle

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Incorrect number of arguments")
        print("Format: python decoder.py <path_to_file>")
        quit()

    file = open('data', 'rb')
    table = pickle.load(file)
    #print(table.matchVar((("hi", "00101"), ("no", "10101")), ("hi", "00 != 00x")))

    table.disassemble(sys.argv[1])

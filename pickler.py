# Saves the instruction data to a file for quick deserialization
from decoder import *
import pickle

if __name__ == "__main__":
    xml = et.parse("arm-files/encodingindex.xml")
    root = xml.getroot()
    hierarchy = root.find("hierarchy")

    table = EncodingTable(root, hierarchy)
    file = open('data.pkl', 'wb')
    pickle.dump(table, file)
    file.close()
# Utility program to match regex across all files in a folder
import sys
import re
import os

folder = sys.argv[1]
regex = re.compile('encoded in "\w+&lt;\d') # must manually edit as entering in cmd line leads to errors with regex input!
#'class="symbol">\w+&lt;\d'

for file in os.listdir(folder):
    with open(folder + "/" + file, "r", encoding="utf8") as f:
        fstring = f.read()
        matches = re.findall(regex, fstring)
        if len(matches) > 0:
            print("Found in file: " + file)

__author__ = 'pat'

import os
import re

path = '/home/pat/CS-646-IR/book-data/books-medium/'
tokens = 0
for dirpath, dirs, files in os.walk(path):
    for filename in files:
        file = open(os.path.join(dirpath, filename), 'r')
        str = file.read()
        tokens += re.compile("\s+").split(str).__len__()
print tokens

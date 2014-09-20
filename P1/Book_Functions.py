__author__ = 'pv'

import os
from collections import defaultdict
from BeautifulSoup import BeautifulSoup
import string

path = '/home/pv/CS-646-IR/book-data/books-tiny/'
# how many times each word appears total
total_word_counts = defaultdict(int)
# how many books each word appears in
books_containing_word = defaultdict(int)
# how many pages each word appears in
pages_containing_word = defaultdict(int)

# global counts
book_count = 0
page_count = 0
book_unique_length = []
book_total_length = []
page_unique_length = []
page_total_length = []

replace_punctuation = string.maketrans(string.ascii_lowercase + string.ascii_uppercase + string.punctuation,
                                       string.ascii_lowercase * 2 + ' '*len(string.punctuation))

# get the line contents from all the books
for dirpath, dirs, files in os.walk(path):
    for book_file_name in files:

        # for each book, read in and parse the xml file
        print ("Parsing " + book_file_name)
        book_file = open(os.path.join(dirpath, book_file_name), 'r')
        book_xml = BeautifulSoup(book_file.read())

        book_count += 1
        book_word_counts = defaultdict(int)
        book_length = 0

        # break the book into pages
        pages = book_xml.document.findAll("page")
        # parse each page
        for page in pages:
            page_count += 1
            page_word_counts = defaultdict(int)
            # break the page into lines
            lines = page.findAll("line")
            # keep track of total number of words on each page
            page_length = 0
            for line in lines:
                # extract line text
                line_text = str(line.getText())
                # count the unique words
                for word in line_text.split():
                    clean_word = word.translate(replace_punctuation)
                  #  print (clean_word)
                    page_word_counts[clean_word] += 1
                    page_length += 1

            # keep track of page sizes
            page_unique_length.append(len(page_word_counts))
            page_total_length.append(page_length)
            book_length += page_length

            for word, count in page_word_counts.iteritems():
                # add page word occurances to the book occurances
                book_word_counts[word] += count
                pages_containing_word[word] += 1

        # keep track of total book sizes
        book_unique_length.append(len(book_word_counts))
        book_total_length.append(book_length)

        for word, count in book_word_counts.iteritems():
            books_containing_word[word] += 1
            total_word_counts[word] += count

print "GLOBAL"
print "book count : ", book_count
print "page count : ", page_count
print "page all word sum:", sum(page_total_length)
print "page unique word sum:", sum(page_unique_length)
print "book all word sum:", sum(book_total_length)
print "book unique word sum:", sum(book_unique_length)

print "sum total word:", sum(total_word_counts.values())
# print "SINGLE WORD"
# print "unique words across corpus:", total_word_counts.__len__()


# contents = map(lambda line: line.getText(), lines)


# SINGLE WORDS
# The number of occurrences of that word that you encounter
# The number of books that the word appears in at least once
# The number of pages that the word appears in at least once
# While doing that, there are a few collection-wide statistics worth keeping track of:

# GLOBAL
# Total number of pages and of books
# The length of books and pages (measured in occurrences of words that you kept)
# The length of books and pages (measured in unique words)

# WORD PAIRS
# The number of pages that contain both w1 and w2 at least once, no matter whether there are other words separating them
# The number of windows that contain both w1 and w2 at least once. A window is defined as 20 words. For each page that you find, there is a window at word numbers 1-20, 21-40, 41-60, and so on. Obviously the last window on a page may be smaller than 20 words.
# The number of times you find w1 followed immediately by w2 on the same page or in the same book (your choice)
# The number of times you find w1 followed by any other word (ought to be very close to the total number of occurrences of w1)
# Produce these statistics for word pairs where w1 or w2 is one of the four words powerful, strong, butter, or salt.
# For the three words Washington, James, and church, do the same, though you will only be using the immediately adjacent word information so you can omit the others if you like.
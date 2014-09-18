__author__ = 'pv'

import os
import re
from BeautifulSoup import BeautifulSoup
from collections import Counter

path = '/home/pv/CS-646-IR/book-data/books-tiny/'
# how many books each word appears in
# how many pages each word appears in
pages_words_occured_in = Counter

def read_books_from_disk():
    # global counts
    book_count = 0
    book_word_count_list = []
    book_unique_word_count_list = []
    page_count = 0
    page_word_count_list = []
    page_unique_word_count_list = []

    # single words stats
    # how many times each word appears in total
    total_word_counts = Counter()


    # get the line contents from all the books
    for dirpath, dirs, files in os.walk(path):
        for filename in files:
            print ("Parsing " + filename)
            book_count += 1
            file = open(os.path.join(dirpath, filename), 'r')
            xml_str = file.read()
            (book_page_count, book_total_word_counts) = parse_book(xml_str, total_word_counts, page_word_count_list, page_unique_word_count_list,
                                     book_word_count_list, book_unique_word_count_list)
            page_count += book_page_count
            total_word_counts += book_total_word_counts

    print "GLOBAL"
    print "book count : ", book_count
    print "page count : ", page_count
    print "page word sum:", sum(page_word_count_list)
    print "page unique word sum:", sum(page_unique_word_count_list)
    print "book word sum:", sum(book_word_count_list)
    print "book unique word sum:", sum(book_unique_word_count_list)
    print "SINGLE WORD"
    print "unique words across corpus:", total_word_counts.__len__()



def parse_book(xml_str, current_word_counts, page_word_count_list, page_unique_word_count_list,
               book_word_count_list, book_unique_word_count_list):
    global pages_words_occured_in
    # i think we only care about the lines of the books
    xml_parse = BeautifulSoup(xml_str)
    pages = xml_parse.document.findAll("page")
    page_count = pages.__len__()

    book_word_counts = Counter()

    # parse each page
    for page in pages:
        # get the contents of each page in a single list
        lines = page.findAll("line")
        contents = map(lambda line: line.getText(), lines)
        # count the unique words
        page_word_counts = Counter(contents)
        # increment counters for this book
        book_word_counts = book_word_counts + page_word_counts
        # counter for all books
        current_word_counts = current_word_counts + page_word_counts
        # lists of page word counts
        page_word_count_list.append(contents.__len__())
        page_unique_words = list(page_word_counts)
        # for each word, we want to know how many pages it occured in
        pages_words_occured_in.update(Counter(page_unique_words))
        page_unique_word_count_list.append(page_unique_words.__len__())

    book_word_count_list.append(sum(book_word_counts.values()))
    book_unique_word_count_list.append(book_word_counts.__len__())

    return page_count, current_word_counts


read_books_from_disk()

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
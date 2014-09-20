__author__ = 'pv'

import os
import string
import datetime
from collections import defaultdict
from BeautifulSoup import BeautifulSoup


# keep track of runtime
start_time = datetime.datetime.now()

# io info
data_set = "tiny"
my_name = "pv"
output_file = "../output/" + data_set
path = '/home/pv/CS-646-IR/book-data/books-' + data_set

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

to_lower = string.maketrans(string.ascii_uppercase, string.ascii_lowercase)

# get the line contents from all the books
def process_word(dirty_word):
    global page_length
    clean_word = dirty_word.translate(to_lower).translate(None, string.punctuation)
    page_word_counts[clean_word] += 1
    page_length += 1

    # print (clean_word)
    return clean_word


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

            # extract line text
            page_text_list = [str(line.getText()) for line in lines]
            page_text = " ".join(page_text_list)
            # count and clean the words
            clean_words = map(process_word, page_text.split())

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


# sort our result dictionaries
top_words = sorted(total_word_counts.items(), key=lambda x: x[1])
top_words.reverse()
# get total number of words we encountered
total_words = sum(total_word_counts.values())

output = open(output_file, 'w')

print "\n\n"

output.write("%s %s %s %s %s\n" % (my_name, data_set, "N", book_count, page_count))
output.write("%s %s %s %s\n" % (my_name, data_set, "TO", total_words))
output.write("%s %s %s %s\n" % (my_name, data_set, "TU", total_word_counts.__len__()))

# print stats on top 50 words
for i in range(0, 50):
    w, v = top_words[i]
    tokenP = float(v) / float(total_words)
    output.write("%s %s %s %s %s %s %s %f %f\n" % (my_name, data_set, i, w, books_containing_word.get(w),
                                                   pages_containing_word.get(w), v, tokenP, tokenP * (i + 1)))

output.close()
print(datetime.datetime.now() - start_time)
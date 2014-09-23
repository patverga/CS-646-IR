__author__ = 'pv'

import os
import re
import string
import datetime
from collections import defaultdict
from BeautifulSoup import BeautifulSoup


# keep track of runtime
start_time = datetime.datetime.now()

# io info
data_set = "big"
my_name = "pv"
output_file = "../output/" + data_set + ".results"
association_file = "../output/" + data_set + ".associations"
stoplist_file = "../stopwords.list.sorted"
path = '/home/pv/CS-646-IR/book-data/books-' + data_set

# how many times each word appears total
total_word_counts = defaultdict(int)
# how many books each word appears in
books_containing_word = defaultdict(int)
# how many pages each word appears in
pages_containing_word = defaultdict(int)

# specific word bigram stats - map special words to dict location index
bigram_index_map = {'powerful': 0, 'strong': 1, 'salt': 2, 'butter': 3, 'washington': 4, 'james': 5, 'church': 6}
bigram_pages = [defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int),
                defaultdict(int), defaultdict(int)]
bigram_windows = [defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int),
                  defaultdict(int), defaultdict(int)]
bigram_follows = [defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int),
                  defaultdict(int), defaultdict(int)]
bigram_proceeds = [defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int),
                   defaultdict(int), defaultdict(int)]
bigram_followed_by_count = [0, 0, 0, 0, 0, 0, 0]

# global counts
book_count = 0
page_count = 0
book_unique_length = []
book_total_length = []
page_unique_length = []
page_total_length = []

# precompile these for efficiency
to_lower = string.maketrans(string.ascii_uppercase, string.ascii_lowercase)
bigram_regex = re.compile(".*(powerful|strong|butter|salt|james|church|washington).*")
special_word_regex = re.compile("^(powerful|strong|butter|salt|james|church|washington)$")

# read in stop word list
stop_words = set([line.rstrip() for line in open(stoplist_file, 'r')])

# get the line contents from all the books
def process_word(dirty_word):
    global page_length
    clean_word = dirty_word.translate(to_lower).translate(None, string.punctuation)
    page_word_counts[clean_word] += 1
    page_length += 1

    return str(clean_word.strip())


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
            page_text_list = [line.getText().encode('utf-8') for line in lines]
            page_text = " ".join(page_text_list)
            # count and clean the words
            clean_words = map(process_word, page_text.split())
            clean_words = filter(lambda cww: cww.strip(), clean_words)

            # gross, but only count full page bigram stats once per special word
            special_word_page_done = [False, False, False, False, False, False, False]
            # calculate bigram stats
            if bigram_regex.match(page_text):
                for i in range(0, len(clean_words)):
                    cw = clean_words[i]
                    # is this a special word?
                    if special_word_regex.match(cw):
                        index = bigram_index_map.get(cw)
                        if i + 1 < len(clean_words):
                            bigram_followed_by_count[index] += 1
                            # increment the word right after special word
                            bigram_follows[index][clean_words[i + 1]] += 1
                        if i - 1 >= 0:
                            # increment the word right before special word
                            bigram_proceeds[index][clean_words[i - 1]] += 1
                        # increment all the words within the current window
                        window_start = i - (i % 20)
                        for j in range(window_start, min(window_start + 20, len(clean_words))):
                            if i != j:
                                bigram_windows[index][clean_words[j]] += 1
                        # increment all other words on the page
                        if not special_word_page_done[index]:
                            special_word_page_done[index] = True
                            for j in range(0, len(clean_words)):
                                if i != j:
                                    bigram_pages[index][clean_words[j]] += 1

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
for i in range(0, len(bigram_index_map)):
    # words that follow
    sorted_follows_pages = sorted(bigram_follows[i].items(), key=lambda x: x[1])
    sorted_follows_pages.reverse()
    # remove stop words from sorted list
    bigram_follows[i] = [word for word in sorted_follows_pages if not stop_words.__contains__(word[0])]
    # words that proceed
    sorted_proceeds_pages = sorted(bigram_proceeds[i].items(), key=lambda x: x[1])
    sorted_proceeds_pages.reverse()
    # remove stop words from sorted list
    bigram_proceeds[i] = [word for word in sorted_proceeds_pages if not stop_words.__contains__(word[0])]
    # words within the same window
    sorted_window = sorted(bigram_windows[i].items(), key=lambda x: x[1])
    sorted_window.reverse()
    bigram_windows[i] = [word for word in sorted_window if not stop_words.__contains__(word[0])]
    # words on the same page
    sorted_pages = sorted(bigram_pages[i].items(), key=lambda x: x[1])
    sorted_pages.reverse()
    bigram_pages[i] = [word for word in sorted_pages if not stop_words.__contains__(word[0])]

# get total number of words we encountered
total_words = sum(total_word_counts.values())

# open output file
output = open(output_file, 'w')
association = open(association_file, 'w')

print "\n Exporting Results ... \n"

output.write("%s %s %s %s %s\n" % (my_name, data_set, "N", book_count, page_count))
output.write("%s %s %s %s\n" % (my_name, data_set, "TO", total_words))
output.write("%s %s %s %s\n" % (my_name, data_set, "TU", total_word_counts.__len__()))

# print stats on top 50 words
for i in range(0, 50):
    w, v = top_words[i]
    tokenP = float(v) / float(total_words)
    output.write("%s %s %s %s %s %s %s %f %f\n" % (my_name, data_set, i, w, books_containing_word.get(w),
                                                   pages_containing_word.get(w), v, tokenP, tokenP * (i + 1)))

# print stats on the 4 special bigram words
for w, bigram_index in bigram_index_map.iteritems():
    # find this word in the word ranking list
    for i in range(0, len(top_words)):
        if top_words[i][0] == w:
            rank = i
            v = top_words[i][1]
            break

    tokenP = float(v) / float(total_words)
    output.write("%s %s %s %s %s %s %s %f %f\n" % (my_name, data_set, rank, w, books_containing_word.get(w),
                                                   pages_containing_word.get(w), v, tokenP, tokenP * (rank + 1)))

# find top most associated words with this special words
association.write("%s %s %s %s %s %s %s %s %s %s\n" % (
    "word", "rank", "page", "page_prob", "window", "window_prob", "follow", "follow_prob", "proceed", "proceed_prob"))
for w, bigram_index in bigram_index_map.iteritems():
    proceeds_total = sum(n for _, n in bigram_proceeds[bigram_index])
    follows_total = sum(n for _, n in bigram_follows[bigram_index])
    page_total = sum(n for _, n in bigram_pages[bigram_index])
    window_total = sum(n for _, n in bigram_windows[bigram_index])
    print proceeds_total, follows_total
    for i in range(0, 10):
        page_word, v1 = "", 0
        if i < len(bigram_pages[bigram_index]):
            page_word, v1 = bigram_pages[bigram_index][i]
        window_word, v2 = "", 0
        if i < len(bigram_windows[bigram_index]):
            window_word, v2 = bigram_windows[bigram_index][i]
        follows_word, v3 = "", 0
        if i < len(bigram_follows[bigram_index]):
            follows_word, v3 = bigram_follows[bigram_index][i]
        proceed_word, v4 = "", 0
        if i < len(bigram_proceeds[bigram_index]):
            proceed_word, v4 = bigram_proceeds[bigram_index][i]

        if i < 5:
            output.write("%s %s %s %s %s %s\n" % (my_name, data_set, w, page_word, window_word, follows_word))

        association.write(
            "%s %s %s %f %s %f %s %f %s %f\n" % (
                w, i, page_word, float(v1 / float(page_total + 1)), window_word, float(v2 / float(window_total + 1)),
                follows_word, float(v3 / float(follows_total + 1)), proceed_word,
                float(v4 / float(proceeds_total + 1))))

association.close()
print("%s %s" % ("Finished Dataset :", data_set))
output.write("%s %s\n" % ("Time Elapsed: ", str(datetime.datetime.now() - start_time)))
output.close()

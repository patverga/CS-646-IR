__author__ = 'pv'


import os
import string
from BeautifulSoup import BeautifulSoup

# io info
data_set = "medium"
output_file = "TREC-books"
path = '/home/pv/CS-646-IR/book-data/books-' + data_set

def page_to_trec(page, page_num):
    lines = page.findAll("line")
    # extract line text
    page_text_list = [line.getText().encode('utf-8') for line in lines]
    page_text = (" ".join(page_text_list)).translate(None, string.punctuation)
    if page_text != "":
        page_id = book_id + '-' + str(page_num)
        trec_page = '<DOC>\n<DOCNO>'+page_id+'</DOCNO>\n'+'<TEXT>\n'+page_text+'\n</TEXT>\n</DOC>\n'
        return trec_page
    return ""


out = open(output_file, 'w')
for dirpath, dirs, files in os.walk(path):
    for book_file_name in files:
        book_id = book_file_name.split("_")[0]
        # for each book, read in and parse the xml file
        print ("Parsing " + book_file_name)
        book_file = open(os.path.join(dirpath, book_file_name), 'r')
        book_xml = BeautifulSoup(book_file.read())

        # break the book into pages
        pages = book_xml.document.findAll("page")
        trec_pages = [page_to_trec(p, i) for i, p in enumerate(pages)]

        for page in trec_pages:
            if page != "":
                out.write(page)

out.close()

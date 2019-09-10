#!/usr/bin/env python3

import sqlite3
from bs4 import BeautifulSoup
import re
import json

import logging
logging.basicConfig(level=logging.DEBUG)

class Indexer:
    def __init__(self, crawl_db):
        self.index_urls = [] # list of normalised URLs in the index, position of a URL in here gives its posting ID
        self.index = {} # dictionary mapping token -> postings list for that token
        
        # Open DB
        self.db_conn = sqlite3.connect(crawl_db)   

    @staticmethod 
    def parse_html(html):
        soup = BeautifulSoup(html, "html.parser")
        for invisible in soup(("style", "script")):
            invisible.extract()
        text = soup.get_text()
        headings = []
        for heading in soup(("title", "h1", "h2", "h3", "h4", "h5", "h6")):
            headings.append(heading.get_text())
        meta_desc = None
        meta_tag = soup.find("meta", {"name": "description"})
        if meta_tag:
            if "content" in meta_tag.attrs:
                meta_desc = meta_tag["content"]
        return (text, headings, meta_desc) # (plain text of whole document, list of headings in plain text)

    @staticmethod
    def match_stoplist(token):
        # Stoplist is taken from Figure 2.5 of "Introduction to Information Retrieval", <https://nlp.stanford.edu/IR-book>
        # The letters 's' and 't' are also included, due to tokenising, e.g., "someone's" as ("someone", "s") and "don't" as ("don", "t")
        return token in ("a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it", "its", \
                         "of", "on", "that", "the", "to", "was", "were", "will", "with", "s", "t")

    @staticmethod
    def strip_s(word):
        if word.endswith("s"):
            return word[:-1]
        else:
            return word

    def tokenise(self, text):
        # text matched on \w+; tokens converted to lowercase; filtered with match_stoplist
        return map(self.strip_s, filter(lambda token: not self.match_stoplist(token), re.findall(r"\w+", text.lower())))

    def extract_tokens_and_metadata(self, document):
        '''Parse an HTML or plain text document and extract tokens with frequency scores and summary data.'''
        text, headings, meta_desc = self.parse_html(document)
        token_scores = {}
        # main body text
        for token in self.tokenise(text):
            if token in token_scores:
                token_scores[token] += 1
            else:
                token_scores[token] = 1
        # heading text
        for heading in headings:
            for token in self.tokenise(heading):
                if token in token_scores:
                    token_scores[token] += 100
                else:
                    token_scores[token] = 100
        # possible text in meta description tag
        if meta_desc:
            for token in self.tokenise(meta_desc):
                if token in token_scores:
                    token_scores[token] += 10
                else:
                    token_scores[token] = 10
        title = ""
        summary = ("meta", meta_desc)
        if len(headings) > 0: title = headings[0]
        if len(text) > 0 and not meta_desc: summary = ("text", re.sub("\s\s+", "\t", text[0:1000]))
        return (token_scores, title, summary, len(text)) # dict mapping token to score for this document for insertion into the index

    def read_crawl_db_iter(self):
        cur = self.db_conn.cursor()
        for row in cur.execute("SELECT url, html FROM crawl_data"):
            yield row
        cur.close()

    def add_to_index(self, token, posting):
        if token in self.index:
            self.index[token].append(posting)
        else:
            self.index[token] = [posting]
                
    def build_index(self):
        # build index in memory
        # convert URLs to posting IDs
        logging.info("Building index...")
        url_id = 0
        for url, html in self.read_crawl_db_iter():
            logging.info("Indexing: " + url)
            token_scores, title, description_data, doc_length = self.extract_tokens_and_metadata(html)
            logging.debug("  " + str(len(token_scores)) + " tokens found")
            for token in token_scores:
                self.add_to_index(token, (url_id, token_scores[token]))
            self.index_urls.append((url, title, description_data, doc_length))
            url_id += 1

    def store_index(self):
        # convert index and metadata to JSON and store as JSON-encoded strings in the crawl database
        logging.info("Storing index to database...")
        cur = self.db_conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS index_data (index_urls_json TEXT, index_json TEXT)")
        index_urls_json = json.dumps(self.index_urls, ensure_ascii=False)
        index_json = json.dumps(self.index, ensure_ascii=False).replace(" ", "")
        cur.execute("INSERT INTO index_data VALUES (?, ?)", (index_urls_json, index_json))
        cur.close()
        self.db_conn.commit()
        logging.info("Stored index! (" + str(len(index_urls_json) + len(index_json)) + " chars of JSON)")

#!/usr/bin/env python3

import sqlite3
import json
from indexer import Indexer

class Client:
    def __init__(self, crawl_db):
        self.db_conn = sqlite3.connect(crawl_db)

        index_urls_json, index_json = self.db_conn.execute("SELECT index_urls_json, index_json FROM index_data").fetchone()

        self.index_urls = json.loads(index_urls_json)
        self.index = json.loads(index_json)
        
    def query(self, query_string):
        query_terms = list(Indexer.tokenise(Indexer, query_string))
        
        url_scores = {} # dictionary mapping url ID to relevance score

        for term in query_terms:
            term_url_freq = self.term_query(term)
            if term_url_freq == None:
                continue
            for url_freq in term_url_freq:
                url_id = url_freq[0]
                freq = url_freq[1]
                if url_id in url_scores:
                    url_scores[url_id] += freq
                else:
                    url_scores[url_id] = freq

        results = [self.index_urls[url_id] for url_id in sorted(url_scores, key=url_scores.__getitem__, reverse=True)]
        return results
        
    def term_query(self, term):
        return self.index.get(term)

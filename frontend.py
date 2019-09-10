#!/usr/bin/env python3

import sqlite3

class Frontend:
    def __init__(self, crawl_db):
        # Open DB
        self.db_conn = sqlite3.connect(crawl_db)

    def write_json(self, index_urls_filename, index_filename):
        cur = self.db_conn.cursor()
        cur.execute("SELECT index_urls_json, index_json FROM index_data ORDER BY rowid DESC LIMIT 1")
        json = cur.fetchone()
        index_urls_json = json[0]; index_json = json[1]
        with open(index_urls_filename, 'w') as file:
            file.write(index_urls_json)
        with open(index_filename, 'w') as file:
            file.write(index_json)

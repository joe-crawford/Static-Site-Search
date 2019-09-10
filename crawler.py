#!/usr/bin/env python3

import sqlite3
from bs4 import BeautifulSoup
import requests
import urllib.parse

import logging
logging.basicConfig(level=logging.INFO)

class Crawler:
    def __init__(self, crawl_db, start_url=None):
        self.allowed_url_prefixes = []

        # Open DB
        self.db_conn = sqlite3.connect(crawl_db)
        cur = self.db_conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS crawl_data (
                           url TEXT PRIMARY KEY,
                           html TEXT
                       )''')
        cur.execute("CREATE TABLE IF NOT EXISTS visited (url TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS crawl_properties (name TEXT, value BOOLEAN)")
        self.db_conn.commit()

        # Start crawl here
        if start_url:
            self.add_allowed_prefix(start_url)
            self.crawl([start_url])

    @staticmethod
    def normalise(url):
        return urllib.parse.urlparse(url)[1:5] # strip scheme:// and #fragments

    def is_visited(self, url):
        urls = [self.normalise(values[0]) for values in self.db_conn.execute("SELECT url FROM visited").fetchall()]
        return self.normalise(url) in urls

    def visit(self, url):
        logging.info("Visiting: " + url)
        r = requests.get(url)
        logging.info("  status_code: " + str(r.status_code))
        if not r.ok:
            logging.warn("  error requesting page!")
            return None
        if "Content-Type" not in r.headers:
            logging.warn("  no Content-Type header!")
            return None
        content_type = r.headers["Content-Type"].lower()
        if "text/html" not in content_type:
            logging.info("  Content-Type: " + content_type)
            if "text/plain" in content_type:
                return(r.url, r.text, [])
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                links.append(urllib.parse.urljoin(r.url, href.strip()))
        logging.info("  found " + str(len(links)) + " links")
        return (r.url, r.text, links)

    def mark_visited(self, url):
        self.db_conn.execute("INSERT INTO visited VALUES (?)", (url,))
        self.db_conn.commit()

    def url_match(self, url):
        '''Check whether url matches one of the allowed URL patterns for this crawl.

        This is used to determine whether the URL will be crawled or not.'''
        parsed_url = urllib.parse.urlparse(url)
        # check url scheme, file extension, netloc and rest of path
        return self.match_url_scheme(parsed_url) and self.match_url_fileext(parsed_url) and self.match_url_prefix(parsed_url)

    @staticmethod
    def match_url_scheme(parsed_url):
        '''Check whether parsed_url matches an allowed URL scheme to crawl.'''
        return parsed_url.scheme in ("http", "https")

    @staticmethod
    def match_url_fileext(parsed_url):
        '''Check whether parsed_url matches an allowed file extension to crawl.''' 
        poss_ext = parsed_url.path[-5:].lower()
        if poss_ext[-5:] in (".tiff", ".docx", ".xlsx", ".pptx", ".flac", ".aiff", ".jpeg", ".webm", ".mpeg", ".webp") or \
           poss_ext[-4:] in (".iso", ".zip", ".exe", ".pdf", ".gif", ".jpg", ".png", ".bz2", ".jar", ".bmp", ".tif",
                             ".cab", ".ppt", ".xls", ".doc", ".pub", ".rar", ".msi", ".deb", ".rpm", ".mp4", ".mp3",
                             ".wav", ".wmv", ".ogg", ".ogv", ".m4a", ".flv", ".aac", ".dvi", ".tex", ".svg", ".eps",
                             ".tgz", ".ttf", ".otf", ".img", ".dmg", ".smi") or \
           poss_ext[-3:] in (".gz", ".ps", ".xz", ".7z", ".ai") or \
           poss_ext[-2:] in (".z"):
            return False
        return True

    def match_url_prefix(self, parsed_url):
        '''Check whether parsed_url matches an allowed URL prefix (i.e. matches the network location (in full) and path (as a string prefix)).

        Allowed URL prefixes are set by the add_allowed_prefix method.'''
        for prefix in self.allowed_url_prefixes:
            if prefix.netloc == parsed_url.netloc and "".join(parsed_url[1:5]).startswith("".join(prefix[1:5])):
                return True
        return False

    def add_allowed_prefix(self, url_prefix):
        '''Set an allowed URL prefix for this crawl.

        A URL will be crawled if it matches one or more allowed prefixes.'''
        self.allowed_url_prefixes.append(urllib.parse.urlparse(url_prefix))

    def crawl(self, to_visit=[]):
        logging.info("Starting crawl...")
        for link in to_visit:
            if self.is_visited(link):
                continue
            logging.debug(str(len(to_visit)) + " links in to_visit: " + str(to_visit))
            v = self.visit(link)
            if v == None:
                continue
            url, html, next_links = v
            if self.url_match(url) and not self.is_visited(url):
                self.db_conn.execute("INSERT INTO crawl_data VALUES (?, ?)", (url, html))
                self.db_conn.commit()
                self.mark_visited(link)
                if url != link: self.mark_visited(url) # might have url != link, e.g. if a redirect occurs
                for next_link in next_links:
                    if next_link not in to_visit and self.url_match(next_link) and not self.is_visited(next_link):
                        to_visit.append(next_link)
        self.db_conn.execute("INSERT INTO crawl_properties VALUES (?, ?)", ("finished", True))
        self.db_conn.commit()

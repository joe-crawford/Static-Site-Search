#!/usr/bin/env python3

if __name__ == "__main__":
    import sys
    import argparse
    import os
    import shutil
    from .crawler import Crawler
    from .indexer import Indexer
    from .frontend import Frontend
    
    parser = argparse.ArgumentParser(description='Generate a "static" website search engine', prog="Static-Site-Search")                                     
    parser.add_argument("--urls", nargs="+", required=True, help="list of full URL(s) to crawl, e.g. https://www.example.org")
    parser.add_argument("--output", nargs=1, required=True, help="output directory, which must not already exist")
    args = parser.parse_args()
    
    urls = args.urls
    output_directory = args.output[0]
    print(">>>", urls)
    
    if os.path.exists(output_directory):
        exit("Error: output directory `" + output_directory + "` already exists.")

    output_directory = os.path.realpath(output_directory)
    os.makedirs(output_directory)
    os.chdir(output_directory)

    # Crawl the URL:
    crawler = Crawler("crawldb.sqlite3")
    for url in urls:
        crawler.add_allowed_prefix(url)
    crawler.crawl([urls[0]])

    # Index the crawl database:
    indexer = Indexer("crawldb.sqlite3")
    indexer.build_index()
    indexer.store_index()

    # Output the index data in JSON:
    frontend = Frontend("crawldb.sqlite3")
    frontend.write_json("index_urls.json", "index.json")
    
    # Clean up temporary files:
    os.remove("crawldb.sqlite3")

    # Copy files for the web interface:
    module_directory = os.path.dirname(sys.argv[0])
    for filename in ("search.html", "search.js", "preload.js", "search.css"):
        shutil.copyfile(os.path.join(module_directory, filename), filename)
    
        

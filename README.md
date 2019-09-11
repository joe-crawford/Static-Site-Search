# Static-Site-Search

Static-Site-Search is a Python program (module) for generating a search engine for static websites. The generated search engine itself consists only of HTML, JavaScript, CSS and JSON files, so can be uploaded as part of a static site, for example to a GitHub Pages site.

As an example of the sort of output to expect, see [this demo search engine](https://joe-crawford.github.io/Static-Site-Search/search-demo/search.html).

## Getting the program

This shows one way to download the program from this GitHub repository, assuming that you have Git and Python 3 installed already:

```bash
$ git clone https://github.com/joe-crawford/Static-Site-Search.git  # download the repository from GitHub
$ python3 -m venv Static-Site-Search  # create a virtualenv in the repository directory
$ source Static-Site-Search/bin/activate # activate the new virtualenv, the shell prompt should change:
(Static-Site-Search) $ pip install -r Static-Site-Search/requirements.txt # install dependencies*
```
\**you may want to inspect the requirements.txt file, which lists Python package dependencies to be installed by the last command above, before running that command.*

You are now ready to use the program, for example:

```bash
(Static-Site-Search) $ python3 -m Static-Site-Search --urls https://www.example.org --output example-search/
```
will create a "static search engine" for the website https://www.example.org in the file `search.html` in the example-search/ directory. Try opening this file in your browser, and you should be able to search for the world "Example", and one page will appear as a result (which is the only page on https://www.example.org).

## Using the program

The syntax to run the program is:
```bash
python3 -m Static-Site-Search --urls [list of URLs allowed to crawl, starting at the first] --output [output directory]
```
Both arguments, --urls and --output, are required. The --urls argument can be one domain, or a list of many. You can also include a path to restrict the crawler to a certain part of the website. For example, 
```bash
python3 -m Static-Site-Search --urls https://www.example.org/path --output output/
```
will start crawling from https://www.example.org/path, and only follow links which also start with https://www.example.org/path.

To allow the crawler to crawl multiple domains, even subdomains, you must specify this explicitly. For example, to crawl both https://www.example.org (with www) and https://example.org (no www), you must use:
```bash
python3 -m Static-Site-Search --urls https://www.example.org https://example.org --output output/
```

The crawl will start from the URL that appears first in the list. You must also specify if you want to crawl both the HTTP and HTTPS versions of a website:
```bash
python3 -m Static-Site-Search --urls https://www.example.org http://www.example.org --output output/
```
will start crawling from https://www.example.org and is allowed to follow links to http://www.example.org. Without specifying http://www.example.org as a second URL, the crawler will crawl only https://www.example.org, without following any links to the HTTP version of the website. This may be important if the content of the HTTP and HTTPS versions of the same website differ.

## Including the generated search engine on your static website

The generated output includes a `preload.js` script, which you can include on your web pages to cache the index files required for the search engine in your users' browsers in the background. It also lets you add a search box to any page on your website by adding some appropriate HTML elements. For more information, see [this demonstration page](https://joe-crawford.github.io/Static-Site-Search/search-demo/).

"use strict";

// From preload.js:
const SEARCH_PATH_PREFIX = "/Static-Site-Search/search-demo/";
const storagePrefix = "static-site-search-973804c0-";
const expiryTimeMilliseconds = 24 * 60 * 60 * 1000;
const resourceLocations = [["index", SEARCH_PATH_PREFIX+"index.json"], ["index_urls", SEARCH_PATH_PREFIX+"index_urls.json"]];
function getJSONString(url, callback) {
	let request = new XMLHttpRequest();
	request.overrideMimeType("application/json");
	request.open("GET", url, true);
	request.onload = function () {
		callback(request.responseText);
	};
	request.send(null);
}
function store(key, value) {
	return localStorage.setItem(storagePrefix+key, value);
}
function load(key) {
	return localStorage.getItem(storagePrefix+key);
}
function requestAndStoreTimestamped(url, key, callback) {
	getJSONString(url, function(responseText) {
		store(key, responseText);
		store(key+"-time", Date.now());
		if (callback) callback();
	});
}
function isStale(key) {
	let keyTime = load(key+"-time");
	if (Boolean(keyTime) && Boolean(load(key))) {
		return Math.abs((Date.now() - keyTime)) > expiryTimeMilliseconds;
	} else {
		return true;
	}
}

// Resource loading

let resources = {};

function unpackResources() {
	for (const resource of resourceLocations) {
		let key = resource[0];
		resources[key] = JSON.parse(load(key));
	}
}

function loadMissingResources() {
	displayLoading();

	let resourcesPossiblyMissing = resourceLocations.length;
	
	function afterResourceFound() {
		resourcesPossiblyMissing--;
		if (resourcesPossiblyMissing === 0) allResourcesLoaded();
	}	

	for (const resource of resourceLocations) {
		let key = resource[0];
		let url = resource[1];
		if (isStale(key)) {
			console.log("Static-Site-Search: resource not loaded, downloading: " + key);
			requestAndStoreTimestamped(url, key, afterResourceFound);
		} else {
			console.log("Static-Site-Search: resource already loaded: " + key);
			afterResourceFound();
		}
	}
}

let shouldPerformHashQuery;

function allResourcesLoaded() {
	clearResults();
	displayLoaded();
	unpackResources();
	if (shouldPerformHashQuery) {
		performHashQuery();
	}
}

// Search functions

function tokenise(text) {
	/* should match Indexer.tokenise in indexer.py */
	const stoplist = ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it", "its",
	                  "of", "on", "that", "the", "to", "was", "were", "will", "with", "s", "t"];
	const tokenRegex = /\w+/gu;
	let tokens = [];
	text = text.toLowerCase();
	let match;
	while ((match = tokenRegex.exec(text)) !== null) {
		match = match[0];
		if (!stoplist.includes(match)) {
			tokens.push(match);
		}
	}
	for (let i=0; i < tokens.length; i++) {
		if (tokens[i].slice(-1) === "s") {
			tokens[i] = tokens[i].slice(0, -1);
		}
	}
	return tokens;
}

function termQuery(term) {
	return resources.index[term];
}

function query(queryString) {
	const queryTerms = tokenise(queryString)
	
	let urlScores = {};
	
	for (let term of queryTerms) {
		let termUrlFreq = termQuery(term);
		if (termUrlFreq) {
			for (const urlFreq of termUrlFreq) {
				let urlID = urlFreq[0];
				let freq = urlFreq[1];
				if (urlScores.hasOwnProperty(urlID)) {
					urlScores[urlID] += freq;
				} else {
					urlScores[urlID] = freq;
				}
			}
		}
	}
	
	let sortedUrlIDs = Object.entries(urlScores).sort(function (a, b) { return b[1] - a[1]; });
	let results = [];
	for (let urlID of sortedUrlIDs) {
		urlID = urlID[0];
		results.push(resources["index_urls"][urlID]);
	}
	return results;
}

// Display functions

function clearResults() {
	document.querySelector("main").innerHTML = "";
}

function noResults() {
	document.querySelector("main").innerHTML = "<p class='results-count'>No results found.</p>";
}

function displayLoading() {
	document.querySelector("main").innerHTML = "<p class='loading'>Loading search index, please wait&hellip;</p>";
}

function displayLoaded() {
	console.log("Static-Site-Search: All resources loaded.");
}

function displayResults(results) {
	const resultsList = document.querySelector("main");
	for (const result of results) {
		// format of result is [url, title, summary text, document lenght]
		let url = result[0]; let title = result[1]; let descriptionData = result[2];
		const newResultElem = document.importNode(document.querySelector("template#result-template").content, true);
		newResultElem.querySelector("h1 a").textContent = title;
		newResultElem.querySelectorAll("a").forEach(function (e) { e.href = url; });
		newResultElem.querySelector("a.result-url").textContent = url;
		newResultElem.querySelector("p.result-summary").textContent = summariseDescription(descriptionData);
		
		resultsList.appendChild(newResultElem);
	}
}

function summariseDescription(description) {
	let description_type = description[0];
	description = description[1];
	
	if (description_type === "meta") {
		return description;
	}

	function wordCount(text) {
		let parts = text.split(/\s+/gu);
		let words = [];
		for (let part of parts) {
			if (part.length > 0) {
				words.push(part);
			}
		}
		return words.length;
	}
	
	let parts = description.split(/[\n|\t]+/gu);
	let keepParts = [];
	let foundPart = false;
	for (let part of parts) {
		if (wordCount(part) > 10 || foundPart) {
			keepParts.push(part);
			foundPart = true;
		}
	}
		
	let summary = "";
	for (let part of keepParts) {
		if (summary.length < 140) {
			summary += (" " + part);
		}
	}
	
	return summary;
}

function bindUI() {
	document.querySelector("button#search-button").addEventListener("click", function () {
		const input = document.querySelector("input#search-bar").value;
		
		if (input !== "") {
			clearResults();
			displayResults(query(input));
		} else {
			clearResults();
		}
	});
	document.querySelector("input#search-bar").addEventListener("keydown", function (event) {
		if (event.key === "Enter") {
			document.querySelector("button#search-button").click();
		}
	});
}

// Handle queries from URL hash

let hashQuery;

function detectHashQuery() {
	document.querySelector("input#search-bar").value = "";
	if (window.location.hash.slice(0, 3) === "#q=") {
		hashQuery = decodeURIComponent(window.location.hash.slice(3));
		document.querySelector("input#search-bar").value = hashQuery;
	}
}

function performHashQuery() {
	// this function is called from allResourcesLoaded, so we are sure we are able to perform the query
	if (hashQuery) {
		document.querySelector("button#search-button").click();
	}
}

function setPerformHashQuery() {
	shouldPerformHashQuery = true;
}

// Start here...

function main() {
	detectHashQuery();
	if (hashQuery) setPerformHashQuery();
	bindUI();
	loadMissingResources();
}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", main);
} else {
	main();
}

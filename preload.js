(function () {
"use strict";

const SEARCH_PATH_PREFIX = "";

// fixed random prefix for localStorage keys so that they don't get accidentally clobbered
const storagePrefix = "static-site-search-973804c0-";

// time before resources in localStorage are considered stale (in milliseconds)
const expiryTimeMilliseconds = 24 * 60 * 60 * 1000;

// resource [key, path]-pairs
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

function bindUI() {
	const searchBar = document.querySelector("input#static-site-search-bar");
	const searchButton = document.querySelector("button#static-site-search-button");
	
	searchButton.addEventListener("click", function () {
		const input = searchBar.value;
		if (input !== "") {
			window.location = SEARCH_PATH_PREFIX + "search.html#q=" + encodeURIComponent(input);
		}
	});
	searchBar.addEventListener("keydown", function (event) {
		if (event.key === "Enter") {
			searchButton.click();
		}
	});
}

function preload() {
	for (const resource of resourceLocations) {
		let key = resource[0];
		let url = resource[1];
		if (isStale(key)) {
			requestAndStoreTimestamped(url, key);
		}
	}
}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", bindUI);
} else {
	bindUI();
}

preload();
})();

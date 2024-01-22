# filename: arxiv_gpt4_search.py
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# Base api query url
base_url = 'http://export.arxiv.org/api/query?'

# Search parameters
query = 'gpt-4'
max_results = 1
sort_by = 'submittedDate'
sort_order = 'descending'

# Construct query with parameters
query_params = urllib.parse.urlencode({
    "search_query": query,
    "start": 0,
    "max_results": max_results,
    "sortBy": sort_by,
    "sortOrder": sort_order
})

# Perform the GET request
response = urllib.request.urlopen(base_url + query_params).read()

# Parse the response using ElementTree
root = ET.fromstring(response)

# arXiv namespace
ns = {'arxiv': 'http://arxiv.org/schemas/atom'}

# Find the entry element in the feed
entry = root.find('arxiv:entry', ns)

if entry is not None:
    # Extract and output necessary information from the entry
    title = entry.find('arxiv:title', ns).text
    authors = [author.find('arxiv:name', ns).text for author in entry.findall('arxiv:author', ns)]
    summary = entry.find('arxiv:summary', ns).text
    url = entry.find('arxiv:id', ns).text

    print("Title: ", title)
    print("Authors: ", ', '.join(authors))
    print("Abstract: ", summary)
    print("URL: ", url)
else:
    print("No papers found on GPT-4.")
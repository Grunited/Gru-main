# filename: search_arxiv.py
import urllib.parse
import urllib.request
import feedparser

# Base API query URL
base_url = 'http://export.arxiv.org/api/query?'

# Search parameters
search_query = 'all:gpt-4'  # search for the keyword 'gpt-4' in all fields
start = 0                    # start at the first result
total_results = 1            # want only the most recent paper
sort_by = 'submittedDate'    # sort by submission date
sort_order = 'descending'    # sort in descending order, so the recent papers come first

# Construct the query with the search parameters
query = f'search_query={search_query}&start={start}&max_results={total_results}&sortBy={sort_by}&sortOrder={sort_order}'
url = base_url + query

# Perform the GET request and parse the response
response = urllib.request.urlopen(url)
feed = feedparser.parse(response)

# Output the entry information
if feed.entries:
    for entry in feed.entries:
        print('Title:', entry.title)
        print('Published:', entry.published)
        print('Authors:', ', '.join(author.name for author in entry.authors))
        print('Abstract:', entry.summary)
        print('Link to paper:', entry.id)
else:
    print('No papers found on GPT-4.')
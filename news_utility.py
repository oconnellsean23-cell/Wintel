import feedparser
import urllib.parse
import requests

def get_google_news(school_name):
    # THE FIX: Using intitle: forces the school name to be in the actual headline.
    # We also stripped out the "AND" operators which Google RSS sometimes misinterprets.
    query = f'intitle:"{school_name}" ("mental health" OR wellness OR counseling OR "student affairs" OR therapy)'
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)
    
    articles = []
    for entry in feed.entries[:5]: 
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'source': 'Google News RSS' 
        })
        
    return articles

def get_newsapi_articles(school_name, api_key):
    url = "https://newsapi.org/v2/everything"
    query = f'"{school_name}" AND ("mental health" OR wellness OR counseling OR "student affairs" OR therapy)'
    
    params = {
        'q': query,
        'searchIn': 'title,description', 
        'language': 'en',
        'sortBy': 'relevancy', 
        'apiKey': api_key,
        'pageSize': 5 
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    articles = []
    if data.get('status') == 'ok':
        for article in data['articles']:
            articles.append({
                'title': article['title'],
                'source': article['source']['name'],
                'link': article['url'],
                'published': article['publishedAt'],
                'description': article['description']
            })
            
    return articles
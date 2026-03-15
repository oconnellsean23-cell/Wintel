import feedparser
import urllib.parse
import requests

def get_google_news(school_name):
    # ADDED: -study -research -faculty -professor to eliminate academic papers
    # ADDED: "counseling center" and "student affairs" for higher-intent administrative news
    query = f'"{school_name}" AND ("counseling center" OR "student affairs" OR "mental health" OR "wellness") -sports -football -basketball -hockey -study -research -faculty -professor'
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
    query = f'"{school_name}" AND ("mental health" OR wellness OR counseling OR "student affairs")'
    
    params = {
        'q': query,
        'searchIn': 'title,description', # <--- THE MAGIC FIX: Only searches headlines/summaries
        'language': 'en',
        'sortBy': 'relevancy', # Changed from 'publishedAt' to prioritize exact matches
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
import feedparser
import urllib.parse
import requests

def get_google_news(school_name):
    # Hunting for relevant institutional/student wellness news and filtering out sports
    query = f'"{school_name}" AND ("wellness" OR "mental health" OR "administration" OR "partnership") -football -basketball -hockey'
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
    # Similar query logic formatted for NewsAPI
    query = f'"{school_name}" AND (wellness OR health OR administration OR student)'
    
    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt', 
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
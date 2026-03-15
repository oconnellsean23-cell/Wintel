import feedparser
import urllib.parse
import requests

def get_google_news(school_name):
    # We ask Google for a slightly broader search but force the school name in the title
    query = f'intitle:"{school_name}" ("mental health" OR wellness OR counseling OR "student affairs")'
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)
    
    # --- THE PYTHON VETO FILTER ---
    # If any of these words are in the headline, the article is thrown in the trash.
    # You can add to this list anytime you see a weird trend!
    spam_words = ["study", "research", "professor", "tips", "finds", "expert", "scientists", "gene", "pain", "hospital"]
    
    articles = []
    for entry in feed.entries:
        title_lower = entry.title.lower()
        
        # Check if any spam word is in the title
        is_spam = any(spam_word in title_lower for spam_word in spam_words)
        
        # Only add the article if it passes the spam check
        if not is_spam:
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.published,
                'source': 'Google News RSS' 
            })
            
        # Stop once we have 5 high-quality articles
        if len(articles) >= 5:
            break
            
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
import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
import os.path
from datetime import date, timedelta
import json

class Article:
    def __init__(self, url, headline, author, date):
        self.url = url
        self.headline = headline
        self.author = author
        self.date = date
        
class WebScraper:
    def __init__(self, url):
        self.url = url
    
    def get_articles(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = json.loads(soup.find('script', type='application/json').text)
        result = []
        for article in articles['props']['pageProps']['hydration']['responses']:
            for data in article['data']['community']['frontPage']['placements']:
                if data['placeable'] != None:
                    headline = data['placeable']['title']
                    url = data['placeable']['url']
                    author = data['placeable']['author']['fullName']
                    date_str=(data['placeable']['publishDate'][:10])
                    year, month, day = map(int, date_str.split('-'))
                    date_obj = date(year, month, day)

                    result.append(Article(url, headline, author, date_obj))
        return result

class ArticleStorage:
    def __init__(self, filename,dbfilename):
        self.filename = filename
        self.dbfilename = dbfilename
        
    def store_csv(self, articles):
        with open(self.filename, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'URL', 'headline', 'author', 'date'])
            for i, article in enumerate(articles):
                writer.writerow([i, article.url, article.headline, article.author, article.date])
                
    def create_sqlite_db(self):
        conn = sqlite3.connect(self.dbfilename)
        print(self.dbfilename)
        c = conn.cursor()
        c.execute('''CREATE TABLE articles
                     (id INTEGER PRIMARY KEY, url TEXT, headline TEXT, author TEXT, date DATE)''')
        conn.commit()
        conn.close()
        
    def store_sqlite(self, articles):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        i =0
        for article in articles:
            c.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?)",
                      (i, article.url, article.headline, article.author, article.date))
            i += 1
        conn.commit()
        conn.close()
        
    def has_duplicate(self, article):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM articles WHERE url = ?", (article.url,))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    
    def store_articles(self, articles):
        for article in articles:
            self.store_sqlite([article])
        
if __name__ == '__main__':
    today = date.today()
    yesterday = today - timedelta(days=1)
    filename = yesterday.strftime('%d%m%Y') + '_verge.csv'

    url = 'https://www.theverge.com/'
    scraper = WebScraper(url)
    articles = scraper.get_articles()
    
    storage = ArticleStorage(filename,"dbfile")

    storage.create_sqlite_db()
    storage.store_csv(articles)
    storage.store_articles(articles)

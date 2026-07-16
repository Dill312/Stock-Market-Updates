import requests
import html
import smtplib
import yfinance as yf
from email.mime.text import MIMEText
import datetime as dt
from watchlist import watchlist
import os

def main():
    news_api_key = os.environ.get("NEWS_API_KEY")
    news_website = "https://newsapi.org/v2/everything"
    
    my_email = os.environ.get("MY_EMAIL")
    password = os.environ.get("PASSWORD")
    to_email = os.environ.get("TO_EMAIL")
    
    if not news_api_key or not my_email or not password or not to_email:
        raise ValueError("Missing environment variables")
        
    for stock_info in watchlist:
        news_parameters = {
            "q": stock_info["company"],
            "from": (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d"),
            "sortBy": "popularity",
            "apiKey": news_api_key,
        }
        
        stock = yf.Ticker(stock_info["stock"])
        history = stock.history(period="5d")
        closes = history["Close"].dropna().tolist()
    
        if len(closes) < 2:
            continue
            
        previous_close = closes[-2]
        latest_close = closes[-1]
        
        percent_change = (latest_close - previous_close) / previous_close * 100
        
        if percent_change > 0:
            arrow = "🔺"
        else:
            arrow = "🔻"
        print(f"Checked {stock_info['stock']}: {arrow}{abs(percent_change):.2f}%")   
        if abs(percent_change) >= stock_info["threshold"]:
            news_response = requests.get(url=news_website, params=news_parameters)
            news_response.raise_for_status()
            news_data = news_response.json()
            
            articles = news_data["articles"]
            news_stories = []
            
            for article in articles[:3]:
                story = {
                    "headline": html.unescape(article["title"] or "No headline"),
                    "summary": html.unescape(article["description"] or "No summary available"),
                    "website": html.unescape(article["url"]),
                }
                news_stories.append(story)
    
            if len(news_stories) < 3:
                continue
    
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                
                message = f"""\
{stock_info['company']} has moved {arrow}{abs(percent_change):.2f}%
Headline: {news_stories[0]['headline']}
Summary: {news_stories[0]['summary']}
Website: {news_stories[0]['website']}
                        
Headline: {news_stories[1]['headline']}
Summary: {news_stories[1]['summary']}
Website: {news_stories[1]['website']}
                        
Headline: {news_stories[2]['headline']}
Summary: {news_stories[2]['summary']}
Website: {news_stories[2]['website']}
                """
    
                email = MIMEText(message, "plain", "utf-8")
                email["Subject"] = f"{stock_info['company']}: {arrow}{abs(percent_change):.2f}%"
                email["From"] = my_email
                email["To"] = to_email
    
                connection.send_message(email)

if __name__ == "__main__":
    main()
    

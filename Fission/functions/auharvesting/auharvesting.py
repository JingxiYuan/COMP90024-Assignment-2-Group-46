import logging, json, requests, socket
from flask import current_app
import warnings,ssl
warnings.filterwarnings("ignore")
from mastodon import Mastodon
from bs4 import BeautifulSoup
import nltk
try:
    nltk.download('vader_lexicon')
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
from nltk.sentiment import SentimentIntensityAnalyzer

au_client_id = "6mpOKYS9AqQloIOFkSR0uGF0EOvekMUEhJ0Sjul4mRQ"
au_client_secret = "kbf6RaLjK40PrmlMupcN6lgTaVGqpJwyTTspIhgCr8E"
au_access_token = "0LIfIQQ0uxBCwrpc2V8Ipgp8qE4cBZwdNmz3-NkfX1w"
au_api_base_url = 'https://mastodon.au'

def parse_time(toot):
    tmp = toot.created_at.strftime("%Y-%m-%dT%H:%M:%S")
    return tmp


def parse_content(toot):
    text = toot['content'].replace("*", " ")
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()
    text = text.lower()
    return text


def get_sentiment(text):
    sentiment = SentimentIntensityAnalyzer().polarity_scores(text)
    compound_score = sentiment['compound']

    compound_tmp = 0
    if compound_score <= -0.8:
        compound_tmp = 1
    elif -0.8 < compound_score <= -0.6:
        compound_tmp = 2
    elif -0.6 < compound_score <= -0.4:
        compound_tmp = 3
    elif -0.4 < compound_score <= -0.2:
        compound_tmp = 4
    elif -0.2 < compound_score < 0.2:
        compound_tmp = 5
    elif 0.2 <= compound_score < 0.4:
        compound_tmp = 6
    elif 0.4 <= compound_score < 0.6:
        compound_tmp = 7
    elif 0.6 <= compound_score < 0.8:
        compound_tmp = 8
    else:
        compound_tmp = 9

    return compound_tmp


def main():
    au_mast = Mastodon(access_token=au_access_token, client_id=au_client_id, client_secret=au_client_secret,
                       api_base_url=au_api_base_url)
    au_response = au_mast.timeline_public(limit=40, remote=True)

    for i in range(0, len(au_response)):
        au_response[i]["created_at"] = parse_time(au_response[i])
        text = parse_content(au_response[i])
        au_response[i]["content"] = text
        au_response[i]["sentiment"] = get_sentiment(text)

    upload = []
    temp = ["created_at", "content", "sentiment", "id"]
    for i in au_response:
        temp_dict = {k:v for k,v in i.items() if k in temp}
        upload.append(temp_dict)

    current_app.logger.info(f"Harvested {len(upload)} From Mastodon's AU server")

    requests.post(url='http://router.fission/enqueue/mastodonau',
                  headers={'Content-Type': 'application/json'},
                  data=json.dumps({"toots": upload})
                  )
    return json.dumps({"toots": upload})




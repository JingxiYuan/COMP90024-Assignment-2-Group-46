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

social_client_id = "hdjtrbMbuCHM8NLIuNwdhiePeBgfclasQN9pLD7jSdY"
social_client_secret = "pBgdU1FxD_z0PeTJgKGmHPDJor-CkkuvvmetO_XLxRo"
social_access_token = "aUaVtzTFZZjGIAFt3tQNQdJUwXc67jQ_hFUSKm8pRKM"
social_api_base_url = 'https://aus.social'

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
    social_mast = Mastodon(access_token=social_access_token, client_id=social_client_id,
                           client_secret=social_client_secret,
                           api_base_url=social_api_base_url)
    # social_response = social_mast.timeline_public(limit=40)
    social_crime_response = social_mast.timeline_hashtag(hashtag="carcrash", limit=40)

    for i in range(0, len(social_crime_response)):
        social_crime_response[i]["created_at"] = parse_time(social_crime_response[i])
        text = parse_content(social_crime_response[i])
        social_crime_response[i]["content"] = text
        social_crime_response[i]["sentiment"] = get_sentiment(text)

    upload = []
    temp = ["created_at", "content", "sentiment", "id"]
    for i in social_crime_response:
        temp_dict = {k:v for k,v in i.items() if k in temp}
        upload.append(temp_dict)

    current_app.logger.info(f"Harvested {len(upload)} From Mastodon's Social crash server")

    requests.post(url='http://router.fission/enqueue/mastodoncrash',
                  headers={'Content-Type': 'application/json'},
                  data=json.dumps({"crime_toots": upload})
                  )
    return json.dumps({"crime_toots": upload})


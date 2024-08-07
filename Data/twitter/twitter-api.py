import collections
import json
import pandas as pd
import requests

bearer_token = ("AAAAAAAAAAAAAAAAAAAAALEmtgEAAAAAKnt%2FFSUJd%2BMy2Udei%2FOfsQoR4t0"
                "%3DOVGAyUAjKxbzgdD0lxts5gdp0nLLxxL3KQ8Z0JB6CNaV4lIrS0")


def bearer_oauth(r):
    r.headers['Authorization'] = f"Bearer {bearer_token}"
    return r


def main():
    keywords = ['car', 'accident', 'crime', 'criminal', 'weather', 'population', 'pollution']
    hashtags = ['#' + w for w in keywords]
    query = f"({' 0R '.join(keywords)}) ({' OR '.join(hashtags)}) lang:en -is:retweet -is:reply -is:quote"

    query_params = {'query': query, 'max_results': 100, 'tweet.fields': 'created_at'}
    url = "https://api.twitter.com/2/tweets/search/recent"

    tweets = collections.defaultdict(list)
    for _ in range(2):
        r = requests.get(url, auth=bearer_oauth, params=query_params)
        res = json.loads(r.text)
        print(res)
        query_params['next_token'] = res['meta']['next_token']
        for tweet in res['data']:
            for field in ['created_at', 'id', 'next']:
                tweets[field].append(tweet[field])

    df = pd.DataFrame(tweets)
    df.to_csv('tweets.csv', index=False)


if __name__ == '__main__':
    main()

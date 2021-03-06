from text_mining import TextCleaner
import tweepy
import click
from pathlib import Path
from dotenv import load_dotenv
from tweepy.error import TweepError
import os
import pandas as pd
from datetime import datetime
load_dotenv()


consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

filepath = Path(Path(__file__).resolve()).parent

def user_collection(top_words_df):
    file = f"{filepath}/user_collection.csv"
    if os.path.exists(file):
        col = pd.read_csv(file)
        col = pd.concat([col, top_words_df], axis=0)
        col.to_csv(file, index=False)
    else:
        top_words_df.to_csv(file, index=False)

def keywords_collection(top_words_df):
    file = f"{filepath}/keyword_collection.csv"
    if os.path.exists(file):
        col = pd.read_csv(file)
        col = pd.concat([col, top_words_df], axis=0)
        col.to_csv(file, index=False)
    else:
        top_words_df.to_csv(file, index=False)


def get_top_words(user_name=None, keywords=None, min_freq=1):
    # collecting tweets
    try:
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        if user_name is not None:
            print(f"tweet summary for @{user_name}:")
            tweets = api.user_timeline(screen_name=user_name, count=100)
        else:
            print(f"tweet summary for '{keywords}':")
            tweets = api.search(q=keywords, count=100, result_type='recent')
    except TweepError as e:
        error_code = eval(str(e))[0]['code']
        if str(error_code) == '34':
            print('page does not exist')
            return None
        else:
            raise TweepError(e)

    all_tweets = []
    for i in tweets:
        status = api.get_status(i.id, tweet_mode="extended")
        text = status.full_text
        text = " ".join(list(set(text.split())))
        all_tweets.append(text)

    all_tweets = " ".join(all_tweets)
    all_tweets = " ".join([i for i in all_tweets.split() if '@' not in i])
    all_tweets = " ".join([i for i in all_tweets.split() if '_' not in i])

    # text cleaning
    cleaner = TextCleaner()
    clean_df = cleaner.get_clean_text(text=all_tweets)
    clean_df = clean_df[clean_df['count'] > min_freq]

    if user_name is not None:
        clean_df['username'] = user_name
    elif keywords is not None:
        clean_df = clean_df[~clean_df.word.isin(keywords.lower().split())]
        clean_df['keywords'] = keywords

    clean_df = clean_df.head(10)

    # add time
    today = datetime.now()
    date = f"{today.year}{today.strftime('%m')}{today.strftime('%d')}"
    time = f"{today.hour:02d}:{today.minute:02d}"
    clean_df['report_date'] = date
    clean_df['time'] = time

    return clean_df

@click.command()
@click.option('--username', '-u')
@click.option('--search', '-s')
def main(username, search):
    if username is not None and search is not None:
        raise Exception('what?')
    elif username is not None:
        top_words = get_top_words(user_name=username)
        user_collection(top_words_df=top_words)
        click.echo(top_words)
    else:
        top_words = get_top_words(keywords=search)
        keywords_collection(top_words_df=top_words)
        click.echo(top_words)

if __name__ == '__main__':
    main()
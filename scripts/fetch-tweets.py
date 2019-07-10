import json
import pandas as pd
from flock import Flocka
from twython import Twython

# Load Twitter API credentials
with open("twitter-creds.json", "r") as f:
    creds = json.load(f)

# Instantiate a Twython object
python_tweets = Twython(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'])

# Create our query
query = {'q': 'Oracle',
         'result_type': 'popular',
         'count': '10',
         'lang': 'en',
        }

# Search tweets
t_dict = {'tweet_date': [], 'hashtags': [], 'text': [], 'twitter_user': [], 'user_loc': [], 'keyword': [] }
deEmojify = Flocka.deEmojify
getHashtags

            # Extract tweet and append to file
            basic = self.process_tweet(data)
            summary = self.summarize(data)
            basic['keyword'] = self.find_group(summary, self.groups)


for status in python_tweets.search(**query)['statuses']:
    t_dict['twitter_user'].append(deEmojify(object, status['user']['screen_name']))
    t_dict['tweet_date'].append(status['created_at'])
    t_dict['text'].append(deEmojify(object, status['text']))
    t_dict['favorite_count'].append(status['favorite_count'])

df = pd.DataFrame(t_dict)
df.sort_values(by='favorite_count', inplace=True, ascending=False)
# df.head(5)
print(df)
# print(python_tweets.get_application_rate_limit_status())


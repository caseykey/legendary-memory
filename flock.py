'''
Flock is a tool for fetching historical tweets or for streaming tweets live
Created by: Casey Key, SE Intern
Created: July 20th, 2019
'''
import csv # Exporting tweets
import datetime # Calculate rate of tweets
import json # Loading twitter credentials
import os # For finding console width
import pprint
import sys # For keyword 'track' arguments
import time # For finding last tweet in previous fetch
from twython import Twython, TwythonStreamer # Gateway to Twitter
from urllib3.exceptions import ProtocolError # For handling IncompleteRead error


class Flock(object): 
    def __init__(self, json_creds, output, cont):
        self._creds =  self.creds(json_creds)
        self._output = output # Output file
        self._cont = cont # Continue last query
        with open('./query.txt', 'r') as query:
            self._groups = self.get_search_terms() if not cont else json.load(query)

        self._streamer = Streamer(self._creds['CONSUMER_KEY'], self._creds['CONSUMER_SECRET'],
                                  self._creds['ACCESS_KEY'], self._creds['ACCESS_SECRET'],
                                  groups=self._groups, outfile=self._output)
    @staticmethod 
    def get_search_terms(): 
        '''
        Get keywords and labels from the user.
        For example "bitcoin" : {"btc", "bitcoin", "satoshi nakamoto"}
        Where "bitcoin" is the associated label for these search terms.
            - Saves query to query.txt
            - Returns a dictionary
        '''
        groups = []
        terms = {}
        
        try:
            print("What topics do you want to search for?\n")
            print("Press enter to use previous query.")
            print("Enter one topic per prompt.")
            print("Then, press enter when complete.\n")

            while True:
                label = input("Search label: ")
                # User entered empty input
                if not label:
                    if groups:
                        raise ValueError("Done with labels")
                    else:
                        # Do we have a previous query to load?
                        try:
                            with open('./query.txt', 'r') as f:
                                return json.load(f)
                        except FileNotFound as e:
                            print(e, ": must enter at least one label")
                        continue
                groups.append(label)

        # User finished adding topics
        # Now user adds  search terms associated with each topic
        except ValueError:
            print("\nEnter the keywords for your search.") 
            print("Press enter to continue.\n")
            for label in groups:
                terms[label] = [label]  
                try:
                    while True:
                        keyword = input("Keyword for " + label + ": ")
                        if not keyword:
                            raise ValueError("Done with keywords")
                        if keyword not in terms[label]:
                            terms[label].append(keyword)
                except:
                    continue
        
        except Exception as inst:
            print("Exception:", inst)
            print("Invalid input")
            sys.exit(1)
       
        # print(terms)

        with open('query.txt', 'w', newline='\n') as f:
            json.dump(terms, f)

        return terms
    
    def creds(self, json_creds):
        # Load Twitter API credentials
        if type(json_creds) is dict:
            return json_creds
        with open(json_creds, "r") as f:
            return json.load(f)

    
    # Flock().tracks = [term1, term2, ..., termN]
    @property
    def tracks(self):
        # Extract tracks from search_query
        tracks = []
        groups = self._groups
        for keywords in groups.values():
            for keyword in keywords:
                tracks.append(keyword)
        return tracks
    
    def start(self, quiet=True):
        print("Streaming tweets about:")   
        for index, track in enumerate(self.tracks):
            print(str(index) + ". " + track)

        stream = self._streamer
        stream.quiet = quiet

        # try/catch for clean exit after Ctrl-C
        try:
            # Start stream, restart on error
            # https://github.com/tweepy/tweepy/issues/908
            while True:
                try:
                    stream.statuses.filter(track=self.tracks)
                except (ProtocolError, AttributeError) as e:
                    print("Error:", e)
                    time.sleep(3)
                    continue
            
        except (KeyboardInterrupt, SystemExit):
            print("\nSaved", stream.total_tweets, "tweets in", stream.duration)
            

    
    def fetch(self, cont=False):
        api = Twython(self._creds['CONSUMER_KEY'], self._creds['CONSUMER_SECRET'])
        term_lists = [term for term in self._groups.values()]
        terms = []
        for tl in term_lists:
            for term in tl:
                terms.append(term)
        print("Fetching tweets matching: ", terms)
        input("Press enter to continue.")
        
        last_date = datetime.datetime.now()
        if cont:
            # Credit: Dave @ https://bit.ly/2JGPcUw
            with open(self._output, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                last_tweet = f.readline().decode()
            tweet_items = last_tweet.split(',')
            last_date = time.strptime(tweet_items[0], '%a %b %d %H:%M:%S +0000 %Y')
            print("Starting fetch from:", time.strftime('%a %b %d %H:%M:%S +0000 %Y', last_date))

        tweets = []
        MAX_ATTEMPTS = 20
        COUNT_OF_TWEETS_TO_BE_FETCHED = 5000000000000  # int(input("How many tweets would you like?: ")) 

        for i in range(0,MAX_ATTEMPTS):
            print("Attempt:", i)
            if(COUNT_OF_TWEETS_TO_BE_FETCHED < len(tweets)):
                print("got 500 tweets")
                break # we got 500 tweets... !!

            #----------------------------------------------------------------#
            # STEP 1: Query Twitter
            # STEP 2: Save the returned tweets
            # STEP 3: Get the next max_id
            #----------------------------------------------------------------#

            # STEP 1: Query Twitter
            results = []
            if(i == 0):
                # Query twitter for data.
                print("Query pt.1")
                for term in terms:
                    print("term: ", term)
                    results.append(api.search(q=term,count='100'))
                    print("results:", len(results))
                print("i==0:", results)
            else:
                # After the first call we should have max_id from result of previous call. Pass it in query.
                print('Query pt.2')
                for term in terms:
                    print("term: ", term)
                    results.append(api.search(q=term,include_entities='true',max_id=next_max_id))
                    print("results:", len(results))
                print("i else 0:", results)

            # STEP 2: Save the returned tweets
            for result in results:
                print("result")
                for status in result['statuses']:
                    print("Results:", len(results))
                    # Only collect tweets in English
                    #print("-----------------------\n\n\n\n\n\n\n\n")
                    #pp = pprint.PrettyPrinter(indent=2)
                    #pp.pprint(status)
                    #print("Summarized tweet --------------------------------")
                    #pp.pprint(summary)

                    if 'lang' in status and status['lang'] == 'en':
                        
                        # Extract tweet and append to file
                        basic = Streamer.process_tweet(status)
                        summary = Streamer.summarize(status)
                        # Note Streamer uses self.groups, not _groups. 
                        # TODO: Fix consistency
                        basic['keyword'] = Streamer.find_group(summary, self._groups)
                        if basic['keyword'] != "misc":

                            date = time.strptime(basic['tweet_date'], '%a %b %d %H:%M:%S +0000 %Y')
                            if cont == False or date > last_date:
                                # print("Tweet saved:", basic)
                                Streamer.save_to_csv(self._output, basic)


            # STEP 3: Get the next max_id
            try:
                # Parse the data returned to get max_id to be passed in consequent call.
                next_results_url_params = result['search_metadata']['next_results']
                next_max_id = next_results_url_params.split('max_id=')[1].split('&')[0]
            except:
                # No more next pages
                break


'''
Streamer takes api credentials, a "groups" dictionary, and an outfile
Used by the Flock class.
'''
class Streamer(TwythonStreamer):
    # start_time = None
    # last_tweet_time = None
    # total_tweets = None
    # total_difference = None
    

    def __init__(self, *creds, groups, outfile):
        self._start_time = datetime.datetime.now()
        self.last_tweet_time =  self._start_time
        self.total_tweets = 0
        self.total_difference = 0
        self.groups = groups
        self.outfile = outfile
        self._quiet = True
        super().__init__(*creds)  

    @property
    def quiet(self):
        return self._quiet

    @quiet.setter
    def quiet(self, value):
        self._quiet = value

    @property
    def duration(self):
        return datetime.datetime.now() - self._start_time

    # Received data
    def on_success(self, data):
            
        try: 
            # Only collect tweets in English
            if data['lang'] == 'en':
                self.total_tweets += 1
                
                # Calculate average time per tweet
                tweet_time = datetime.datetime.now()
                tweet_time_difference = tweet_time - self.last_tweet_time
                self.total_difference += tweet_time_difference.total_seconds()
                avg_time_per_tweet = self.total_difference / self.total_tweets
                self.last_tweet_time = tweet_time
                
                # Extract tweet and append to file
                basic = Streamer.process_tweet(data)
                summary = Streamer.summarize(data)
                basic['keyword'] = Streamer.find_group(summary, self.groups)
                if basic['keyword'] != "misc":
                    #pp = pprint.PrettyPrinter(indent=2)
                    #pp.pprint(data)
                    #print("Summarized tweet --------------------------------")
                    #pp.pprint(summary)
                    #print("Keyword:", basic['keyword'])
                    #sys.exit(1) 
                    Streamer.save_to_csv(self.outfile, basic)
                else:
                    with('errors.txt', 'a') as f:
                        f.write('Tweet filed under "misc":')
                        pp = pprint.PrettyPrinter(indent=2, stream=f)
                        f.write("Data:\n")
                        pp.pprint(data)
                        f.write("Summary:\n")
                        pp.pprint(summary)
                        f.write("Summary:\n", summary, "\n", self.groups)
                        print("Misc logged\n")
                        return
                
                # Update stream status to console
                try:
                    rows, columns = os.popen('stty size', 'r').read().split()
                    print('-' * int(columns))
                except:
                    # We are running headless
                    print('-' * 10)
                print(avg_time_per_tweet, "secs/tweet;", self.total_tweets, "total tweets")
                print("Keyword:", basic['keyword'], "Tweet:", basic['text'])
            
        except KeyError as e:
            with open('errors.txt', 'a') as f:
                    f.write('KeyError: ' + str(e))
                    f.write(str(data))
    
    # Problem with the API
    def on_error(self, status_code, data):
        print(status_code, data)
        self.disconnect()

    # Save each tweet to csv file
    @staticmethod
    def save_to_csv(outfile, tweet):
        with open(outfile, 'a', newline='\n') as f:
            if f.tell() == 0:
                try: header = list(tweet.keys())
                except Exception as e:
                    print(tweet)
                writer = csv.DictWriter(f,fieldnames=header, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                try: writer.writerow(list(tweet.values())) # Occasionally causes an error for no keys
                except Exception as e:
                    print(tweet)

            else:
                writer = csv.writer(f)
                writer.writerow(list(tweet.values())) # Occasionally causes an error for no keys


    '''
    Used for sanitizing input for ADW
    Credit: https://bit.ly/2NhKy4f
    '''
    @staticmethod
    def deEmojify(inputString):
        return inputString.encode('ascii', 'ignore').decode('ascii')

    '''
    This loads the most comprehensive text portion of the tweet  
    Where "data" is an individual tweet, treated as JSON / dict
    Inspired by: colditzjb @ https://github.com/tweepy/tweepy/issues/878
    '''
    @staticmethod
    def getText(data):       
        # Try for extended text of original tweet, if RT'd (streamer)
        try: text = data['retweeted_status']['extended_tweet']['full_text']
        except: 
            # Try for extended text of an original tweet, if RT'd (REST API)
            try: text = data['retweeted_status']['full_text']
            except:
                # Try for extended text of an original tweet (streamer)
                try: text = data['extended_tweet']['full_text']
                except:
                    # Try for extended text of an original tweet (REST API)
                    try: text = data['full_text']
                    except:
                        # Try for basic text of original tweet if RT'd 
                        try: text = data['retweeted_status']['text']
                        except:
                            # Try for basic text of an original tweet
                            try: text = data['text']
                            except: 
                                # Nothing left to check for
                                text = ''
        return text

    '''
    This loads the most comprehensive hashtag portion of the tweet  
    Where "data" is an individual tweet, treated as JSON / dict
    Inspired by: colditzjk @ https://github.com/tweepy/tweepy/issues/878
    '''
    @staticmethod
    def getHashtags(data):            
        try: text = data['quoted_status']['extended_tweet']['entities']['hashtags']
        except:
            # Try for extended text of original tweet, if RT'd (streamer)
            try: text = data['retweeted_status']['extended_tweet']['entities']['hashtags']
            except: 
                # Try for extended text of an original tweet, if RT'd (REST API)
                try: text = data['retweeted_status']['entities']['hashtags']
                except:
                    # Try for basic text of original tweet if RT'd 
                    try: text = data['retweeted_status']['entities']['hashtags']
                    except:
                        # Try f or basic text of an original tweet
                        try: text = data['entities']['hashtags']
                        except:
                            # Nothing left to check for
                            text = ''

        hashtags = []
        for entity in text:
            hashtags.append(entity["text"].lower())
        return text

    # Filter out unwanted data
    @staticmethod
    def process_tweet(tweet):
        d = {}
        d['tweet_date'] = tweet['created_at']
        d['hashtags'] = [hashtag['text'] for hashtag in Streamer.getHashtags(tweet)]
        text = Streamer.getText(tweet)
        text = Streamer.deEmojify(text) 
        text = text.lower().replace("\n", " ")
        d['text'] = text
        d['twitter_user'] = Streamer.deEmojify(tweet['user']['screen_name'])
        location = tweet['user']['location']
        if location:
            location = Streamer.deEmojify(location)
        d['user_loc'] = location 
        return d

    '''
    This extracts all aspects that are searched for in a tweet
    Suggested extra_fields: "id_str", "retweet_count", "favorite_count", "created_at"
    Returns a dictionary
    Credit: https://gwu-libraries.github.io/sfm-ui/posts/2016-11-10-twitter-interaction
    '''
    @staticmethod
    def summarize(tweet, extra_fields = None):
        new_tweet = {}
        for field, value in tweet.items():
            if field in ['text', 'full_text', 'screen_name', 'expanded_url', 'display_url'] and value is not None:
                if field == 'created_at':
                    new_tweet['tweet_date'] = tweet[field]
                elif field == 'text' or field == 'full_text':
                    text = tweet[field]
                    text = Streamer.deEmojify(text)
                    text = text.lower().replace('\n', ' ')
                    new_tweet[field] = text
                elif field == 'screen_name':
                    new_tweet['twitter_user'] = tweet[field]
                else:
                    new_tweet[field] = value
            
            elif extra_fields and field in extra_fields:
                new_tweet[field] = value
            
            elif field == 'hashtags' and len(value):
                for hashtag in value:
                    Streamer.summarize(hashtag)

            elif field == 'urls':
                if type(value) == list and len(value):
                    for link_dict in value:
                        new_tweet[field] = Streamer.summarize(link_dict)

            elif field in ['retweeted_status', 'quoted_status', 'user', 'extended_tweet', 'entities']:
                if value:
                    new_tweet[field] = Streamer.summarize(value)
        return new_tweet



    '''
    We can use this to inste ad "tally" the occurences of each group
    By changing to tweet[group] = 1
    '''
    @staticmethod
    def find_group(tweet, groups):
        for group, keywords in groups.items():
            found = False
            found = Streamer.find_keyword(tweet, keywords, found)
            if(found):
                return group
        return 'misc'
    
    @staticmethod
    def find_keyword(tweet, keywords, found):
        if type(tweet) == str: 
            for keyword in keywords:
                for word in keyword.split():
                    if tweet.lower().find(word) != -1:
                        found = True
                        return True
        else:
            for key, value in tweet.items():
                found = Streamer.find_keyword(value, keywords, found)
            
        return found

class Tweet:
    # TODO: Move Streamer static methods to here
    pass

if __name__ == '__main__':           
    # Save filters and output file  
    argv = sys.argv
    outfile = 'saved-tweets.csv' if len(argv) == 1 else sys.argv[1]
    samesearch = True if len(argv) == 3 else False
    creds = 'twitter-creds.json'


    # Check correct arguments were given
    if len(argv) > 3:
        print('Usage:', os.path.basename(__file__), 
              '[api-creds.json] [outfile] [continue]')
        sys.exit(1)

 
    stream = Flock(creds, outfile, samesearch)
    stream.start()  
    # stream.fetch(cont=True)
        



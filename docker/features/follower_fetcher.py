
'''
Built-in modules
'''
import pdb
import os
import traceback
import urllib.parse
import time
from datetime import datetime

'''
Initialization code
'''
def __init_program():
    print("CWD is {}".format(os.getcwd()))
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print("After change, CWD is {}".format(os.getcwd()))

__init_program()

'''
User defined modules
'''

from config.load_config import load_config
load_config()

dep_check = os.getenv("DEPENDENCY_CHECK", "False")
if dep_check.lower() == "true":
    from installer import dependency_check


from libs.twitter_errors import  TwitterRateLimitError, TwitterUserNotFoundError, TwitterUserInvalidOrExpiredToken, TwitterUserAccountLocked

from libs.twitter_access import fetch_tweet_info, get_reponse_header
from libs.twitter_logging import logger

from libs.follower_buckets_manager_client import FollowerCheckBucketManagerClient as BucketManager

class FollowerFetcher():
    """
    This class uses expert pattern. 
    It provides API to 
    """
    def __init__(self, client_id, client_screen_name, source_id, source_screen_name):
        #tested
        print("Initializing user follower")
        self.client_id = client_id
        self.client_screen_name = client_screen_name
        self.bucket_mgr = BucketManager(client_id, client_screen_name)
        self.grandtotal = 0 #Tracks the count of total friendship stored in DB
        print("User friendship init finished")
    
    def register_as_followercheck_client(self):
        #tested
        print("Registering follower check client as {} Id and {} screen.name".format(self.client_id, self.client_screen_name))
        self.bucket_mgr.register_service()
        print("Successfully registered client as {} Id and {} screen.name".format(self.client_id, self.client_screen_name))

    def unregister_client(self):
        print("Unregistering  follower check client as {} Id and {} screen.name".format(self.client_id, self.client_screen_name))
        pdb.set_trace()
        self.bucket_mgr.unregister_service()
        print("Successfully unregistered client as {} Id and {} screen.name".format(self.client_id, self.client_screen_name))

    def __process_follower_fetch(self, user):
        #print("Processing friendship fetch for {}  user".format(user))
        pdb.set_trace()
        base_url = 'https://api.twitter.com/1.1/followers/list.json'
        count = 200
        cursor = -1
        friendship = []
        users_to_import = True
        while users_to_import:
            if user['id']:
                params = {
                    'user_id': user['id'],
                    'count': count,
                    'cursor': cursor
                    }
            else:
                print("User Id is missing and so using {} screen name".format(user['screen_name']))
                params = {
                    'screen_name': user['screen_name']
                    }
            url = '%s?%s' % (base_url, urllib.parse.urlencode(params))
    
            response_json = fetch_tweet_info(url)
            #print(type(response_json))
        cursor = response_json["next_cursor"]
        if 'users' in response_json.keys():
            friendship = friendship.extend(response_json['users'])
        else:
            users_to_import = False
        
        if not friendship:
            print("No follower found for {}".format(user['screen_name']))
        return friendship

    def __check_follower_user_detail(self, users):
        print("Finding follower users for {} users".format(len(users)))
        pdb.set_trace()
        friendships = []
        count = 0
        start_time = datetime.now()
        remaining_threshold = 0
        for user in users:
            try:
                curr_limit = get_reponse_header('x-rate-limit-remaining')
                if(curr_limit and int(curr_limit) <= remaining_threshold):
                    print("Sleeping as remaining x-rate-limit-remaining is {}".format(curr_limit))
                    time_diff = (datetime.now()-start_time).seconds
                    remaining_time = (15*60) - time_diff
                    sleeptime = remaining_time + 2
                    print("sleeping for {} seconds to avoid threshold. Current time={}".format(sleeptime, datetime.now()))
                    if(sleeptime > 0):
                        time.sleep(sleeptime)
                    start_time = datetime.now()
                    print("Continuing after threshold reset")

                print("Fetching follower info for {} user".format(user))
                followers_user = self.__process_follower_fetch(user)
            except TwitterUserNotFoundError as unf:
                logger.warning("Twitter couldn't found user {} and so ignoring".format(user))
                user['followers'] = []
                self.grandtotal += 1
                continue
            count = count + 1
            user['followers'] = followers_user
        print("Processed {} out of {} users for follower Check".format(count, len(users)))
        if count != len(users):
            logger.info("Unable to fetch fetch status for {} users".format(len(users)-count))

    def __process_bucket(self, bucket):
        print("Processing bucket with ID={}".format(bucket['bucket_id']))
        pdb.set_trace()
        bucket_id = bucket['bucket_id']
        users = bucket['users']
        self.__check_follower_user_detail(users)
        return

    def findfollowerForUsersInStore(self):
        print("Finding follower for users")
        try_count = 0
        buckets_batch_cnt = 2
        while True:
            try:
                try_count = try_count + 1
                print("Retry count is {}".format(try_count))
                buckets = self.bucket_mgr.assignBuckets(bucketscount=buckets_batch_cnt)
                while buckets:
                    for bucket in buckets:
                        print("Processing {} bucket at  {}Z".format(bucket['bucket_id'], datetime.utcnow()))
                        self.__process_bucket(bucket)
                        print("Storing {} bucket user info at  {}Z".format(bucket['bucket_id'], datetime.utcnow()))
                        self.bucket_mgr.store_processed_data_for_bucket(bucket)
                    buckets = self.bucket_mgr.assignBuckets(bucketscount=buckets_batch_cnt)
                print("Not Found any bucket for processing. So waiting for more buckets to be added")
                time.sleep(60)
            except TwitterRateLimitError as e:
                logger.exception(e)
                print(traceback.format_exc())
                print(e)
                # Sleep for 15 minutes - twitter API rate limit
                print('Sleeping for 15 minutes due to quota. Current time={}'.format(datetime.now()))
                time.sleep(900)
                continue
            except TwitterUserInvalidOrExpiredToken as e:
                logger.exception(e)
                print(traceback.format_exc())
                print(e)
                print('Exiting since user credential is invalid')
                return         

            except TwitterUserAccountLocked as e:
                logger.exception(e)
                print(traceback.format_exc())
                print(e)
                print('Exiting since Account is locked')
                return       

            except Exception as e:
                logger.exception(e)
                print(traceback.format_exc())
                print(e)
                time.sleep(900)
                continue

def main():
    print("Starting follower lookup with {}/{} client. \nConfig file should be [config/{}]\n".format(os.environ["TWITTER_ID"],os.environ["TWITTER_USER"],'.env'))
    stats_tracker = {'processed': 0}
    followerFetcher = FollowerFetcher(client_id=os.environ["CLIENT_ID"], client_screen_name=os.environ["CLIENT_SCREEN_NAME"], source_id=os.environ["TWITTER_ID"], source_screen_name=os.environ["TWITTER_USER"])
    followerFetcher.register_as_followercheck_client()
    try:
        followerFetcher.findfollowerForUsersInStore()
    except Exception as e:
        pass
    finally:
        stats_tracker['processed'] = followerFetcher.grandtotal
        logger.info("[follower stats] {}".format(stats_tracker))
        print("Exiting program")

if __name__ == "__main__": main()

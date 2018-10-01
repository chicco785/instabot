# -*- coding: utf-8 -*-

from glob import glob
import os
import sys
import threading
import time
from tqdm import tqdm
import argparse
import random

sys.path.append(os.path.join(sys.path[0], '../'))
import schedule
from instabot import Bot, utils, schema, dbutils
from instabot.schema import Follower, Followed, Media
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

import config
from datetime import datetime, timezone, timedelta

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-u', type=str, help="username")
parser.add_argument('-p', type=str, help="password")
parser.add_argument('-proxy', type=str, help="proxy")
args = parser.parse_args()

bot = Bot(comments_file=config.COMMENTS_FILE,
            blacklist_file=config.BLACKLIST_FILE,
            whitelist_file=config.WHITELIST_FILE,
            followed_file=config.FOLLOWED_FILE,
            unfollowed_file=config.UNFOLLOWED_FILE,
            min_media_count_to_follow=config.MIN_MEDIA,
            skipped_file=config.SKIPPED_FILE,
            friends_file=config.FRIENDS_FILE,
            filter_business_accounts=True,
            filter_verified_accounts=False,
            filter_previously_followed=True,
            max_likes_per_day=300,
            max_unlikes_per_day=300,
            max_follows_per_day=350,
            max_unfollows_per_day=350,
            max_comments_per_day=100,
            max_blocks_per_day=100,
            max_unblocks_per_day=100,
            max_likes_to_like=100,
            min_likes_to_like=20,
            max_messages_per_day=300,
            max_followers_to_follow=7000,
            min_followers_to_follow=100,
            max_following_to_follow=7000,
            min_following_to_follow=100,
            max_followers_to_following_ratio=10,
            max_following_to_followers_ratio=50,
            max_following_to_block=5000,
            stop_words=config.STOP_WORDS,
            like_delay=30,
            unlike_delay=30,
            follow_delay=60,
            unfollow_delay=60,
            comment_delay=60,
            message_delay=120)
bot.login(username=args.u, password=args.p,
          proxy=args.proxy)
bot.logger.info("ULTIMATE script. Safe to run 24/7!")

random_user_file = utils.file(config.USERS_FILE)
random_hashtag_file = utils.file(config.HASHTAGS_FILE)
photo_captions_file = utils.file(config.PHOTO_CAPTIONS_FILE)
posted_pic_list = utils.file(config.POSTED_PICS_FILE).list

pics = sorted([os.path.basename(x) for x in
               glob(config.PICS_PATH + "/*.jpg")])

locked = False

schema.initialisedb(dbpath=config.DB)

engine = create_engine(config.DB, echo=False, poolclass=SingletonThreadPool)
Session = sessionmaker(bind=engine)

followers = dbutils.follower(verbose=False)

followings = dbutils.following(verbose=False)

media = dbutils.media(verbose=False)


def lock():
    global locked
    while (locked == True):
        time.sleep(10)
    locked = True

def unlock():
    global locked
    locked = False

def stats():
    bot.save_user_stats(bot.user_id,config.STATS_FILE)


def like_medias(medias):
    try:
        session = Session()
        if not medias:
            bot.logger.info("Nothing to like.")
        bot.logger.info("Going to like %d medias." % (len(medias)))
        for m in tqdm(medias):
            if not bot.like(m):
                bot.error_delay()
            else:
                media.append(session, Media(id=m))
                session.commit()
    except Exception as e:
        bot.logger.error("Couldn't like medias")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def like_hashtags():
    bot.logger.info("like_hashtags")
    amount = random.randint(20,35)
    hashtag = random_hashtag_file.random()
    media_to_like = set(bot.get_total_hashtag_medias(hashtag, amount))
    media_to_like = media_to_like - set(media.getBlacklisted(Session()))
    lock()
    like_medias(list(media_to_like))
    unlock()

def like_timeline():
    bot.logger.info("like_timeline")
    amount = random.randint(40,70)
    media_to_like = set(bot.get_timeline_medias()[:amount])
    media_to_like = media_to_like - set(media.getBlacklisted(Session()))
    lock()
    like_medias(list(media_to_like))
    unlock()

def like_followers(user_id, nlikes=None, nfollows=None):
    follower_ids = bot.get_user_followers(user_id, nfollows)
    if not follower_ids:
        bot.logger.info("%s not found / closed / has no followers." % user_id)
    else:
        media_to_like = set(bot.get_user_medias(user_id, filtration=True))
        media_to_like = media_to_like - set(media.getBlacklisted(Session()))
        if not media_to_like:
            bot.logger.info(
                "None medias received: account is closed or medias have been filtered.")
            return False
        lock()
        like_medias(list(media_to_like)[:nlikes])
        unlock()

def like_followers_from_random_user_file():
    bot.logger.info("like_followers_from_random_user_file")
    nlikes = random.randint(2,5)
    like_followers(user_id=random_user_file.random(), nlikes=nlikes, nfollows=config.NUMBER_OF_FOLLOWERS_TO_FOLLOW)


def follow_followers():
    try:
        lock()
        session = Session()
        updateFollowers()
        updateFollowings()
        current_followers = followers.set(session)
        current_followings = followings.set(session)
        bot.logger.info("follow_followers")
        bot.logger.info('Amount of valid followers is {count}'.format(
            count=len(current_followers)
        ))

        bot.logger.info('Amount of valid followings is {count}'.format(
            count=len(current_followings)
        ))
        bot.logger.info('Difference is {count}'.format(
            count=(len(current_followers)-len(current_followings))
        ))
        if (len(current_followers) - 100) > len(current_followings):
            bot.follow_followers(random_user_file.random(), nfollows=config.NUMBER_OF_FOLLOWERS_TO_FOLLOW)
            bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't follow_followers")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def comment_medias():
    bot.logger.info("comment_medias")
    bot.comment_medias(bot.get_timeline_medias())

def follow_users_from_hastag_file():
    try:
        lock()
        session = Session()
        updateFollowers()
        updateFollowings()
        current_followers = followers.set(session)
        current_followings = followings.set(session)
        if (len(current_followers) - 100) > len(current_followings):
            bot.logger.info("follow_users_from_hastag_file")
            to_follow = bot.get_hashtag_users(random_hashtag_file.random())
            to_follow = list(set(to_follow) - set(bot.blacklist))
            to_follow = list(set(to_follow) - followings.set(session)) 
            bot.follow_users(to_follow)
            bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't follow_followers")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def comment_hashtag():
    hashtag = random_hashtag_file.random()
    bot.logger.info("Commenting on hashtag: " + hashtag)
    bot.comment_hashtag(hashtag)

def upload_pictures():  # Automatically post a pic in 'pics' folder
    try:
        for pic in pics:
            if pic in posted_pic_list:
                continue

            caption = photo_captions_file.random()
            full_caption = caption + "\n" + config.FOLLOW_MESSAGE
            bot.logger.info("Uploading pic with caption: " + caption)
            bot.upload_photo(config.PICS_PATH + pic, caption=full_caption)
            if bot.api.last_response.status_code != 200:
                bot.logger.error("Something went wrong, read the following ->\n")
                bot.logger.error(bot.api.last_response)
                break

            if pic not in posted_pic_list:
                # After posting a pic, comment it with all the hashtags specified
                # In config.PICS_HASHTAGS
                posted_pic_list.append(pic)
                with open('pics.txt', 'a') as f:
                    f.write(pic + "\n")
                bot.logger.info("Succesfully uploaded: " + pic)
                bot.logger.info("Commenting uploaded photo with hashtags...")
                medias = bot.get_your_medias()
                last_photo = medias[0]  # Get the last photo posted
                bot.comment(last_photo, config.PICS_HASHTAGS)
                break
    except Exception as e:
        bot.logger.error("Couldn't upload pic")
        bot.logger.error(str(e))


def update_blacklist():  # put non followers on blacklist
    try:
        lock()
        session = Session()
        bot.logger.info("update blacklist file")
        blacklisted_followings = followings.getBlacklisted(session)
        for user_id in blacklisted_followings:
            bot.blacklist_file.append(user_id, allow_duplicates=False)
        blacklisted_followers = followers.getBlacklisted(session)
        for user_id in blacklisted_followers:
            bot.blacklist_file.append(user_id, allow_duplicates=False)
        bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't update blacklist")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def notify_followers():  # notify new followers
    try:
        lock()
        bot.logger.info("Notifying new followers")
        # Check on existed file with notified users
        updateFollowers()

        session = Session()
        all_followers = followers.list(session)

        new_followers = set(all_followers) - set(followers.getNotified(session))

        if not new_followers:
            bot.logger.info('New followers not found')
            return

        bot.logger.info('Found new followers. Count: {count}'.format(
            count=len(new_followers)
        ))

        for follower in tqdm(list(new_followers)):
            if bot.send_message(config.NEW_FOLLOWER_MESSAGE, str(follower)):
                followers.notify(session, follower)
                session.commit()
        bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't notify new followers")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def followback(nunfollows=25):  # followback new followers
    try:
        lock()
        bot.logger.info("followback new followers")
        # Check on existed file with notified users
        updateFollowers()
        updateFollowings()

        session = Session()
       
        bot.logger.info('Amount of valid followers is {count}'.format(
            count=len(followers.set(session))
        ))

        bot.logger.info('Amount of valid followings is {count}'.format(
            count=len(followings.set(session))
        ))

        recent_followers = set(followers.newerThan(session,hours=24))
        current_followings = set(followings.listAll(session))
        candidates = recent_followers - current_followings

        if not candidates:
            bot.logger.info('New followers not found')
            return

        bot.logger.info('Found new followers. Count: {count}'.format(
            count=len(candidates)
        ))

        if len(candidates) > nunfollows:
            to_followback = random.sample(candidates, nunfollows)
        else:
            to_followback = candidates

        for f in tqdm(list(to_followback)):
            try:
                print()
                bot.logger.info('Registering new follower: {follower}'.format(
                    follower=str(f)
                ))
                if bot.follow(str(f)):
                    bot.logger.info('Update db')
                    if (bot.check_user(str(f))):
                        followings.append(session, Followed(id=f, blacklist=False))
                        session.commit()
                        bot.logger.info('Mute follower: {follower}'.format(
                            follower=str(f)
                        ))
                        bot.mute_user(str(f))
                    else:
                        if not followings.update(session, Followed(id=f, blacklist=True)):
                            followings.append(session, Followed(id=f, blacklist=True))
                    # if not bot.get_user_info(str(f))["is_private"]:
                    #     nlikes = random.randint(2,5)
                    #     bot.logger.info('Like media for follower: {follower}'.format(
                    #         follower=str(f)
                    #     ))
                    #     media_to_like = set(bot.get_user_medias(str(f), filtration=True))
                    #     media_to_like = media_to_like - set(media.getBlacklisted(session))
                    #     if not media_to_like:
                    #         bot.logger.info(
                    #             "No media received: account is closed or medias have been filtered.")
                    #     else:
                    #         like_medias(list(media_to_like)[:nlikes])
                else:
                    bot.logger.info(
                        "follow {follower} failed".format(
                            follower=str(f)
                        ))
            except Exception as e:
                bot.logger.error("Couldn't follow back {follower}".format(
                    follower=str(f)
                ))
                bot.logger.error(str(e))
                if session:
                    session.rollback()
        bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't follow back new followers")
        bot.logger.error(e)
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def updateFollowers():
    try:
        session = Session()
        current_followers = set(map(int,bot.followers))
        lost_followers = followers.set(session) - current_followers
        bot.logger.info('Amount of lost followers is {count}'.format(
            count=len(lost_followers)
        ))

        new_followers = current_followers - followers.set(session)
        bot.logger.info('Amount of new followers is {count}'.format(
            count=len(new_followers)
        ))

        bot.logger.info('Amount of followers is {count}'.format(
            count=len(current_followers)
        ))

        followers.save_list(session, list(new_followers), blacklisted = False)
        followers.save_list(session, list(lost_followers), blacklisted = True)
        session.commit()
    except Exception as e:
        bot.logger.error("Couldn't update followers")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def updateFollowings():
    try:
        session = Session()
        current_following = set(map(int,bot.following))
        unfollowing = followings.set(session) - current_following
        bot.logger.info('Amount of following is {count}'.format(
            count=len(current_following)
        ))
        bot.logger.info('Amount of recent unfollowing is {count}'.format(
            count=len(unfollowing)
        ))
        new_following = current_following - followings.set(session)
        followings.save_list(session, list(new_following), blacklisted = False)
        followings.save_list(session, list(unfollowing), blacklisted = True)
        skipped = set(map(int,bot.skipped_file.set))
        followings.save_list(session, list(skipped), blacklisted = True)
        session.commit()
    except Exception as e:
        bot.logger.error("Couldn't update following")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def unfollow(nunfollows=100):  # unfollow followed users
    try:
        lock()
        bot.logger.info("cleanup followed users")
        # Check on existed file with notified users
        updateFollowers()
        updateFollowings()
        session = Session()
        current_followers = followers.set(session)

        bot.logger.info('Amount of valid followers is {count}'.format(
            count=len(current_followers)
        ))
        bot.logger.info('Amount of valid followings is {count}'.format(
            count=len(followings.set(session))
        ))

        friends = set()
        for i in bot.friends_file.set:
            friends.add(bot.convert_to_user_id(i))

        bot.logger.info('Amount of friends is {count}'.format(
            count=len(friends)
        ))

        old_followings = set(followings.olderThan(session, hours = 72))

        bot.logger.info('Amount of old followings is {count}'.format(
            count=len(old_followings)
        ))

        candidates = old_followings - (current_followers.union(friends))

        candidates = candidates - set(bot.whitelist)

        if not candidates:
            bot.logger.info('No candidate')
            return

        if len(candidates) > nunfollows:
            to_unfollow = random.sample(candidates, nunfollows)
        else:
            to_unfollow = candidates

        bot.logger.info("number of candidates to unfollow:  {count}".format(
            count=len(candidates)
        ))

        bot.logger.info("number of selected followers to remove:  {count}".format(
            count=len(to_unfollow)
        ))

        bot.unfollow_users(to_unfollow)
        bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't cleanup followers")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def unlike():  # unfollow followed users
    try:
        lock()
        session = Session()
        bot.logger.info("cleanup liked media")

        bot.logger.info('Amount of auto like media is {count}'.format(
            count=len(media.set(session))
        ))

        candidates = set(media.olderThan(session, hours = 24))

        if not candidates:
            bot.logger.info('No candidate')
            return

        print("number of media to unlike:  {count}".format(
            count=len(candidates)
        ))

        bot.unlike_medias(list(candidates))

        media.save_list(session, list(candidates), blacklisted = True)
        session.commit()
        bot.logger.info("Done.")
    except Exception as e:
        bot.logger.error("Couldn't unlike old media")
        bot.logger.error(str(e))
        if session:
            session.rollback()
    finally:
        unlock()
        if session:
            session.close()
        else:
            sys.exit("unexpected error");

def delete_old_threads():
    try:
        messages = bot.get_messages()['inbox']['threads']
        now = datetime.now(timezone.utc)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc) # use POSIX epoch
        posix_timestamp_micros = (now - epoch) // timedelta(microseconds=1)
        posix_timestamp_millis = posix_timestamp_micros // 1000 # or `/ 1e3` for float
        print(posix_timestamp_micros)
        print(posix_timestamp_millis)
        for message in tqdm(messages):
            age = message['last_activity_at'] 
            print(age)
    except Exception as e:
        bot.logger.error("Couldn't delete old threads")
        bot.logger.error(str(e))

def run_threaded(job_fn):
    job_thread = threading.Thread(target=job_fn)
    job_thread.start()


schedule.every(1).hour.do(run_threaded, stats)
#TEST
#schedule.every(1).to(2).minutes.do(run_threaded, notify_followers)
#schedule.every(1).to(2).minutes.do(run_threaded, followback)
#schedule.every(27).to(39).minutes.do(run_threaded, like_hashtags)
#schedule.every(12).to(25).minutes.do(run_threaded, like_timeline)
#schedule.every(40).to(50).minutes.do(run_threaded, like_followers_from_random_user_file)
#schedule.every(50).to(70).minutes.do(run_threaded, follow_followers)
#schedule.every(1).to(2).minutes.do(run_threaded, unfollow)
#schedule.every(50).to(70).minutes.do(run_threaded, unlike)
#schedule.every(16).hours.do(run_threaded, comment_medias)
#schedule.every(2).to(3).hours.do(run_threaded, follow_users_from_hastag_file)
#schedule.every(1).days.at("07:50").do(run_threaded, update_blacklist)

#actual schedule
schedule.every(5).to(25).minutes.do(run_threaded, follow_followers)
schedule.every(10).to(15).minutes.do(run_threaded, notify_followers)
schedule.every(15).to(20).minutes.do(run_threaded, followback)
schedule.every(7).to(20).minutes.do(run_threaded, like_timeline)
schedule.every(1).to(2).hours.do(run_threaded, like_hashtags)
schedule.every(2).to(3).hours.do(run_threaded, like_followers_from_random_user_file)
schedule.every(4).to(6).hours.do(run_threaded, unlike)
schedule.every(4).to(6).hours.do(run_threaded, unfollow)
schedule.every(2).to(3).hours.do(run_threaded, follow_users_from_hastag_file)
schedule.every(1).days.at("07:50").do(run_threaded, update_blacklist)
# NOT USED
#schedule.every(16).hours.do(run_threaded, comment_medias)
#schedule.every(6).hours.do(run_threaded, comment_hashtag)
#schedule.every(1).days.at("21:28").do(run_threaded, upload_pictures)

updateFollowers()
updateFollowings()
unfollow()

while True:
    schedule.run_pending()
    time.sleep(1)

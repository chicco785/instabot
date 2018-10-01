from .schema import Follower, Followed, Media
from datetime import datetime, timezone, timedelta
from huepy import bold, green, orange

class follower(object):

    def __init__(self, verbose=True):
        self.verbose = verbose

    def listAll(self, session):
        followers = session.query(Follower).all()
        return [x for x in followers if x]

    def list(self, session):
        followers = session.query(Follower).filter(Follower.blacklist == False)
        return [x.id for x in followers if x]

    def set(self, session):
        return set(self.list(session))

    def getBlacklisted(self, session):
        followers = session.query(Follower).filter(Follower.blacklist == True)
        return [x.id for x in followers if x]

    def getNotified(self, session):
        followers = session.query(Follower).filter(Follower.notified == True)
        return [x.id for x in followers if x]

    def olderThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Follower).filter(Follower.created_at < (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Follower.blacklist == False)
        return [x.id for x in followers if x]

    def newerThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Follower).filter(Follower.created_at > (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Follower.blacklist == False)
        return [x.id for x in followers if x]

    def append(self, session, item):
        if self.verbose:
            msg = "Adding '{}' to `{}`.".format(item.id, 'followers')
            print(bold(green(msg)))
        session.add(item)

    def get(self, session, id):
        return session.query(Follower).filter(Follower.id == id).first()

    def getUsername(self, session, id):
        return session.query(Follower).filter(Follower.username == id).first()

    def remove(self, session, id):
        if self.verbose:
            msg = "Removing '{}' to `{}`.".format(id, 'followers')
            print(bold(green(msg)))
        to_remove = session.query(Follower).filter(Follower.id == id).first()
        if to_remove:
            session.delete(to_remove)
            return True
        return False

    def update(self, session, item):
        to_update = session.query(Follower).filter(Follower.id == item.id).first()
        if to_update:
            if item.username: to_update.username = item.username
            if item.notified: to_update.notified = item.notified
            if item.blacklist: to_update.blacklist = item.blacklist
            return True
        return False

    def blacklist(self, session, id):
        return self.update(session,Follower(id=id,blacklist=True))

    def notify(self, session, id):
        return self.update(session,Follower(id=id,notified=True))

    def notified(self, session, id):
            if session.query(Follower).filter(Follower.id == id).filter(Follower.notified == True).first():
                return True
            else:
                return False
    
    def blacklisted(self, session, id):
        if session.query(Follower).filter(Follower.id == id).filter(Follower.blacklist == True).first():
            return True
        else:
            return False

    def random(self, session):
        return random.choice(self.list(session))

    def save_list(self, session, items, blacklisted=False, notified=False):
        for i in items:
            x = str(i)
            if self.get(session,x):
                if blacklisted: self.blacklist(session,x)
                if notified: self.notify(session,x)
            else:
                session.add(Follower(id=x,notified=notified,blacklist=blacklisted))

    def clear(self, session):
        session.query(Follower).delete()

class following(object):

    def __init__(self, verbose=True):
        self.verbose = verbose

    def listAll(self, session):
        followers = session.query(Followed).all()
        return [x for x in followers if x]

    def list(self, session):
        followers = session.query(Followed).filter(Followed.blacklist == False)
        return [x.id for x in followers if x]

    def getBlacklisted(self, session):
        followers = session.query(Followed).filter(Followed.blacklist == True)
        return [x.id for x in followers if x]

    def olderThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Followed).filter(Followed.created_at < (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Followed.blacklist == False)
        return [x.id for x in followers if x]

    def newerThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Followed).filter(Followed.created_at > (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Followed.blacklist == False)
        return [x.id for x in followers if x]

    def set(self, session):
        return set(self.list(session))

    def append(self, session, item):
        if self.verbose:
            msg = "Adding '{}' to `{}`.".format(item.id, 'followed')
            print(bold(green(msg)))
        session.add(item)

    def get(self, session, id):
        return session.query(Followed).filter(Followed.id == id).first()

    def getUsername(self, session, id):
        return session.query(Followed).filter(Followed.username == id).first()

    def remove(self, session, id):
        if self.verbose:
            msg = "Removing '{}' to `{}`.".format(id, 'followed')
            print(bold(green(msg)))
        to_remove = session.query(Followed).filter(Followed.id == id).first()
        if to_remove:
            session.delete(to_remove)
            return True
        return False

    def update(self, session, item):
        to_update = session.query(Followed).filter(Followed.id == item.id).first()
        if to_update:
            if item.username: to_update.username = item.username
            if item.blacklist: to_update.blacklist = item.blacklist
            return True
        return False

    def blacklist(self, session, id):
        return self.update(session,Followed(id=id,blacklist=True))

    def blacklisted(self, session, id):
        if session.query(Followed).filter(Followed.id == id).filter(Followed.blacklist == True).first():
            return True
        else:
            return False

    def random(self, session):
        return random.choice(self.list(session))

    def save_list(self, session, items, blacklisted=False):
        for i in items:
            x = str(i)
            if self.get(session, x):
                if blacklisted: self.blacklist(session, x)
            else:
                session.add(Followed(id=x,blacklist=blacklisted))

    def clear(self, session):
        session.query(Followed).delete()

class media(object):

    def __init__(self, verbose=True):
        self.verbose = verbose

    def listAll(self, session):
        followers = session.query(Media).all()
        return [x for x in followers if x]

    def list(self, session):
        followers = session.query(Media).filter(Media.blacklist == False)
        return [x.id for x in followers if x]

    def getBlacklisted(self, session):
        followers = session.query(Media).filter(Media.blacklist == True)
        return [x.id for x in followers if x]

    def olderThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Media).filter(Media.created_at < (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Media.blacklist == False)
        return [x.id for x in followers if x]

    def newerThan(self, session, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        followers = session.query(Media).filter(Media.created_at > (datetime.utcnow() - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks))).filter(Media.blacklist == False)
        return [x.id for x in followers if x]

    def set(self, session):
        return set(self.list(session))

    def append(self, session, item):
        if self.verbose:
            msg = "Adding '{}' to `{}`.".format(item.id, 'followed')
            print(bold(green(msg)))
        session.add(item)

    def get(self, session, id):
        return session.query(Media).filter(Media.id == id).first()

    def getUsername(self, session, id):
        return session.query(Media).filter(Media.username == id).first()

    def remove(self, session, id):
        if self.verbose:
            msg = "Removing '{}' to `{}`.".format(id, 'media')
            print(bold(green(msg)))
        to_remove = session.query(Media).filter(Media.id == id).first()
        if to_remove:
            session.delete(to_remove)
            return True
        return False

    def update(self, session, item):
        to_update = session.query(Media).filter(Media.id == item.id).first()
        if to_update:
            if item.username: to_update.username = item.username
            if item.blacklist: to_update.blacklist = item.blacklist
            return True
        return False

    def blacklist(self, session, id):
        return self.update(session,Followed(id=id,blacklist=True))

    def blacklisted(self, session, id):
        if session.query(Media).filter(Media.id == id).filter(Media.blacklist == True).first():
            return True
        else:
            return False

    def save_list(self, session, items, blacklisted=False):
        for i in items:
            x = str(i)
            if self.get(session, x):
                if blacklisted: self.blacklist(session, x)
            else:
                session.add(Media(id=x,blacklist=blacklisted))

    def random(self, session):
        return random.choice(self.list(session))

    def clear(self, session):
        session.query(Media).delete()
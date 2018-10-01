from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean
from sqlalchemy  import create_engine

class Follower(Base):

    __tablename__ = 'followers'

    id          =   Column(Integer, primary_key=True, nullable=False)
    username    =   Column(String(36), unique=True, nullable=True)
    created_at  =   Column(DateTime, default=datetime.utcnow)
    blacklist   =   Column(Boolean, default=False)
    notified    =   Column(Boolean, default=False)

    def __repr__(self):
        str_created_at = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "<Follower (id='%d', username=%s, created_at=%s, blacklist=%s, notified=%s )>" % (self.id, self.username, str_created_at, self.blacklist, self.notified)

class Followed(Base):

    __tablename__ = 'followings'

    id          =   Column(Integer, primary_key=True, nullable=False)
    username    =   Column(String(36), unique=True, nullable=True)
    created_at  =   Column(DateTime, default=datetime.utcnow)
    blacklist   =   Column(Boolean, default=False)

    def __repr__(self):
        str_created_at = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "<Followed (id='%d', username=%s, created_at=%s, blacklist=%s, notified=%s )>" % (self.id, self.username, str_created_at, self.blacklist)

class Media(Base):

    __tablename__ = 'medias'

    id          =   Column(Integer, primary_key=True, nullable=False)
    username    =   Column(String(36), unique=True, nullable=True)
    created_at  =   Column(DateTime, default=datetime.utcnow)
    blacklist   =   Column(Boolean, default=False)

    def __repr__(self):
        str_created_at = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "<Media (id='%d', username=%s, created_at=%s, blacklist=%s, notified=%s )>" % (self.id, self.username, str_created_at, self.blacklist)

def initialisedb(dbpath='sqlite:///sqlalchemy_example.db'):
    # Create an engine that stores data in the local directory's
    # sqlalchemy_example.db file.
    engine = create_engine(dbpath)
     
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    Base.metadata.create_all(engine)
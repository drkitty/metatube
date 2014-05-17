from sqlalchemy import (create_engine, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import settings


engine = create_engine('mysql+oursql://metatube@localhost/metatubedb',
                       echo=settings.debug)

Base = declarative_base()

Session = sessionmaker(bind=engine)


class Video(Base):
    __tablename__ = 'video'

    id = Column(String(16), primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    data_published = Column(DateTime)


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(String(40), primary_key=True)
    title = Column(String(60))
    description = Column(Text)


class PlaylistVideo(Base):
    __tablename__ = 'playlistvideo'

    video = Column(String(16), ForeignKey('video.id'), primary_key=True)
    playlist = Column(String(40), ForeignKey('playlist.id'), primary_key=True)
    position = Column(Integer)

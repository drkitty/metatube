from sqlalchemy import create_engine, Column, Integer, String, Text
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

class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(String(40), primary_key=True)
    title = Column(String(60))
    description = Column(Text)

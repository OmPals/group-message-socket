import pymongo
from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_DB_CONNECTION)
db = client.chat_db
chats = db.default_room_chat
FEED_SIZE = 25


def add_chat_message(chat_obj):
    chat_id = chats.insert_one(chat_obj).inserted_id
    return chat_id


def get_feed():
    return chats.find().sort('created_at', pymongo.DESCENDING).limit(FEED_SIZE)

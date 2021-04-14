from pymongo import MongoClient
import config


class Connect(object):
    @staticmethod
    def get_connection():
        return MongoClient(f"mongodb+srv://{config.USERNAME}:{config.PASSWORD}@cluster0.jxstd.mongodb.net/{config.DB_NAME}?retryWrites=true&w=majority")
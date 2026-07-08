import pymongo

mongo_uri = "mongodb+srv://stockuser:T6SxVfhCWTvKjOfN@cluster0.blype8i.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_uri)

try:
    client.admin.command("ping")
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:", e)
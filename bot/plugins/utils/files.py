import json
import os
from bot import config, app

async def download_db():
    storage_channel = config["storage_channel_id"]
    database_message = config["database_message_id"]

    message = await app.get_messages(storage_channel, database_message)
    await app.download_media(message,"./db.json")

    with open("db.json", "r") as file:
        db = json.load(file)

    os.remove("db.json")
    return db
import json
import os
from datetime import datetime
from bot import config, app
from .files import download_db
from .parser import parse_date

from pyrogram.types import Message ,InputMediaDocument

async def create_question(msg: Message, score: int, content: str):
    storage_channel = config["storage_channel_id"]
    file_name = f"question-{msg.message_id}.json"

    question = {
        "chat_id": msg.chat.id,
        "msg_id": msg.message_id,
        "is_closed": False,
        "score": score,
        "content": content,
        "answers": []
    }
    question = json.dumps(question, indent=4)

    with open(file_name, "w") as file:
        file.write(question)

    message = await app.send_document(storage_channel, file_name)
    os.remove(file_name)

    await add_question(msg, message.message_id)

async def add_question(msg: Message, file_id: int):
    storage_channel = config["storage_channel_id"]
    database_message = config["database_message_id"]

    question = {
        "chat_id": msg.chat.id,
        "msg_id": msg.message_id,
        "file_id": file_id
    }

    db = await download_db()

    with open("db.json", "w+") as f:
        db["questions"].append(question)
        json.dump(db, f)

    await app.edit_message_media(storage_channel, database_message, InputMediaDocument("db.json"))
    os.remove("db.json")

async def get_question(question_id: int) -> str:
    storage_channel = config["storage_channel_id"]
    q = None

    db = await download_db()
    if any(filter(lambda x: question_id not in x.values(), db["questions"])):
        for question in db["questions"]:
            if question["msg_id"] == question_id:
                q = question
                break
    else:
        return None
    
    message = await app.get_messages(storage_channel, q["file_id"])
    file_name = message.document.file_name
    await app.download_media(message, f"./{file_name}")

    with open(file_name, "r") as file:
        q = json.load(file)

    os.remove(file_name)
    return q

async def answer_question(question_id, msg):
    storage_channel = config["storage_channel_id"]

    date = datetime.now()
    date = parse_date(date)
    answer = {
        "user_id": msg.from_user.id,
        "date": date,
        "score": 0,
        "answer": msg.text
    }

    db = await download_db()
    for question in db["questions"]:
        if question["msg_id"] == question_id:
            file_id = question["file_id"]

    msg_file = await app.get_messages(storage_channel, file_id)
    file_name = msg_file.document.file_name

    await app.download_media(msg_file, f"./{file_name}")

    with open(file_name, "r") as file:
        db = json.load(file)

        with open(file_name, "w") as f:
            db["answers"].append(answer)
            json.dump(db, f)
    
    await app.edit_message_media(storage_channel, file_id, InputMediaDocument(file_name))
    os.remove(file_name)

async def change_score(question_id: int, user_id: int, score: int):
    storage_channel = config["storage_channel_id"]

    question = await get_question(question_id)
    if not question:
        return None

    db = await download_db()
    for q in db["questions"]:
        if q["msg_id"] == question_id:
            file_id = q["file_id"]

    msg_file = await app.get_messages(storage_channel, file_id)
    file_name = msg_file.document.file_name

    await app.download_media(msg_file, f"./{file_name}")

    with open(file_name, "r") as file:
        q = json.load(file)
        answers = q["answers"]

        for answer in answers:
            if answer["user_id"] == user_id:
                answer["score"] = score
                res = score
                break
            else:
                res = None

        with open(file_name, "w") as f:
            json.dump(q, f)
    
    if res:
        await app.edit_message_media(storage_channel, file_id, InputMediaDocument(file_name))
        os.remove(file_name)
    else:
        os.remove(file_name)
        raise Exception("Cannot find user.")

async def get_scores(question_id: int) -> list:
    storage_channel = config["storage_channel_id"]
    scores = []

    question = await get_question(question_id)
    if not question:
        return None

    db = await download_db()
    for q in db["questions"]:
        if q["msg_id"] == question_id:
            file_id = q["file_id"]

    msg_file = await app.get_messages(storage_channel, file_id)
    file_name = msg_file.document.file_name

    await app.download_media(msg_file, f"./{file_name}")

    with open(file_name, "r") as file:
        db = json.load(file)
        
        for answer in db["answers"]:
            scores.append((answer["user_id"], answer["score"]))

    os.remove(file_name)
    return scores

async def close_question(question_id: int):
    storage_channel = config["storage_channel_id"]

    question = await get_question(question_id)
    if not question:
        raise Exception("Question not found!")
        return

    db = await download_db()
    for q in db["questions"]:
        if q["msg_id"] == question_id:
            file_id = q["file_id"]

    msg_file = await app.get_messages(storage_channel, file_id)
    file_name = msg_file.document.file_name

    await app.download_media(msg_file, f"./{file_name}")

    with open(file_name, "r") as file:
        db = json.load(file)
        db["is_closed"] = True

        with open(file_name, "w") as f:
            json.dump(db, f)

    await app.edit_message_media(storage_channel, file_id, InputMediaDocument(file_name))
    os.remove(file_name)
import json
import os

from pyrogram import Client

START_TEXT = "Hi! I'm a bot that help you study more efficient."

CHECKED_TEXT =  "(Checked)"

HELP_TEXT = """<b>Help for commands:</b>
/start or /alive: Check if the bot is alive.
/help: Get this message.

<b>Admins Commands:</b>
/question [score] [content]: Assign questions to students.
/check [reply to question message]: PM teacher with students' answers to check (close the question before running).
/scores|revealscores [reply to question message]: Reveal students' score in a group.
/close [reply to question message]: Close a question."""

with open("config.json") as file:
    config = json.load(file)

app = Client(
    "ClassroomBot",
    api_id=config["api_id"],
    api_hash=config["api_hash"],
    bot_token=config["bot_token"],
    plugins={'root': os.path.join(__package__, 'plugins')},
    parse_mode="html"
)
from bot import app, HELP_TEXT, START_TEXT
from .utils.parser import parse_args
from .utils.storage import get_question

from pyrogram import filters
from pyrogram.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton

question_answering_data = []

@app.on_message(filters.incoming & filters.text & filters.command(["start", "alive"], "/"))
async def start(client, msg):
    me = await client.get_me()
    args = parse_args(msg)

    if args:
        if args[0] == "help":
            if msg.chat.type != "private":
                await msg.reply_text(
                    "Please contact me in PM to get help.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("PM help", url=f"t.me/{me.username}?start=help")]
                        ]
                    )
                )
                return
            await msg.reply_text(HELP_TEXT)
        elif args[0].startswith("question-"):
            question_id = int(args[0][9:])

            question = await get_question(question_id)
            if not question:
                await msg.reply_text("Question not found!")
                return

            else:
                text = "<b><u>Answering</u></b>\n"
                text += f"Score: {question['score']}\n"
                text += f"Content: {question['content']}"
                message = await msg.reply_text(
                    text,
                    reply_markup=ForceReply()
                )

                question_answering_data.append(
                    {
                        "question_id": question_id,
                        "user_id": msg.from_user.id,
                        "msg_id": message.message_id
                    }
                )
    else:
        await msg.reply_text(START_TEXT)
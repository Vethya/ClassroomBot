from bot import app, HELP_TEXT

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.incoming & filters.text & filters.command("help", "/"))
async def help(client, msg):
    me = await client.get_me()

    if msg.chat.type == "private":
        await msg.reply_text(HELP_TEXT)
    else:
        await msg.reply_text(
            "Please contact me in PM to get help.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("PM help", url=f"t.me/{me.username}?start=help")]
                ]
            )
        )
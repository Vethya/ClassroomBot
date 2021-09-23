from pyrogram.types import Message

def parse_args(msg: Message):
    text = msg.text
    return text.split()[1:]

def parse_date(date):
    return date.strftime("%d/%m/%Y %I:%M%p")
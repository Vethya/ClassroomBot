from bot import app, CHECKED_TEXT
from .utils.parser import parse_args
from .utils.permissions import is_admin
from .utils.storage import change_score, close_question, create_question, answer_question, get_question, get_scores
from .start import question_answering_data

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.incoming & filters.text & filters.group & filters.command("question", "/"))
async def question(client, msg):
    reply = await msg.reply_text("Creating Question...")

    me = await client.get_me()
    args = parse_args(msg)

    if not await is_admin(msg.chat.id, msg.from_user.id):
        await reply.edit_text("Only teachers (admins) can run this command.")
        return
    else:
        if len(args) < 1:
            await reply.edit_text("Sccore and Content is <b>required</b>.")
            return
        elif len(args) < 2:
            await reply.edit_text("Content is <b>required</b>.")
            return
        
        try:
            score = int(args[0])
        except ValueError:
            await reply.edit_text("Score <b>must</b> be a number.")
            return
        
        if score < 0:
            await reply.edit_text("Score must be bigger than 0.")
            return
        
        if len(args[1:]) < 2:
            content = args[1]
        else:
            content = " ".join(args[1:])

        text = "<b>Question</b>\n"
        text += f"ID: <code>{reply.message_id}</code>\n"
        text += f"Score: <b>{score}</b>\n"
        text += f"Content: \n{content}"
        
        await create_question(reply, score, content)

        await reply.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Answer", url=f"t.me/{me.username}?start=question-{reply.message_id}")]
                ]
            )
        )

@app.on_message(filters.incoming & filters.text & filters.private, group=-1)
async def answer(_, msg):
    reply_msg = msg.reply_to_message
    user = msg.from_user

    if reply_msg:
        for question in question_answering_data:
            if reply_msg.message_id == question["msg_id"]:
                reply = await msg.reply_text("Processing...")
                q = await get_question(question["question_id"])
                if not q:
                    await reply.edit_text("Question not found!")
                    return

                if q["is_closed"]:
                    await reply.edit_text("Failed to submit answer. This question was <b>closed</b>.")
                    return
                
                if await is_admin(q["chat_id"], user.id):
                    await reply.edit_text("Teachers (admins) <b>can not</b> answer questions.")
                    return
                
                for answer in q["answers"]:
                    if answer["user_id"] == msg.from_user.id:
                        await reply.edit_text("You have answered this question already.")
                        return
                await answer_question(question["question_id"], msg)

                await reply.edit_text("Answer submitted")

@app.on_message(filters.incoming & filters.text & filters.group & filters.command("check", "/"))
async def check(client, msg):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await msg.reply_text("Only teachers (admins) can run this command.")
        return
    
    reply_msg = msg.reply_to_message
    if not reply_msg:
        await msg.reply_text("Please reply to a question message to reveal students' score for it.")
        return

    question = await get_question(reply_msg.message_id)
    if not question:
        await msg.reply_text("Question not found. Make sure you are replying to a question message.")
        return
    
    if not question["is_closed"]:
        await msg.reply_text("Question is not closed. Please close the question before running this command.")
        return
    
    text = "<b>Checking</b>\n"
    text += f"Question:\n{question['content']}\n"
    text += f"ID: {question['msg_id']}\n"
    text += f"Total Score: {question['score']}\n"
    text += f"Answers: {len(question['answers'])}"
    
    await client.send_message(
        msg.from_user.id,
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Reveal Answers", callback_data=f"reveal_answer-{question['msg_id']}")]
            ]
        )
    )

    await msg.reply_text("The information was sent into your PM.")

reveal_answers_data = []

@app.on_callback_query()
async def reveal_answers(client, callback):
    data = callback.data
    chat = callback.message.chat

    if data.startswith("reveal_answer-"):
        question_id = int(data[14:])
        question = await get_question(question_id)

        if not question:
            await client.send_message(
                chat.id,
                "Question Not found."
            )
            return
        
        await callback.answer()
        await callback.edit_message_reply_markup()
        answers = question["answers"]

        for answer in answers:
            user = await client.get_users(answer["user_id"])
            name = user.first_name if user.first_name else "" + " " + user.last_name if user.last_name else ""

            text = "<b>Answer</b>\n"
            text += f"Name: {name}\n"
            text += f"Date: {answer['date']}\n"
            text += f"Content:\n{answer['answer']}"

            msg = await client.send_message(chat.id, text)
            reveal_answers_data.append({"question_id": question_id, "user_id": user.id, "msg_id": msg.message_id})

@app.on_message(filters.incoming & filters.text & filters.private, group=1)
async def put_score(client, msg):
    reply_msg = msg.reply_to_message

    if reply_msg:
        for data in reveal_answers_data:
            if reply_msg.message_id == data["msg_id"]:
                question_id = data["question_id"]

                try:
                    score = int(msg.text)
                except ValueError:
                    await msg.reply_text("Score <b>must</b> be an integer.")
                    return
                
                question = await get_question(question_id)
                if score < 0 or score > question["score"]:
                    await msg.reply_text(f"Score <b>must</b> be between 0-{question['score']}")
                    return
                
                if reply_msg.text.startswith(CHECKED_TEXT):
                    await msg.reply_text("You have checked this answer already.")
                    return

                await change_score(data["question_id"], data["user_id"], score)
                text = CHECKED_TEXT + "\n" + reply_msg.text

                await client.edit_message_text(
                    msg.from_user.id,
                    reply_msg.message_id,
                    text
                )

@app.on_message(filters.incoming & filters.text & filters.group & filters.command(["scores", "revealscores"], "/"))
async def reveal_score(client, msg):
    reply = await msg.reply_text("Fetching scores...")
    
    if not await is_admin(msg.chat.id, msg.from_user.id):
        await reply.edit_text("Only teachers (admins) can run this command.")
        return

    reply_msg = msg.reply_to_message
    if not reply_msg:
        await reply.edit_text("Please reply to a question message to reveal students' score for it.")
        return

    question = await get_question(reply_msg.message_id)
    if not question["is_closed"]:
        await reply.edit_text("Question is not closed. Please close the question before running this command.")
        return
    
    scores = await get_scores(question["msg_id"])
    if not scores:
        await reply.edit_text("No score data.")
        return
    
    text = "<b>Scores</b>\n"

    for score in scores:
        user = await client.get_users(score[0])
        name = user.first_name if user.first_name else "" + " " + user.last_name if user.last_name else ""
        text += f"- {name} ({score[1]})\n"

    await reply.edit_text(text)

@app.on_message(filters.incoming & filters.text & filters.group & filters.command("close", "/"))
async def close(_, msg):
    reply = await msg.reply_text("Closing question...")

    if not await is_admin(msg.chat.id, msg.from_user.id):
        await reply.edit_text("Only teachers (admins) can run this command.")
        return
    
    reply_msg = msg.reply_to_message
    if not reply_msg:
        await reply.edit_text("Please reply to a question message to close the question.")
        return

    question = await get_question(reply_msg.message_id)
    if not question:
        await reply.edit_text("This was already closed.")
        return
    
    await close_question(question["msg_id"])
    await reply.edit_text("Question closed.")
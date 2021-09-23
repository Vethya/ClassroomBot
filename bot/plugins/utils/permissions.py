from bot import app

async def is_admin(chat_id, user_id):
    status = (await app.get_chat_member(chat_id, user_id)).status
    
    if status in ["creator", "administrator"]:
        return True
    else:
        return False
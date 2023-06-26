import asyncio
import os
import shutil

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper
from Music.core.users import user_data
from Music.helpers.formatters import formatter


@hellbot.app.on_message(filters.command("autoend") & Config.SUDO_USERS)
@UserWrapper
async def auto_end_stream(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "**Usage:**\n\n__To turn off autoend:__ `/autoend off`\n__To turn on autoend:__ `/autoend on`"
        )
    cmd = message.command[1].lower()
    autoend = await db.get_autoend()
    if cmd == "on":
        if autoend:
            await message.reply_text("AutoEnd is already enabled.")
        else:
            await db.set_autoend(True)
            await message.reply_text(
                "AutoEnd Enabled! Now I will automatically end the stream after 5 minutes when the VC is empty."
            )
    elif cmd == "off":
        if autoend:
            await db.set_autoend(False)
            await message.reply_text("AutoEnd Disabled!")
        else:
            await message.reply_text("AutoEnd is already disabled.")
    else:
        await message.reply_text(
            "**Usage:**\n\n__To turn off autoend:__ `/autoend off`\n__To turn on autoend:__ `/autoend on`"
        )


@hellbot.app.on_message(filters.command("gban") & Config.SUDO_USERS)
@UserWrapper
async def gban(_, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(
                "Reply to a user's message or give their id."
            )
        user = await hellbot.app.get_users(message.command[1])
        user_id = user.id
        mention = user.mention
    else:
        user_id = message.reply_to_message.from_user.id
        mention = message.reply_to_message.from_user.mention
    if user_id == message.from_user.id:
        return await message.reply_text("You can't gban yourself.")
    elif user_id == hellbot.app.id:
        return await message.reply_text("Yo! I'm not stupid to gban myself.")
    elif user_id in Config.SUDO_USERS:
        return await message.reply_text("I can't gban my sudo users.")
    is_gbanned = await db.is_gbanned_user(user_id)
    if is_gbanned:
        return await message.reply_text(f"{mention} is already gbanned.")
    if user_id not in Config.BANNED_USERS:
        Config.BANNED_USERS.add(user_id)
    all_chats = []
    chats = await db.get_all_chats()
    async for chat in chats:
        all_chats.append(int(chat["chat_id"]))
    eta = formatter.get_readable_time(len(all_chats))
    hell = await message.reply_text(
        f"{mention} is being gbanned from by the bot. This might take around {eta}."
    )
    count = 0
    for chat_id in all_chats:
        try:
            await hellbot.app.ban_chat_member(chat_id, user_id)
            count += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.x))
        except Exception:
            pass
    await db.add_gbanned_user(user_id)
    await message.reply_text(
        f"**Gbanned Successfully!**\n\n**User:** {mention}\n**Chats:** `{count} chats`"
    )
    await hell.delete()


@hellbot.app.on_message(filters.command("ungban") & Config.SUDO_USERS)
@UserWrapper
async def gungabn(_, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(
                "Reply to a user's message or give their id."
            )
        user = await hellbot.app.get_users(message.command[1])
        user_id = user.id
        mention = user.mention
    else:
        user_id = message.reply_to_message.from_user.id
        mention = message.reply_to_message.from_user.mention
    is_gbanned = await db.is_gbanned_user(user_id)
    if not is_gbanned:
        return await message.reply_text(f"{mention} is not gbanned.")
    if user_id in Config.BANNED_USERS:
        Config.BANNED_USERS.remove(user_id)
    all_chats = []
    chats = await db.get_all_chats()
    async for chat in chats:
        all_chats.append(int(chat["chat_id"]))
    eta = formatter.get_readable_time(len(all_chats))
    hell = await message.reply_text(
        f"{mention} is being ungban from by the bot. This might take around {eta}."
    )
    count = 0
    for chat_id in all_chats:
        try:
            await hellbot.app.unban_chat_member(chat_id, user_id)
            count += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.x))
        except Exception:
            pass
    await db.remove_banned_user(user_id)
    await message.reply_text(
        f"**Ungbanned Successfully!**\n\n**User:** {mention}\n**Chats:** `{count}`"
    )
    await hell.delete()


@hellbot.app.on_message(filters.command("listgban") & Config.SUDO_USERS)
@UserWrapper
async def gbanned_list(_, message: Message):
    users = await db.get_gbanned_users()
    if len(users) == 0:
        return await message.reply_text("No Gbanned Users Found!")
    hell = await message.reply_text("Fetching Gbanned Users...")
    msg = "**Gbanned Users:**\n\n"
    count = 0
    for user_id in users:
        count += 1
        try:
            user = await hellbot.app.get_users(user_id)
            user = user.first_name if not user.mention else user.mention
            msg += f"{'0' if count <= 9 else ''}{count}: {user}\n"
        except Exception:
            msg += f"{'0' if count <= 9 else ''}{count}: [User] `{user_id}`\n"
            continue
    if count == 0:
        return await hell.edit_text("No Gbanned Users Found!")
    else:
        return await hell.edit_text(msg)


@hellbot.app.on_message(filters.command("logs") & Config.SUDO_USERS)
@UserWrapper
async def log_(_, message: Message):
    try:
        if os.path.exists("Mello.log"):
            log = open("Mello.log", "r")
            lines = log.readlines()
            logdata = ""
            try:
                limit = int(message.text.split(None, 1)[1])
            except:
                limit = 100
            for x in lines[-limit:]:
                logdata += x
            link = await formatter.bb_paste(logdata)
            return await message.reply_text(
                f"**Logs:** {link}", disable_web_page_preview=True
            )
        else:
            return await message.reply_text("No Logs Found!")
    except Exception as e:
        await message.reply_text(f"**ERROR:** \n\n`{e}`")


@hellbot.app.on_message(filters.command("restart") & Config.SUDO_USERS)
@UserWrapper
async def restart_(_, message: Message):
    hell = await message.reply_text("Notifying Chats about restart....")
    active_chats = await db.get_active_vc()
    count = 0
    for x in active_chats:
        cid = int(x["chat_id"])
        try:
            await hellbot.app.send_message(
                cid,
                f"**Bot is restarting in a minute or two.**\n\nPlease wait for a minute before using me again.",
            )
            await hellmusic.leave_vc(cid)
            count += 1
        except Exception:
            pass
    try:
        shutil.rmtree("cache")
        shutil.rmtree("downloads")
    except:
        pass
    await hell.edit(
        f"Notified **{count}** chat(s) about the restart.\n\nRestarting now..."
    )
    os.system(f"kill -9 {os.getpid()} && bash StartMusic")


@hellbot.app.on_message(filters.command("sudolist") & Config.SUDO_USERS)
@UserWrapper
async def sudoers_list(_, message: Message):
    text = "**⍟ God Users:**\n"
    gods = 0
    for x in Config.GOD_USERS:
        try:
            if x in user_data.DEVS:
                continue
            user = await hellbot.app.get_users(x)
            user = user.first_name if not user.mention else user.mention
            gods += 1
        except Exception:
            continue
        text += f"{'0' if gods <= 9 else ''}{gods}: {user}\n"
    sudos = 0
    for user_id in Config.SUDO_USERS:
        if user_id not in user_data.DEVS:
            if user_id in Config.GOD_USERS:
                continue
            try:
                user = await hellbot.app.get_users(user_id)
                user = user.first_name if not user.mention else user.mention
                if sudos == 0:
                    sudos += 1
                    text += "\n**⍟ Sudo Users:**\n"
                gods += 1
                text += f"{'0' if gods <= 9 else ''}{gods}: {user}\n"
            except Exception:
                continue
    if gods == 0:
        await message.reply_text("No sudo users found.")
    else:
        await message.reply_text(text)

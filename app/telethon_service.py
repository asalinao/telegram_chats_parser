import asyncio
import re
from datetime import datetime, timezone
import time
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, PeerUser, PeerChat, PeerChannel, 
	DocumentAttributeAudio, DocumentAttributeVideo, DocumentAttributeAnimated,
	DocumentAttributeSticker, DocumentAttributeFilename
)
from telethon.errors import (
    UserAlreadyParticipantError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    FloodWaitError,
)


async def join_chat_for_all(
    chat_url: str,
    clients: list[TelegramClient],
    delay: float = 1.5,
):
    is_private = "+" in chat_url or "joinchat" in chat_url

    if is_private:
        invite_hash = re.split(r"[+/]", chat_url)[-1]
    else:
        username = chat_url.rstrip("/").split("/")[-1]

    for client in clients:
        try:
            # Авто-старт клиента
            if not client.is_connected():
                await client.start()
                if not await client.is_user_authorized():
                    print(f"[!] {client.session.filename} не авторизован")
                    continue

            # Вступление в чат
            if is_private:
                await client(ImportChatInviteRequest(invite_hash))
            else:
                await client(JoinChannelRequest(username))

            print(f"[+] {client.session.filename}: joined")

        except UserAlreadyParticipantError:
            print(f"[=] {client.session.filename}: already joined")

        except InviteHashExpiredError:
            print(f"[!] Invite expired: {chat_url}")
            break

        except InviteHashInvalidError:
            print(f"[!] Invalid invite: {chat_url}")
            break

        except FloodWaitError as e:
            print(f"[⏳] FloodWait {e.seconds}s for {client.session.filename}")
            await asyncio.sleep(e.seconds)

        except Exception as e:
            print(f"[x] {client.session.filename}: {type(e).__name__} — {e}")

        await asyncio.sleep(delay)


async def get_channel_info(client_tg, link: str):
    await client_tg.start()
    
    # Получаем объект канала
    try:
        full = await client_tg(GetFullChannelRequest(link))
    except Exception as e:
        print("Ошибка при получении канала:", e)
        return None
    
    channel = full.chats[0] if full.chats else None
    if not channel:
        return None

    # Основная информация
    info = {
        "chat_id": channel.id,
        "name": getattr(channel, "title", ""),
        "link": link,
        "private": 0 if getattr(channel, "username", None) else 1,
        "participants": getattr(full.full_chat, "participants_count", 0),
        "forum": 1 if getattr(full.full_chat, "forum", False) else 0,
        "write_allowed": 0 if getattr(channel, "default_banned_rights", None) and getattr(channel.default_banned_rights, "send_messages", False) else 1,
        "participants_visible": 1 if hasattr(full.full_chat, "participants_count") else 0,
        "processed_dttm": datetime.utcnow()
    }

    return info


async def dump_all_messages(clients_tg, client_click, url):
	batch_size = 3000 # максимальное коичество сообщений которые парсятся до кд

	offset_msg = 0# номер записи, с которой начинается считывание
	limit_msg = 100  # максимальное число записей, передаваемых за один раз
	min_id = 0

	all_messages = []  # список всех сообщений
	total_messages = 0

	processed_dttm = datetime.now(timezone.utc)

	FIELDS = [
		"message_id", "chat_id", "user_id", "report_dttm", "text", "media_type",
		"photo", "video", "round", "voice", "gif", "sticker", "spoiler",
		"file_name", "size", "processed_dttm"
	]

	def parse_message(msg):
		values = {
			"message_id": msg.id,
			"chat_id": getattr(msg.peer_id, 'channel_id', getattr(msg.peer_id, 'chat_id', None)),
			"user_id": getattr(msg.from_id, "user_id", None),
			"report_dttm": msg.date.isoformat() if msg.date else None,
			"text": msg.message or "",
			"media_type": None,

			"photo": False,
			"video": False,
			"round": False,
			"voice": False,
			"gif": False,
			"sticker": False,
			"spoiler": False,

			"file_name": None,
			"size": None,

			"processed_dttm": processed_dttm
		}

		# --- Фото ---
		if isinstance(msg.media, MessageMediaPhoto):
			values["media_type"] = "photo"
			values["photo"] = True
			values["spoiler"] = getattr(msg.media, "spoiler", False)

		# --- Документы ---
		elif isinstance(msg.media, MessageMediaDocument):
			doc = msg.media.document
			values["media_type"] = doc.mime_type
			values["spoiler"] = getattr(msg.media, "spoiler", False)
			values["size"] = doc.size

			for attr in doc.attributes:
				if isinstance(attr, DocumentAttributeAudio) and attr.voice:
					values["voice"] = True
					values["media_type"] = "voice"

				elif isinstance(attr, DocumentAttributeVideo):
					if attr.round_message:
						values["round"] = True
						values["media_type"] = "round_video"
					else:
						values["video"] = True
						values["media_type"] = "video"

				elif isinstance(attr, DocumentAttributeAnimated):
					values["gif"] = True
					values["media_type"] = "gif"

				elif isinstance(attr, DocumentAttributeSticker):
					values["sticker"] = True
					values["media_type"] = "sticker"

				elif isinstance(attr, DocumentAttributeFilename):
					values["file_name"] = attr.file_name

		# возвращаем список в фиксированном порядке
		return [values[field] for field in FIELDS]
	
	chats = []
	for client in clients_tg:
		chat = await client.get_entity(url)
		chats.append(chat)
		time.sleep(30)

	chat_id = chats[0].id

	# получаем id последнего спаршенного сообщения в чате
	max_message_id = client_click.query(f'''
		SELECT MAX(message_id) as message_id
		FROM dwh.messages
		WHERE chat_id = {chat_id}
	''').first_item['message_id']
	if max_message_id:
		min_id = max_message_id

	flg = False
	
	while True:
		# парсим сообщения поочереди каждым клиентом
		for client, chat in zip(clients_tg, chats):
			history = await client(GetHistoryRequest(
				peer=chat,
				offset_id=offset_msg,
				offset_date=None, add_offset=0,
				limit=limit_msg, max_id=0, min_id=min_id,
				hash=0))
			if not history.messages:
				flg = True
				break
			messages = history.messages

			for message in messages:
				try:
					message_to_append = parse_message(message)
					all_messages.append(message_to_append)

				except Exception as e:
					print(f"Message: {message.id} \n {e}")
			
			offset_msg = messages[len(messages) - 1].id
			total_messages += len(messages)

			if flg:
				break

		if len(all_messages) == batch_size * len(clients_tg) or flg:
				client_click.insert('dwh.messages', all_messages, column_names=FIELDS)
				all_messages = []
			
		if flg:
			break

from telethon.sync import TelegramClient
import clickhouse_connect
import asyncio
import csv
import os

from fastapi import FastAPI

from telethon_service import dump_all_messages

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
CLICKHOUSE_USERNAME = os.getenv("CLICKHOUSE_USERNAME", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

for attempt in range(3):
    try:
        client_click = clickhouse_connect.get_client(host=CLICKHOUSE_HOST, 
                                                     port=CLICKHOUSE_PORT, 
                                                     username=CLICKHOUSE_USERNAME, 
                                                     password=CLICKHOUSE_PASSWORD)
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} to connect to ClickHouse failed: {e}")
        if attempt == 2:
            raise e
        asyncio.sleep(2)

clients_dicts = []
with open('telegram.csv', newline="", encoding="utf-8") as f:
	reader = csv.DictReader(f)
	for row in reader:
		clients_dicts.append(row)

clients_tg = []
for c_dict in clients_dicts:
	client = TelegramClient(f"session_{c_dict['number'][-4:]}", api_id=c_dict['api_id'], api_hash=c_dict['api_hash'], device_model="iPhone 16", system_version="IOS 26.3")
	clients_tg.append(client)

async def dump_chat_by_url(clients_tg, client_click, url):
	await asyncio.gather(*(client.start() for client in clients_tg))
	await dump_all_messages(clients_tg, client_click, url)
	client_click.close()

app = FastAPI()

@app.get("/dump_chat_by_url")
async def dump_chat_by_url_point(url: str):
    await dump_chat_by_url(clients_tg, client_click, url)

@app.get("/get_text_messages_by_user_id")
def get_messages_by_user_id_point(user_id: int):
    query = f'''
    select * 
	from dwh.messages
	where user_id = {user_id}
    and (media_type is null or sticker = 1)
    '''

    result = client_click.query(query)
    query_result = result.result_rows 
    columns = result.column_names
    
    messages_list = []
    if query_result:
        for msg in query_result:
            raw_msg = dict(zip(columns, msg))
            msg_to_append = {
                "message_id": raw_msg["message_id"],
                "report_dttm": raw_msg["report_dttm"],
                "text": raw_msg["text"],
                "is_sticker": raw_msg["sticker"],
                "messsage link": f"https://t.me/c/{raw_msg['chat_id']}/{raw_msg['message_id']}"
            }
            messages_list.append(msg_to_append)
        print(messages_list)
        return {"messages": messages_list}
    else:
        return {"error": "Messages not found"}
    
@app.get("/get_media_messages_by_user_id")
def get_media_messages_by_user_id_point(user_id: int):
    query = f'''
    select * 
	from dwh.messages
	where user_id = {user_id}
    and media_type is not null 
    and sticker = 0
    '''

    result = client_click.query(query)
    query_result = result.result_rows 
    columns = result.column_names
    
    messages_list = []
    if query_result:
        for msg in query_result:
            raw_msg = dict(zip(columns, msg))
            msg_to_append = {
                "message_id": raw_msg["message_id"],
                "report_dttm": raw_msg["report_dttm"],
                "text": raw_msg["text"],
                "media_type": raw_msg["media_type"],
                "spoiler": raw_msg["spoiler"],
                "messsage link": f"https://t.me/c/{raw_msg['chat_id']}/{raw_msg['message_id']}"
            }
            messages_list.append(msg_to_append)
        print(messages_list)
        return {"messages": messages_list}
    else:
        return {"error": "Messages not found"}
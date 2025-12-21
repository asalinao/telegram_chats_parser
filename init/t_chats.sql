CREATE TABLE IF NOT EXISTS dwh.chats(
		chat_id UInt64, 
		name String,
		link String,
		private UInt8,
		participants UInt32,
		forum UInt8,
		write_allowed UInt8,
		participants_visible UInt8,
		processed_dttm DateTime64(3, 'UTC'),
		priority UInt8
) 
ENGINE=MergeTree() 
ORDER BY chat_id;
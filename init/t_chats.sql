CREATE TABLE chats(
		chat_id UInt64, 
		name String,
		link String,
		
		private UInt8,
		category LowCardinality(Nullable(String)),
		participants UInt32,
		forum UInt8,
		write_allowed UInt8,
		participants_visible UInt8,
		
		processed_dttm DateTime64(3, 'UTC')
	) 
	ENGINE=MergeTree() 
	ORDER BY participants;
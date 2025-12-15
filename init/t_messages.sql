CREATE TABLE IF NOT EXISTS dwh.messages
(
    message_id UInt64,
    chat_id UInt64,
    user_id Nullable(UInt64),
    report_dttm DateTime64(3, 'UTC'),
    text Nullable(String),
    media_type LowCardinality(Nullable(String)),

    photo Nullable(UInt8),
    video Nullable(UInt8),
    round Nullable(UInt8),
    voice Nullable(UInt8),
    gif Nullable(UInt8),
    sticker Nullable(UInt8),
    spoiler Nullable(UInt8),

    file_name Nullable(String),
    size Nullable(UInt64), 
    
    processed_dttm Nullable(DateTime64(3, 'UTC'))
)
ENGINE = MergeTree
ORDER BY (chat_id, message_id );
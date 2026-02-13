# encoding: utf-8

class FetcherError(object):
    """
    爬取器错误日志
    """

    ddls = ["""
    CREATE TABLE IF NOT EXISTS fetcher_errors
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fetcher_name VARCHAR(255) NOT NULL,
        error_message TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS fetcher_errors_created_at_index
    ON fetcher_errors(created_at DESC)
    """]

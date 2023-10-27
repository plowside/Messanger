import sqlite3, time



def _dict_factory(cursor, row):
    _ = {}
    for i, column in enumerate(cursor.description):
        _[column[0]] = row[i]
    return _

class SQLiteDatabase:
    def __init__(self, is_json=True, db_file='db.db'):
        self.db_file = db_file
        self.is_json = is_json
        self.con, self.cur = self._connect_to_database()

    def _get_connection(self):
        return (self.con, self.cur)


    def _connect_to_database(self):
        con = sqlite3.connect(self.db_file, check_same_thread=False)
        if self.is_json:
            con.row_factory = _dict_factory
        cur = con.cursor()
        return con, cur

    def close(self):
        if self.con:
            self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()


_db = SQLiteDatabase()
con, cur = _db._get_connection()

cur.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    hashed_password TEXT,
    registration_date INTEGER,
    avatar TEXT,
    last_online INTEGER,
    access_type INTEGER DEFAULT(1)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_name TEXT,
    conversation_avatar TEXT,
    conversation_type TEXT,
    create_date INTEGER,
    show_type INTEGER DEFAULT (1)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    user_id INTEGER,
    create_date INTEGER
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    message_id INTEGER,
    message_type TEXT,
    message_data TEXT,
    create_date INTEGER,
    from_id INTEGER
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_settings(
    user_id INTEGER,
    conversation_id INTEGER,
    is_muted BOOL DEFAULT (False)
    )''')

cur.execute('''CREATE TABLE IF NOT EXISTS conversations_updates(
    user_id INTEGER,
    conversation_id INTEGER,
    message_id INTEGER,
    update_type TEXT,
    update_data TEXT,
    create_date INTEGER
    )''')

con.commit()

def db_getConversations(user_id):
    conversations = cur.execute('''
SELECT c.id, c.conversation_name AS name, c.conversation_avatar AS avatar, c.conversation_type AS type, cs.is_muted,
       last_message.message_data AS last_message_data, last_message.create_date AS last_message_date
FROM conversations AS c
JOIN conversations_settings AS cs
ON c.id = cs.conversation_id
LEFT JOIN (
    SELECT cm.conversation_id, cm.message_data, cm.create_date
    FROM conversations_messages AS cm
    WHERE cm.message_type = "message"
    AND cm.message_id = (SELECT MAX(cm2.message_id) FROM conversations_messages AS cm2 WHERE cm2.conversation_id = cm.conversation_id)
) AS last_message
ON c.id = last_message.conversation_id
WHERE c.show_type = 1
AND c.id IN (SELECT conversation_id FROM conversations_users WHERE user_id = ?)
''', [user_id]).fetchall()

    for x in conversations:
        x['last_message'] = {'data': x['last_message_data'], 'date': x['last_message_date']}
        for g in ['last_message_data', 'last_message_date']:
            del x[g]


    return conversations

def db_getMessages(user_id, conversation_id):
    messages = cur.execute('''
SELECT message_id, message_type AS type, message_data, create_date, from_id
FROM conversations_messages
WHERE conversation_id = ?
AND message_id NOT IN (SELECT message_id FROM conversations_updates WHERE update_type = "message_delete")
''', [conversation_id]).fetchall()
  
    for x in messages:
        if x['from_id'] == user_id:
            x['is_me'] = True
        else:
            x['is_me'] = False


    return messages
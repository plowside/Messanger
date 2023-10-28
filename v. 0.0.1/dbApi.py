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
    custom_id INTEGER,
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

_db.close()

def db_getConversations(user_id):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()


    conversations = cur.execute('''
SELECT c.custom_id AS id, c.conversation_name AS name, c.conversation_avatar AS avatar, c.conversation_type AS type, cs.is_muted,
       last_message.message_data AS last_message_data, last_message.create_date AS last_message_date
FROM conversations AS c
JOIN conversations_settings AS cs
ON c.id = cs.conversation_id AND ? = cs.user_id
LEFT JOIN (
    SELECT cm.conversation_id, cm.message_data, cm.create_date
    FROM conversations_messages AS cm
    WHERE cm.message_type = "message"
    AND cm.message_id = (SELECT MAX(cm2.message_id) FROM conversations_messages AS cm2 WHERE cm2.conversation_id = cm.conversation_id)
) AS last_message
ON c.id = last_message.conversation_id
WHERE c.show_type = 1
AND ? IN (SELECT user_id FROM conversations_users WHERE conversation_id = c.id)
''', [user_id,user_id]).fetchall()

    for x in conversations:
        x['last_message'] = {'data': x['last_message_data'], 'date': x['last_message_date']}
        for g in ['last_message_data', 'last_message_date']:
            del x[g]


    return conversations

def db_getMessages(user_id, conversation_id):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    
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

def db_addMessage(user_id, chat_id, type, text):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    ts = int(time.time())

    cur.execute('''INSERT INTO conversations_messages (conversation_id, message_id, message_type, message_data, create_date, from_id)
                   VALUES (?, (SELECT IFNULL(MAX(message_id), 0) + 1 FROM conversations_messages WHERE conversation_id = ? AND message_type = ?), ?, ?, ?, ?);''', [chat_id, chat_id, type, type, text, ts, user_id])
    con.commit()


    message = cur.execute('SELECT message_id, message_type AS type, message_data, create_date, from_id FROM conversations_messages WHERE conversation_id = ? AND create_date = ? AND from_id = ? AND message_data = ?', [chat_id, ts, user_id, text]).fetchone()
    message['is_me'] = True
    return message

def db_reset_user(user_id, hashed_password):
    print(user_id, hashed_password)
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    
    cur.execute('UPDATE users SET hashed_password = ? WHERE id = ?', [hashed_password, user_id])
    con.commit()

    return cur.execute('SELECT username FROM users WHERE id = ?', [user_id]).fetchone()['username']

def db_get_chat_users(chat_id):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    return cur.execute('SELECT user_id FROM conversations_users WHERE conversation_id = ?', [chat_id]).fetchall()
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


def DB_CreateTables():
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        hashed_password TEXT NOT NULL,
                        registration_date INTEGER,
                        access_type INTEGER
                    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS dialogs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dialog_name TEXT,
                        dialog_type TEXT,
                        creation_date INTEGER
                    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS dialog_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        dialog_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (dialog_id) REFERENCES dialogs (id)
                    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dialog_id INTEGER,
                        sender_id INTEGER,
                        message_type TEXT,
                        message_text TEXT,
                        send_time INTEGER,
                        FOREIGN KEY (dialog_id) REFERENCES dialogs (id),
                        FOREIGN KEY (sender_id) REFERENCES users (id)
                    )''')
    con.commit()


def db_format_sql(q):
    sql_query = ""
    update_pairs = []
    for key, value in q.items():
        if value is not None:
            update_pairs.append(f"{key} = '{value}'")
    
    # Объединение всех пар поле=значение с запятыми
    sql_query += ', '.join(update_pairs)

    return sql_query



def db_create_user(username, first_name = None, last_name = None, hashed_password = None, access_type = 1):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    creation_date = int(time.time())

    cur.execute("INSERT INTO users(username, first_name, last_name, hashed_password, registration_date, access_type) VALUES (?, ?, ?, ?, ?, ?)", [username, first_name, last_name, hashed_password, creation_date, access_type])
    user_id = cur.lastrowid

    con.commit()


    return user_id

def db_get_user(user_id = None, username = None):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()    

    user = cur.execute('SELECT * FROM users WHERE id = ? OR username = ?', [user_id, username]).fetchone()

    return user

def db_update_user(user_id, **kwargs):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    q = db_format_sql(kwargs)
    cur.execute(f"UPDATE users SET {q} WHERE id = {user_id}")
    con.commit()

    user = cur.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()


    return user


def db_create_dialog(user_id, target_user_id, dialog_name, dialog_type = 'private'):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    creation_date = int(time.time())

    cur.execute("INSERT INTO dialogs (dialog_name, dialog_type, creation_date) VALUES (?, ?, ?)", [dialog_name, dialog_type, creation_date])
    dialog_id = cur.lastrowid

    con.commit()

    db_add_user_to_dialog(user_id, dialog_id)
    db_add_user_to_dialog(target_user_id, dialog_id)


    return dialog_id

def db_get_dialogs(user_id, dialog_id = None):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    if dialog_id:
        dialog = cur.execute('''
            SELECT
                d.id AS dialog_id,
                d.dialog_name,
                d.dialog_type,
                m.id AS message_id,
                m.sender_id,
                m.message_type,
                m.message_text,
                m.send_time
            FROM dialogs AS d
            LEFT JOIN (
                SELECT
                    dialog_id,
                    MAX(send_time) AS max_send_time
                FROM messages
                GROUP BY dialog_id
            ) AS m1 ON d.id = m1.dialog_id
            LEFT JOIN messages AS m ON m1.dialog_id = m.dialog_id AND m1.max_send_time = m.send_time
            LEFT JOIN dialog_users AS du ON d.id = du.dialog_id
            WHERE du.dialog_id = ?
        ''', [dialog_id]).fetchall()
    else:
        dialog = cur.execute('''
            SELECT
                d.id AS dialog_id,
                d.dialog_name,
                d.dialog_type,
                m.id AS message_id,
                m.sender_id,
                m.message_type,
                m.message_text,
                m.send_time
            FROM dialogs AS d
            LEFT JOIN (
                SELECT
                    dialog_id,
                    MAX(send_time) AS max_send_time
                FROM messages
                GROUP BY dialog_id
            ) AS m1 ON d.id = m1.dialog_id
            LEFT JOIN messages AS m ON m1.dialog_id = m.dialog_id AND m1.max_send_time = m.send_time
            LEFT JOIN dialog_users AS du ON d.id = du.dialog_id
            WHERE du.user_id = ?
        ''', [user_id]).fetchall()


    return dialog

def db_find_dialogs(user_id, query):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    query = f'%{query.lower()}%'
    results = {}

    results['user_dialogs'] = cur.execute('''
            SELECT
                d.id AS dialog_id,
                d.dialog_name,
                d.dialog_type,
                m.id AS message_id,
                m.sender_id,
                m.message_type,
                m.message_text,
                m.send_time
            FROM dialogs AS d
            LEFT JOIN (
                SELECT
                    dialog_id,
                    MAX(send_time) AS max_send_time
                FROM messages
                GROUP BY dialog_id
            ) AS m1 ON d.id = m1.dialog_id
            LEFT JOIN messages AS m ON m1.dialog_id = m.dialog_id AND m1.max_send_time = m.send_time
            LEFT JOIN dialog_users AS du ON d.id = du.dialog_id
            WHERE du.user_id = ? AND
            d.dialog_name LIKE ? COLLATE NOCASE
        ''', [user_id, f'%{query}%']).fetchall()

    results['users'] = cur.execute('''
            SELECT id AS user_id, username, first_name, last_name FROM users
            WHERE id != ? AND LOWER(username) LIKE ?
               OR LOWER(first_name) LIKE ?
               OR LOWER(last_name) LIKE ?
        ''', [user_id, query, query, query]).fetchall()

    return results


def db_add_user_to_dialog(user_id, dialog_id):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    creation_date = int(time.time())

    cur.execute("INSERT INTO dialog_users (user_id, dialog_id) VALUES (?, ?)", (user_id, dialog_id))
    id = cur.lastrowid    

    con.commit()


    return id

def db_get_dialog_users(dialog_id):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    dialog_users = cur.execute("SELECT id, user_id FROM dialog_users WHERE dialog_id = ?", [dialog_id]).fetchall()

    return dialog_users


def db_create_message(dialog_id, sender_id, message_type, message_text, send_time):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    cur.execute("INSERT INTO messages (dialog_id, sender_id, message_type, message_text, send_time) VALUES (?, ?, ?, ?, ?)", (dialog_id, sender_id, message_type, message_text, send_time))
    message_id = cur.lastrowid

    con.commit()


    return message_id

def db_get_messages(dialog_id, message_id = None):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    if message_id:
        messages = cur.execute("SELECT id AS message_id, dialog_id, sender_id, message_type, message_text, send_time FROM messages WHERE dialog_id = ? AND message_id = ?", [dialog_id, message_id]).fetchone()
    else:
        messages = cur.execute("SELECT id AS message_id, dialog_id, sender_id, message_type, message_text, send_time FROM messages WHERE dialog_id = ?", [dialog_id]).fetchall()

    return messages


DB_CreateTables()
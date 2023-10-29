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


def db_create_dialog(user_id, target_user_id, dialog_name = None, dialog_type = 'private'):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()
    creation_date = int(time.time())

    sq = cur.execute("""SELECT d.id
        FROM dialogs d
        WHERE EXISTS (
            SELECT 1
            FROM dialog_users du1
            WHERE du1.dialog_id = d.id
            AND du1.user_id = ?)
        AND EXISTS (
            SELECT 1
            FROM dialog_users du2
            WHERE du2.dialog_id = d.id
            AND du2.user_id = ?);
    """, [user_id, target_user_id]).fetchall()

    if sq != []:
        return False


    cur.execute("INSERT INTO dialogs (dialog_name, dialog_type, creation_date) VALUES (?, ?, ?)", [dialog_name, dialog_type, creation_date])
    dialog_id = cur.lastrowid

    con.commit()

    db_add_user_to_dialog(user_id, dialog_id)
    db_add_user_to_dialog(target_user_id, dialog_id)


    return dialog_id

def db_get_dialogs(user_id = None, dialog_id = None):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    if dialog_id:
        dialog = cur.execute('''
            SELECT
                d.id AS dialog_id,
                CASE 
                    WHEN d.dialog_name IS NULL THEN u.username
                    ELSE d.dialog_name
                END AS dialog_name,
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
            LEFT JOIN users AS u ON u.id = du.user_id
            WHERE du.dialog_id = ?;

        ''', [dialog_id]).fetchall()
    else:
        dialog = cur.execute('''
            SELECT
                d.id AS dialog_id,
                CASE 
                    WHEN d.dialog_name IS NULL THEN u.username
                    ELSE d.dialog_name
                END AS dialog_name,
                d.dialog_type,
                m.sender_id AS last_message_sender_id,
                m.message_text AS last_message_text,
                m.send_time AS last_message_send_time,
                du_.user_id

            FROM dialog_users as du    


            LEFT JOIN
                dialogs AS d ON d.id = du.dialog_id

            LEFT JOIN (
                SELECT
                    dialog_id,
                    MAX(send_time) AS max_send_time
                FROM messages
                GROUP BY dialog_id
            ) AS m1 ON du.dialog_id = m1.dialog_id
            LEFT JOIN 
                messages AS m ON m1.dialog_id = m.dialog_id AND
                m1.max_send_time = m.send_time

            LEFT JOIN dialog_users as du_ ON du_.dialog_id = d.id AND du_.user_id != ?
            LEFT JOIN users AS u ON u.id = du_.user_id

            WHERE du.user_id = ?
            ''', [user_id, user_id]).fetchall()
        for x in dialog:
            x['last_message'] = {'sender_id': x['last_message_sender_id'], 'text': x['last_message_text'],'send_time': x['last_message_send_time']}
            del x['last_message_sender_id']; del x['last_message_text']; del x['last_message_send_time']
    return dialog


def db_find_dialogs(user_id, query_):
    _db = SQLiteDatabase()
    con, cur = _db._get_connection()

    query_ = query_.lower()
    query = f'%{query_}%'
    results = {}

    results['temp_user_dialogs'] = cur.execute('''
        SELECT
            d.id AS dialog_id,
            CASE 
                WHEN d.dialog_name IS NULL THEN u.username
                ELSE d.dialog_name
            END AS dialog_name,
            d.dialog_type,
            m.sender_id AS last_message_sender_id,
            m.message_text AS last_message_text,
            m.send_time AS last_message_send_time,
            du_.user_id,
            u.first_name AS temp_fn,
            u.last_name AS temp_ln

        FROM dialog_users as du    


        LEFT JOIN
            dialogs AS d ON d.id = du.dialog_id

        LEFT JOIN (
            SELECT
                dialog_id,
                MAX(send_time) AS max_send_time
            FROM messages
            GROUP BY dialog_id
        ) AS m1 ON du.dialog_id = m1.dialog_id
        LEFT JOIN 
            messages AS m ON m1.dialog_id = m.dialog_id AND
            m1.max_send_time = m.send_time

        LEFT JOIN dialog_users as du_ ON du_.dialog_id = d.id AND du_.user_id != ?
        LEFT JOIN users AS u ON u.id = du_.user_id

        WHERE du.user_id = ?
        ''', [user_id, user_id]).fetchall()

    results['user_dialogs'] = []
    user_dialogs_id = []
    for i, x in enumerate(results['temp_user_dialogs']):
        user_dialogs_id.append(x['user_id'])
        if query_ not in (x['dialog_name'].lower() if x['dialog_name'] else '') and query_ not in (x['temp_fn'].lower() if x['temp_fn'] else '') and query_ not in (x['temp_ln'].lower() if x['temp_ln'] else ''):
            continue

        del x['dialog_name']; del x['temp_fn']; del x['temp_ln']


        x['last_message'] = {'sender_id': x['last_message_sender_id'], 'text': x['last_message_text'],'send_time': x['last_message_send_time']}
        del x['last_message_sender_id']; del x['last_message_text']; del x['last_message_send_time']

        results['user_dialogs'].append(x)




    results['temp_users'] = cur.execute(f'''
            SELECT id AS user_id, username, first_name, last_name FROM users
            WHERE id != ? AND user_id NOT IN ({",".join(["?"] * len(user_dialogs_id))})
        ''', [user_id] + user_dialogs_id).fetchall()

    results['users'] = []
    for i, x in enumerate(results['temp_users']):
        if query_ not in (x['username'].lower() if x['username'] else '') and query_ not in (x['first_name'].lower() if x['first_name'] else '') and query_ not in (x['last_name'].lower() if x['last_name'] else ''):
            continue

        results['users'].append(x)


    del results['temp_users']; del results['temp_user_dialogs']
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
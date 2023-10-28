import sqlite3

# Assuming you have a SQLite database connection 'conn' and a cursor 'cur' already established
def _dict_factory(cursor, row):
    _ = {}
    for i, column in enumerate(cursor.description):
        _[column[0]] = row[i]
    return _


user_id = 2  # Replace with the actual user_id
con = sqlite3.connect('db.db')
con.row_factory = _dict_factory
cur = con.cursor()

cur.execute('''
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
    ''', [user_id, user_id])

# Fetch the results
results = cur.fetchall()

# Now, 'results' contains a list of tuples where each tuple represents the information for a dialog/message related to the user_id.

for row in results:
    row['last_message'] = {'sender_id': row['last_message_sender_id'], 'text': row['last_message_text'],'send_time': row['last_message_send_time']}
    del row['last_message_sender_id']; del row['last_message_text']; del row['last_message_send_time']
    print(row)
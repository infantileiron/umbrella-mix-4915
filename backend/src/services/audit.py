def record(cursor, actor, action, subject):
    cursor.execute('INSERT INTO audit_events (actor, action, subject) VALUES (%s,%s,%s)',
                   (actor, action, str(subject)))

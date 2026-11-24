from scripts.seed_cases import PLAN, USERS, demo_tickets
from src.models.db import transaction
from src.utils.security import hash_password
from src.utils.serialization import canonical, checksum


def main():
    with transaction() as cursor:
        cursor.executemany('INSERT INTO users (username,display_name,password_hash,role) VALUES (%s,%s,%s,%s) '
                           'ON DUPLICATE KEY UPDATE username=users.username',
                           [(name, display, hash_password(password), role) for name, display, password, role in USERS])
        cursor.executemany('INSERT INTO tickets (code,branch,worked_on,ribs,fabric,mechanism,minutes,note) '
                           'VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE code=tickets.code',
                           list(demo_tickets()))
        cursor.execute('INSERT INTO comparison_plans (plan_key,version,label,focus_branch,control_branch,coefficient_ref,'
                       'date_from,date_to,min_samples,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
                       'ON DUPLICATE KEY UPDATE plan_key=comparison_plans.plan_key', PLAN)
        keys = {}
        for table, columns in [('users', 'username'), ('tickets', 'code'), ('comparison_plans', 'plan_key, version')]:
            cursor.execute(f'SELECT {columns} FROM {table} ORDER BY {columns}')
            keys[table] = cursor.fetchall()
    print(canonical({'counts': {table: len(values) for table, values in keys.items()},
                     'natural_keys_sha256': checksum(canonical(keys))}))


if __name__ == '__main__':
    main()

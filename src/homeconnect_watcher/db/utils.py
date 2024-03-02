from psycopg import Connection


def clean_schema(connection: Connection) -> None:
    with connection.cursor() as cursor:
        db_name = connection.info.dbname
        cursor.execute(f"DROP SCHEMA IF EXISTS {db_name} CASCADE; CREATE SCHEMA {db_name};")

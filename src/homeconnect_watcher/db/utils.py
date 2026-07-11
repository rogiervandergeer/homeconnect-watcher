from psycopg import Connection, sql


def clean_schema(connection: Connection) -> None:
    with connection.cursor() as cursor:
        db_name = connection.info.dbname
        cursor.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE; CREATE SCHEMA {};").format(
                sql.Identifier(db_name), sql.Identifier(db_name)
            )
        )

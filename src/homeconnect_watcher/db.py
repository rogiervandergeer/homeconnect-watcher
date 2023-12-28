from importlib.resources import files

from psycopg import Connection


def clean_schema(connection: Connection) -> None:
    with connection.cursor() as cursor:
        db_name = connection.info.dbname
        cursor.execute(f"DROP SCHEMA IF EXISTS {db_name} CASCADE; CREATE SCHEMA {db_name};")


def create_views(connection: Connection, views: dict[str, str], drop: bool = True):
    with connection.cursor() as cursor:
        if drop:
            for view in reversed(views.keys()):
                cursor.execute(f"DROP VIEW IF EXISTS {view};")
        for name, sql in views.items():
            cursor.execute(sql)


def load_views() -> dict[str, str]:
    resources = [r for r in (files("homeconnect_watcher") / "sql").iterdir() if r.is_file()]
    return {resource.name[2:-4]: resource.read_text() for resource in sorted(resources)}

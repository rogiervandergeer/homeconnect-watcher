from importlib.resources import files
from re import IGNORECASE, search


class View:
    def __init__(self, query: str):
        self.query = query

    @property
    def drop_query(self) -> str:
        return f"DROP {'MATERIALIZED' if self.materialized else ''} VIEW IF EXISTS {self.name}"

    @property
    def materialized(self) -> bool:
        return "MATERIALIZED VIEW" in self.query

    @property
    def name(self) -> str:
        result = search("VIEW(?: IF NOT EXISTS)? ([a-z_]+) AS", self.query, IGNORECASE)
        return result.group(1)


def load_views() -> list[View]:
    resources = [r for r in (files("homeconnect_watcher") / "sql").iterdir() if r.is_file()]
    return [View(resource.read_text()) for resource in sorted(resources)]


def load_view(name: str) -> View:
    for view in load_views():
        if view.name == name:
            return view
    raise KeyError(f"No such view: {name}")

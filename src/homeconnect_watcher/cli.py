from typer import Typer
from uvicorn import run

from homeconnect_watcher.api import define_endpoints

app = Typer()


@app.command()
def watch(host: str = "0.0.0.0", port: int = 8000, reload: bool = False, simulation: bool = False):
    api = define_endpoints(simulation=simulation)
    run(api, host=host, port=port, reload=reload)

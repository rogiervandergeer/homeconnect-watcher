from datetime import datetime, timedelta
from pathlib import Path

from pytest import fixture
from pytest_mock.plugin import MockerFixture

from homeconnect_watcher.exporter.file import FileExporter


class TestFileExporter:
    @fixture(scope="function")
    def exporter(self, tmp_path: Path):
        exporter = FileExporter(tmp_path, flush_interval=timedelta(minutes=5))
        return exporter

    def test_file_opened(self, exporter: FileExporter):
        assert len(list(exporter.path.glob("hcw*.jsonl"))) == 0
        with exporter:
            assert len(list(exporter.path.glob("hcw*.jsonl"))) == 1

    def test_flush_skipped(self, exporter: FileExporter, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._flush()
        mock.flush.assert_not_called()

    def test_flushed(self, exporter: FileExporter, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = datetime.now() - timedelta(minutes=10)
        exporter._flush()
        mock.flush.assert_called_once()

    def test_repeated_flush_skipped(self, exporter: FileExporter, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = datetime.now() - timedelta(minutes=10)
        exporter._flush()
        exporter._flush()
        mock.flush.assert_called_once()

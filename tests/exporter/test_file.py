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

    @fixture(scope="function")
    def now(self, mocker: MockerFixture) -> datetime:
        # Freeze the exporter's clock mid-day, so the tests are unaffected by the actual date rolling over.
        now = datetime(2026, 1, 1, 12, 0)
        mocker.patch("homeconnect_watcher.exporter.file.datetime").now.return_value = now
        return now

    def test_flush_skipped(self, exporter: FileExporter, now: datetime, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = now
        exporter._flush()
        mock.flush.assert_not_called()

    def test_flushed(self, exporter: FileExporter, now: datetime, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = now - timedelta(minutes=10)
        exporter._flush()
        mock.flush.assert_called_once()

    def test_repeated_flush_skipped(self, exporter: FileExporter, now: datetime, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = now - timedelta(minutes=10)
        exporter._flush()
        exporter._flush()
        mock.flush.assert_called_once()

    def test_reopened_on_date_rollover(self, exporter: FileExporter, now: datetime, mocker: MockerFixture):
        mock = mocker.Mock()
        exporter._fp = mock
        exporter._last_flush = now - timedelta(days=1)
        exporter._flush()
        mock.flush.assert_not_called()
        mock.close.assert_called_once()
        assert exporter._fp is not mock

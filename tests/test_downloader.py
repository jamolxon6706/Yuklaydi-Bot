import pytest
from unittest.mock import MagicMock, patch
from bot.services.downloader import DownloadError, _download_sync


def test_download_error_private():
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        import yt_dlp
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("This video is private")
        mock_ydl_cls.return_value = mock_ydl

        with pytest.raises(DownloadError) as exc_info:
            _download_sync("https://youtu.be/abc", "/tmp/out.mp4", "720")
        assert exc_info.value.kind == "private"


def test_download_error_geo():
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        import yt_dlp
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "not available in your country"
        )
        mock_ydl_cls.return_value = mock_ydl

        with pytest.raises(DownloadError) as exc_info:
            _download_sync("https://youtu.be/abc", "/tmp/out.mp4", "720")
        assert exc_info.value.kind == "geo"


def test_download_error_unsupported():
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        import yt_dlp
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("Unsupported URL")
        mock_ydl_cls.return_value = mock_ydl

        with pytest.raises(DownloadError) as exc_info:
            _download_sync("https://example.com/whatever", "/tmp/out.mp4", "720")
        assert exc_info.value.kind == "unsupported"

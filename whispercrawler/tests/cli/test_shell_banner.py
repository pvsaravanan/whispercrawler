"""Tests for interactive shell startup ordering."""

from whispercrawler import shell as shell_module


class TestBannerOrdering:
    def test_banner_printed_before_shell_starts(self, monkeypatch, capsys):
        """Regression: the banner was written only after start_ipython returned,
        so the user saw it once they had already quit the shell."""
        import IPython

        seen_at_startup = {}

        def fake_start_ipython(argv=None, user_ns=None, display_banner=False):
            # Whatever has been printed by the time the shell starts
            seen_at_startup["stdout"] = capsys.readouterr().out

        monkeypatch.setattr(IPython, "start_ipython", fake_start_ipython)

        shell_module.launch()

        assert "whispercrawler Interactive Shell" in seen_at_startup["stdout"]
        assert "Shortcuts:" in seen_at_startup["stdout"]

    def test_namespace_is_populated(self, monkeypatch):
        import IPython

        captured = {}

        def fake_start_ipython(argv=None, user_ns=None, display_banner=False):
            captured["ns"] = user_ns

        monkeypatch.setattr(IPython, "start_ipython", fake_start_ipython)

        shell_module.launch()

        ns = captured["ns"]
        for name in ("get", "post", "fetch", "ghost_fetch", "shadow_fetch", "view", "curl2crawler"):
            assert name in ns, f"{name} missing from shell namespace"

    def test_banner_markup_is_stripped(self, monkeypatch, capsys):
        import IPython

        monkeypatch.setattr(IPython, "start_ipython", lambda **kw: None)

        shell_module.launch()
        out = capsys.readouterr().out

        assert "[bold cyan]" not in out
        assert "[/bold cyan]" not in out

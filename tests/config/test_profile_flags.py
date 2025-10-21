from __future__ import annotations

from pdf2zh_next.config import ConfigManager


def test_profile_flags_default():
    cm = ConfigManager()
    # simulate empty CLI by parsing with no args/ENV
    settings = cm.initialize_cli_config().to_settings_model()
    assert settings.basic.profile is False
    assert settings.basic.cprofile is False
    assert isinstance(settings.basic.cprofile_topn, int)



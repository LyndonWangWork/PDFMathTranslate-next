from __future__ import annotations

from pdf2zh_next.config.cli_env_model import CLIEnvSettingsModel


def test_profile_flags_default():
    # Use model defaults without parsing current process argv (pytest args)
    settings = CLIEnvSettingsModel().to_settings_model()
    assert settings.basic.profile is False
    assert settings.basic.cprofile is False
    assert isinstance(settings.basic.cprofile_topn, int)



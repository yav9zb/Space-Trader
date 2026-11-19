import os


def test_the_suite_never_points_at_the_developers_real_saves_or_legacy_file():
    from src.legacy import legacy
    from src.save_system import save_system

    real_saves = os.path.abspath("saves")
    assert os.path.abspath(str(save_system.save_directory)) != real_saves
    assert not os.path.abspath(str(save_system.save_directory)).startswith(real_saves + os.sep)
    assert os.path.abspath(legacy._file()) != os.path.abspath("legacy.json")


def test_an_autosave_from_the_real_engine_lands_in_the_isolated_folder(tmp_path):
    from src.engine.game_engine import GameEngine
    from src.save_system import save_system

    engine = GameEngine()
    engine._auto_save()
    assert (save_system.save_directory / "autosave.json").exists()
    assert os.path.abspath(str(save_system.save_directory)) != os.path.abspath("saves")


def test_settings_are_read_from_and_written_to_the_isolated_folder():
    from src.paths import get_user_data_path
    from src.settings import game_settings

    path = get_user_data_path("settings.json")
    assert os.path.abspath(path) != os.path.abspath("settings.json")
    game_settings.save()
    assert os.path.exists(path)

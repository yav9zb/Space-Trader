"""Loads and plays sound effects and music stingers, applying settings volumes."""

import os
import glob
import pygame


SFX_DIR = os.path.join("assets", "audio", "sfx")
MUSIC_DIR = os.path.join("assets", "audio", "music")


class SoundManager:
    """Central place for playing sfx/music. Safe to call even if audio init fails."""

    def __init__(self):
        self.enabled = False
        self.sfx = {}
        self.music = {}
        self.loop_channels = {}  # name -> pygame.mixer.Channel
        self._init_mixer()
        self._load_sounds()

    def _init_mixer(self):
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error as e:
            print(f"Audio disabled: {e}")
            self.enabled = False

    def _load_sounds(self):
        if not self.enabled:
            return

        for path in glob.glob(os.path.join(SFX_DIR, "*.ogg")):
            name = os.path.splitext(os.path.basename(path))[0]
            try:
                self.sfx[name] = pygame.mixer.Sound(path)
            except pygame.error as e:
                print(f"Failed to load sfx {path}: {e}")

        for path in glob.glob(os.path.join(MUSIC_DIR, "*.ogg")):
            name = os.path.splitext(os.path.basename(path))[0]
            try:
                self.music[name] = pygame.mixer.Sound(path)
            except pygame.error as e:
                print(f"Failed to load music {path}: {e}")

        self.apply_volumes()

    def apply_volumes(self):
        """Re-apply current settings volumes to all loaded sounds."""
        if not self.enabled:
            return

        try:
            from ..settings import game_settings
        except ImportError:
            from settings import game_settings

        master = game_settings.master_volume
        sfx_vol = master * game_settings.sfx_volume
        music_vol = master * game_settings.music_volume

        for sound in self.sfx.values():
            sound.set_volume(sfx_vol)
        for sound in self.music.values():
            sound.set_volume(music_vol)

    def play(self, name: str):
        """Play a one-shot sound effect by name (no-op if missing or disabled)."""
        if not self.enabled:
            return
        sound = self.sfx.get(name)
        if sound:
            sound.play()

    def play_music(self, name: str):
        """Play a one-shot music stinger by name."""
        if not self.enabled:
            return
        sound = self.music.get(name)
        if sound:
            sound.play()

    def play_loop(self, name: str):
        """Start looping a sound effect if it isn't already looping."""
        if not self.enabled or name in self.loop_channels:
            return
        sound = self.sfx.get(name)
        if sound:
            channel = sound.play(loops=-1)
            if channel:
                self.loop_channels[name] = channel

    def stop_loop(self, name: str):
        """Stop a looping sound effect if it's playing."""
        channel = self.loop_channels.pop(name, None)
        if channel:
            channel.stop()


# Global sound manager instance
sound_manager = SoundManager()

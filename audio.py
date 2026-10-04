"""Load the four original electronic combat cues once per game."""

from pathlib import Path

import pygame


AUDIO_DIRECTORY = Path(__file__).resolve().parent / "assets" / "audio"
VOLUMES = {"laser": 0.35, "asteroid_hit": 0.6, "player_hit": 0.65, "game_over": 0.7}


class SoundManager:
    def __init__(self):
        self.sounds = {}
        if pygame.mixer.get_init() is None:
            print("Audio unavailable; continuing silently.")
            return
        try:
            pygame.mixer.set_num_channels(16)
            # Critical player feedback cannot be stolen by overlapping impacts.
            pygame.mixer.set_reserved(2)
            for name, volume in VOLUMES.items():
                sound = pygame.mixer.Sound(str(AUDIO_DIRECTORY / f"{name}.wav"))
                sound.set_volume(volume)
                self.sounds[name] = sound
        except (pygame.error, OSError) as error:
            self.sounds.clear()
            print(f"Audio unavailable; continuing silently: {error}")

    def play(self, event):
        sound = self.sounds.get(event)
        if sound is None:
            return
        if event == "game_over":
            pygame.mixer.stop()
            pygame.mixer.Channel(0).play(sound)
        elif event == "player_hit":
            pygame.mixer.Channel(1).play(sound)
        else:
            sound.play()

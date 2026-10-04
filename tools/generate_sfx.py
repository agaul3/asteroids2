"""Deterministic original cyberpunk SFX. No runtime synthesis or dependencies."""

from array import array
import math
from pathlib import Path
import random
import sys
import wave


RATE = 44100
DURATIONS = {"laser": 0.12, "asteroid_hit": 0.35, "player_hit": 0.55, "game_over": 1.4}
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "audio"
TAU = math.tau


def synthesize(name):
    duration = DURATIONS[name]
    rng = random.Random(2077 + list(DURATIONS).index(name))
    samples = []
    phase = bass_phase = sparkle_phase = 0.0
    filtered_noise = held_noise = 0.0
    for index in range(round(RATE * duration)):
        t = index / RATE
        noise = rng.uniform(-1, 1)
        filtered_noise = filtered_noise * 0.88 + noise * 0.12
        if index % 22 == 0:
            held_noise = noise
        if name == "laser":
            frequency = 3400 * math.exp(-22 * t) + 160
            phase += TAU * frequency / RATE
            value = (0.7 * math.sin(phase) + 0.16 * math.sin(phase * 2.03)
                     + 0.22 * held_noise) * math.exp(-30 * t)
        else:
            frequency = (150 if name == "asteroid_hit" else 190) * math.exp(-30 * t) + 45
            bass_phase += TAU * frequency / RATE
            decay = 13 if name == "asteroid_hit" else 9
            kick = math.sin(bass_phase) * math.exp(-decay * t)
            crack = (noise * 0.55 + held_noise * 0.3) * math.exp(-32 * t)
            rumble = filtered_noise * math.exp(-8 * t)
            sparkle_phase += TAU * (2200 * math.exp(-10 * t) + 650) / RATE
            sparkle = math.sin(sparkle_phase) * math.exp(-15 * t)
            if name == "asteroid_hit":
                value = kick * 1.1 + crack + rumble * 0.8 + sparkle * 0.2
            elif name == "player_hit":
                phase += TAU * (780 * math.exp(-7 * t) + 90) / RATE
                shield = math.tanh(2.5 * math.sin(phase)) * math.exp(-7 * t)
                value = kick * 0.9 + crack * 0.9 + rumble + shield * 0.5
            else:
                phase += TAU * (720 * math.exp(-3.5 * t) + 36) / RATE
                shutdown = math.sin(phase) * math.exp(-2.7 * t)
                glitch = held_noise * max(0, 1 - t / 0.85) * (0.4 if int(t * 25) % 3 == 0 else 0.08)
                flatline_envelope = min(1, max(0, (t - 0.85) / 0.06)) * min(1, max(0, (duration - t) / 0.2))
                flatline = math.sin(TAU * 920 * t) * flatline_envelope * 0.3
                value = kick * 1.2 + crack + rumble * 1.2 + shutdown * 0.6 + glitch + flatline
        # Smooth onset and tail avoid digital clicks, including the flatline.
        envelope = min(1, t / 0.002) * min(1, (duration - t) / 0.012)
        samples.append(value * envelope)
    peak = max(abs(value) for value in samples) or 1
    gain = 0.82 / peak
    pcm = array("h")
    for index, value in enumerate(samples):
        # A small stereo delay adds width while keeping a strong centered attack.
        delayed = samples[max(0, index - 75)]
        pcm.extend((round(value * gain * 32767), round((0.88 * value + 0.12 * delayed) * gain * 32767)))
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in DURATIONS:
        with wave.open(str(OUTPUT / f"{name}.wav"), "wb") as file:
            file.setnchannels(2)
            file.setsampwidth(2)
            file.setframerate(RATE)
            file.writeframes(synthesize(name))
        print(f"Generated {name}.wav ({DURATIONS[name]:.2f}s)")


if __name__ == "__main__":
    main()

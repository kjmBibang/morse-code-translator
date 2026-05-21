from __future__ import annotations

import wave
from typing import List, Tuple

import numpy as np


def decode_audio_file(path: str) -> str:
    """Decode a WAV file into a Morse string."""
    samples, sample_rate = _load_wav_mono(path)
    return decode_audio_wave(samples, sample_rate)


def decode_audio_wave(samples: np.ndarray, sample_rate: int) -> str:
    """Decode audio samples into a Morse string."""
    if samples.size == 0 or sample_rate <= 0:
        return ""

    mono = _normalize_audio(samples)
    envelope = _amplitude_envelope(mono, sample_rate)
    if envelope.size == 0:
        return ""

    threshold = _adaptive_threshold(envelope)
    if threshold <= 0:
        return ""

    mask = envelope >= threshold
    runs = _mask_to_runs(mask, sample_rate)
    if not runs:
        return ""

    min_tone = 0.03
    tone_durations = [duration for is_tone, duration in runs if is_tone and duration >= min_tone]
    if not tone_durations:
        return ""

    dot = float(np.percentile(tone_durations, 20))
    dot = max(dot, min_tone)
    dot_dash_boundary = dot * 2.0
    letter_gap = dot * 2.5
    word_gap = dot * 6.0
    min_gap = dot * 0.4

    parts: List[str] = []
    current = ""
    for is_tone, duration in runs:
        if is_tone:
            if duration < min_tone:
                continue
            current += "." if duration < dot_dash_boundary else "-"
            continue

        if not current:
            continue
        if duration >= word_gap:
            parts.append(current)
            current = ""
            if not parts or parts[-1] != "/":
                parts.append("/")
        elif duration >= letter_gap:
            parts.append(current)
            current = ""
        elif duration < min_gap:
            continue

    if current:
        parts.append(current)
    while parts and parts[-1] == "/":
        parts.pop()

    return " ".join(parts)


def _load_wav_mono(path: str) -> Tuple[np.ndarray, int]:
    with wave.open(path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frames = wav_file.readframes(wav_file.getnframes())

    if sample_width == 1:
        data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(frames, dtype=np.dtype("<i2")).astype(np.float32)
        data /= 32768.0
    elif sample_width == 4:
        data = np.frombuffer(frames, dtype=np.dtype("<i4")).astype(np.float32)
        data /= 2147483648.0
    else:
        raise ValueError("Unsupported WAV sample width.")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return data, sample_rate


def _normalize_audio(samples: np.ndarray) -> np.ndarray:
    max_value = float(np.max(np.abs(samples)))
    if max_value <= 0:
        return samples.astype(np.float32)
    return (samples / max_value).astype(np.float32)


def _amplitude_envelope(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    window_size = max(1, int(sample_rate * 0.01))
    kernel = np.ones(window_size, dtype=np.float32) / float(window_size)
    return np.convolve(np.abs(samples), kernel, mode="same")


def _adaptive_threshold(envelope: np.ndarray) -> float:
    low = float(np.percentile(envelope, 10))
    high = float(np.percentile(envelope, 90))
    if high <= 0:
        return 0.0
    return low + (high - low) * 0.5


def _mask_to_runs(mask: np.ndarray, sample_rate: int) -> List[Tuple[bool, float]]:
    if mask.size == 0:
        return []
    changes = np.flatnonzero(mask[1:] != mask[:-1]) + 1
    indices = np.concatenate(([0], changes, [mask.size]))
    runs: List[Tuple[bool, float]] = []
    for start, end in zip(indices[:-1], indices[1:]):
        duration = (end - start) / float(sample_rate)
        runs.append((bool(mask[start]), duration))
    return runs

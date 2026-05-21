import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from audio.beeper import build_morse_wave
from audio.processor import decode_audio_wave
from core import translate


class TestAudioProcessor(unittest.TestCase):
    def test_decode_sos_wave(self) -> None:
        morse = "... --- ..."
        wave, sample_rate = build_morse_wave(morse, 0.1, 1.0)
        decoded_morse = decode_audio_wave(wave, sample_rate)
        decoded_text, _ = translate(decoded_morse, "decode")
        self.assertEqual(decoded_text, "SOS")


if __name__ == "__main__":
    unittest.main()

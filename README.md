# Morse Code Translator

## Setup

1. Create and activate virtual environment:
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .\venv\Scripts\Activate.ps1
     ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run app:
   ```powershell
   python src/main.py
   ```

## Audio Decode (WAV)

- Open a WAV file from File -> Open Audio or the Audio tab.
- Click Decode to extract Morse and translate it using the core decoder.
- Audio preprocessing is intentionally simple: amplitude envelope + threshold, then timing-based dots and dashes.

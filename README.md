## 📄 Documentation

| Document | Download |
|----------|----------|
| Algorithm Flowchart | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/Documentation%20for%20Morse%20Code%20Translator-Algorithm%20Flowchart.jpg) |
| Class Diagram | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/Documentation%20for%20Morse%20Code%20Translator-Class%20Diagram.drawio.png) |
| Decoder Flowchart | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/Documentation%20for%20Morse%20Code%20Translator-Decoder%20flowchart.jpg) |
| Encoder Flowchart | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/Documentation%20for%20Morse%20Code%20Translator-Encoder%20flowchart.jpg) |
| ERD | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/ERD.png) |
| Paper | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/MorseCodeTranslator_Paper.docx) |
| PowerPoint Presentation | [⬇ Download](https://github.com/kjmBibang/morse-code-translator/raw/main/docs/MorseCodeTranslator_Presentation.pptx) |

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

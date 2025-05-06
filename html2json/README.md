# 📄 Html2Json Cog for discord.py

This Discord bot cog allows you to convert **HTML chapters** from [https://prabhupadabooks.com/bg](https://prabhupadabooks.com/bg) into a structured **JSON file**, preserving verse numbers, translations, synonyms, and other elements.

## ✨ Features

- ✅ Accepts `.html` files directly from Prabhupāda’s Bhagavad-gītā website.
- ✅ Extracts:
  - Chapter description
  - Verse numbers and text
  - Synonyms (standardised and cleaned)
  - Translations
  - Titles (e.g. ślokas or subheadings)
- ✅ Outputs a clean, readable `.json` file for further use in apps, studies, or publication pipelines.

---

## 🛠 Installation

1. **Add this modmail-plugin** to your `cogs/` folder or use the command in step 3.
2. **BS4** `beautifulsoup4` is installed automatically via requirements.txt:

```bash
beautifulsoup4
````

3. Load the cog in your bot:

```diff
!plugin add WebKide/modmail-plugins/html2json@master
```

> Adjust the path as needed based on your cog structure.

---

## 🧪 Usage

### ✅ Command:

```
!html2json
```

### 📝 How to Use:

1. Go to: [https://prabhupadabooks.com/bg](https://prabhupadabooks.com/bg)
2. Open any chapter.
3. Save the entire webpage as an `.html` file.
4. Attach it to your message and use the command:

   ```
   !html2json
   ```

### 💡 Example:

```
User: (uploads BG_02.html)
User: !html2json
User: hits Enter
Bot: (uploads BG_02.json with parsed verses)
```

---

## 📁 Output Format (JSON)

```json
{
  "Chapter-Desc": "The Supreme Personality of Godhead said...",
  "Verses": [
    {
      "Textnum": "2.1",
      "Titles": "Śrī Bhagavān uvāca",
      "Uvaca-line": "śrī-bhagavān uvāca",
      "Synonyms-SA": "śrī-bhagavān — the Supreme Personality of Godhead; uvāca — said...",
      "Verse-Text": "saṅjaya uvāca...\nkṛipayā parayāviṣṭo...",
      "Translation": "Sañjaya said: Seeing Arjuna full of compassion..."
    },
    ...
  ]
}
```

---

## 🧩 Dependencies

* [`discord.py`](https://pypi.org/project/discord.py/) (v2.x)
* [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

---

## 👨‍💻 Developer Notes

* **Filename Check**: Only accepts `.html` files.
* **Safe Parsing**: Filters empty elements and whitespace.
* **Cleaning Logic**: Normalises hyphens, em-dashes, and punctuation in Sanskrit synonyms and translations.
* **Output Handling**: JSON is returned as a downloadable file directly in the Discord chat.

---

## 🙏 Credits

Developed for parsing and preserving the teachings of **Śrīla A.C. Bhaktivedānta Swāmī Prabhupāda** from *Bhagavad-gītā As It Is* in a structured data format.

---

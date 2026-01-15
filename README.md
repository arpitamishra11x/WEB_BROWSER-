```markdown
PyBrowser — minimal web browser in Python (PyQt)

What this is!!
- A small multi-tab web browser built with PyQt5 + QtWebEngine.
- Useful as a learning project or starting point for a custom browser.

Files~
- main.py         # the browser application
- requirements.txt

Requirements~
- Python 3.8+
- pip

Install~
1) Create and activate a virtual environment (recommended):

PowerShell (Windows)~
```powershell
cd "C:\path\to\project"
py -3 -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

📌 Features

✔ Multi-tab browsing
✔ URL bar with smart search handling
✔ Back, Forward, Reload, Stop, Home navigation
✔ Bookmark management with persistent storage
✔ Load local HTML files
✔ Save web pages as HTML
✔ Keyboard shortcuts for faster navigation
✔ Status bar with loading progress
✔ Confirmation dialogs for tab and app closing.

🛠️ Technologies Used

-Programming Language: Python 3
-GUI Framework: PyQt5
-Web Rendering Engine: Qt WebEngine
-Data Storage: JSON (for bookmarks)

🧭 Application Overview
🔹 Main Window
Displays tabs, toolbar, menu bar, and status bar
Supports multiple open web pages simultaneously

🔹 Navigation Toolbar
Includes buttons for:
Back
Forward
Reload
Stop loading
Home
New Tab
Bookmark current page

🔹 URL/Search Bar
Enter a full URL (e.g., https://example.com)
Or type keywords to perform a Google search automatically

🔹 Tabs
Each tab loads a webpage independently
Duplicate URLs are prevented from opening twice
Tabs show page title and favicon

⭐ Bookmarks System

Bookmarks are saved in a bookmarks.json file
Each bookmark stores:
Page title
Page URL
Bookmarks persist even after closing the browser
Duplicate bookmarks are prevented

# 🧘‍♀️ FocusWell — Wellness Assistant

*FocusWell* is a desktop wellness assistant that helps you focus better, keep hydrated,
and manage daily tasks — built with **Python** and **Tkinter**.

## 🚀 Features
- Pomodoro-style focus timer (start / pause / reset)
- Hydration goal & quick add (+1 glass)
- Daily planner with due dates & times
- Persistent local settings and SQLite storage
- Clean Tkinter UI and unit tests with `pytest`

## 🧱 Project Structure
```text
core/         → App settings, DB connection, event loop
features/     → focus, hydration, planner modules
ui/           → windows/tabs/widgets
tests/        → unit tests (pytest)
.vscode/      → editor configuration for pytest discovery
```

## 🧪 Run tests
```bash
python -m pytest -q
```
In Visual Studio Code, tests appear under the **Testing** panel when the interpreter is set to the project `.venv`.

## ⚙️ Setup
```bash
# 1) Create & activate virtual environment
py -3.13 -m venv .venv
.venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run app
python main.py
```

## 🧰 Requirements
See [`requirements.txt`](requirements.txt).  (The app primarily uses the Python standard library.
Optional GUI deps like `tkcalendar` or `customtkinter` can be added if you enable those views.)

---

## 👤 Author
**Tilemachos Bouris** 

## 📜 License
Released under the MIT License. See [`LICENSE`](LICENSE).

## Env details
- Python 3.9.4

## Set up project
- `python -m venv myvenv`
- `source ./myvenv/bin/activate` (On *nix)
    - `.\myvenv\Scripts\activate.bat` (On Windows)
- `pip install -r requirements.txt`
- For now, manually add the user name in `grader.py` and set the platforms to scan in `PLATFORMS` array in the same python file.
    - Also, for the sake of testing the grader, I've manually added a time delta of -7 days to test last week's submissions. But that's configurable too in `grader.py`
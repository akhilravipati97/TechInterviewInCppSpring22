## Env details
- Python 3.9.4

## Set up project
- `python -m venv myvenv`
- `source ./myvenv/bin/activate` (On *nix)
    - `.\myvenv\Scripts\activate.bat` (On Windows)
- `pip install -r requirements.txt`

## Initialize values
- Download [chromedriver]( https://chromedriver.chromium.org/downloads) and set its path in `constants.py`
- Create a cache directory for storing preprocessing results and grades. Set its path in `constant.py`
- Obtain a local copy of the form 1 responses (with user handles) and place it in the cache directory.


## Running the grader
- Run the preprocessor first: `python3 preprocessor.py -w <week_num>` 
    - This can take up to ~30min-1hr.
- Run the grader next: `python3 grader.py -w <week_num>`
    - It will store grades in `/path/to/cache/dir/grades_<week_num>.csv`.

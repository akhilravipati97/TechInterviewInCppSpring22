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
- Copy `handles.csv` from the shared drive location and place it in the cache directory.
- Create a `logs` directory in the project root if you wish the logger to auto spool to a log file along with console.


## Running the grader
- Remember to activate the virtual env (see setup)
- Run the preprocessor first: `python3 preprocessor.py -w <week_num>` 
    - This can take up to ~30min-1hr.
    - If someone's already done this, they can share the preprocessing cache files to avoid waiting.
- Run the grader next: `python3 grader.py -w <week_num>`
    - It will store grading events in `/path/to/cache/dir/grade_<week_num>.log`.
- Run the calculator/assimilator next: `python3 calculate_points.py -w <week_num>`
    - It will store the grades/points in `/path/to/cache/dir/grades_<week_num>.csv`

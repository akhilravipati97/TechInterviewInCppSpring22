## Env details
- Python 3.9.4

## Set up project
- `python -m venv myvenv`
- `source ./myvenv/bin/activate` (On *nix)
    - `.\myvenv\Scripts\activate.bat` (On Windows)
- `pip install -r requirements.txt`

## Initialize values
- Download [chromedriver]( https://chromedriver.chromium.org/downloads) and set its path in `constants.py`
    - You may be required to upgrade the driver to a newer version from time to time (there'll be errors indicating that)
- Create a cache directory for storing preprocessing results and grades. Set its path in `constant.py`
- Copy `handles.csv` from the shared drive location and place it in the cache directory.
    - This csv file contains each student's names, unis, and each of their coding platform/website handles.
- Create a `logs` directory in the project root if you wish the logger to spool to a log file. Either way the grader will still print stuff to the console.


## Running the grader
- Remember to activate the virtual env (see setup)
- Run the preprocessor first: `python3 preprocessor.py -w <week_num>` 
    - This can take up to ~30min-1hr.
    - If someone's already done this, they can share the preprocessing cache files to avoid waiting.
- Run the grader next: `python3 grader.py -w <week_num>`
    - It will store grading events in `/path/to/cache/dir/grading_events_<week_num>.log`.
- Run the calculator/assimilator next: `python3 calculate_points.py -w <week_num>`
    - It will store the grades/points in `/path/to/cache/dir/grades_<week_num>.csv`
- After all grades in `grades_<week_num>.csv` are finalized i.e. `final_points` column's filled (perhaps after a manual comparison with code/screenshots submitted by students), download/export the gradebook from courseworks and then run the populate gradebook script: `python3 populate_gradebook.py -w <week_num> -c /path/to/courseworks/exported/gradebook.csv -g /path/to/finalized/grades_<week_num>.csv -o /path/to/output/coursworks/import/gradebook.csv`
    - The `-o` option is going to be the new file that the script will create which can be directly uploaded/imported on courseworks to update assignment scores.
- **NOTE**:
    - The grader can be run for a single person and/or a single platform using `python3 grader.py -w <week_num> -u <uni> -p <platform_name_used_in_code>`. This is very useful to crosscheck certain scores (if code/screenshots differ from what the grader calculated)


## Current Shortcomings
- **Leetcode** Practice problem points cannot be calculated by auto-grader because Leetcode does not show all submissions made by a user.
- **Topcoder** Contest and practice problems points are not auto-calculated yet. It was too complicated too code and I thought we should only put efforts if we see enough student submissions for Topcoder.
- **Kattis** Practice problem points cannot be calculated by auto-grader because Kattis does not show submissions made by a user at all.

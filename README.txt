STUDENT PRODUCTIVITY ASSISTANT (Python + C++)

FILES
- main.py: main application (assignments, deadlines, study goals, summaries)
- task_sorter.cpp: C++ module that sorts pending tasks by priority and deadline
- run_project.bat: quick launcher for Windows

REQUIREMENTS
1. Python 3 installed and available as the `python` command.
2. A C++ compiler with g++ installed and available in PATH (for example, MinGW-w64/MSYS2).
3. Visual Studio Code is recommended.

RUN IN VS CODE
1. Extract this folder.
2. Open the folder in VS Code: File > Open Folder.
3. Open Terminal > New Terminal.
4. Run: python main.py
   Or, on Windows, double-click run_project.bat.
5. The program compiles task_sorter.cpp automatically when task sorting is needed.

IMPORTANT
- Keep main.py and task_sorter.cpp in the same folder.
- If g++ is not installed, the program will still work using Python's sorting fallback.
- Tasks and study goals are saved in student_data.json, created automatically in this folder.
- Enter deadlines in YYYY-MM-DD format, for example 2026-10-25.

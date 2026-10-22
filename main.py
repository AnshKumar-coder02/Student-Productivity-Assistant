import json
import os
import subprocess
import sys
from datetime import datetime, date

DATA_FILE = "student_data.json"
CPP_SOURCE = "task_sorter.cpp"
CPP_EXE = "task_sorter.exe" if os.name == "nt" else "task_sorter"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "goals": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("tasks", [])
        data.setdefault("goals", [])
        return data
    except (json.JSONDecodeError, OSError):
        print("Warning: Could not read saved data. Starting with empty data.")
        return {"tasks": [], "goals": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def valid_date(prompt):
    while True:
        value = input(prompt).strip()
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("Please enter a date in YYYY-MM-DD format, for example 2026-10-25.")

def compile_cpp():
    if not os.path.exists(CPP_SOURCE):
        print(f"Missing {CPP_SOURCE}. Put it in the same folder as main.py.")
        return False
    compiler = "g++"
    try:
        result = subprocess.run(
            [compiler, CPP_SOURCE, "-std=c++17", "-O2", "-o", CPP_EXE],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            print("Could not compile the C++ module.")
            print(result.stderr.strip() or "Check that a C++ compiler (g++) is installed.")
            return False
        return True
    except FileNotFoundError:
        print("C++ compiler g++ was not found.")
        print("Install MinGW-w64/MSYS2 with g++, or use the Python sorting fallback.")
        return False

def sorted_tasks(tasks):
    # Use the C++ module when available. Fall back to Python if compilation fails.
    pending = [t for t in tasks if not t.get("completed", False)]
    completed = [t for t in tasks if t.get("completed", False)]
    if pending and compile_cpp():
        # Pass tasks through stdin as simple tab-separated rows to avoid extra libraries.
        lines = []
        for t in pending:
            title = t["title"].replace("\t", " ").replace("\n", " ")
            due = t["due"]
            # C++ sorter expects numeric priorities: High=1, Medium=2, Low=3.
            priority = {"High": 1, "Medium": 2, "Low": 3}.get(t.get("priority", "Medium"), 2)
            lines.append(f"{priority}\t{due}\t{t['id']}\t{title}")
        try:
            result = subprocess.run(
                [os.path.abspath(CPP_EXE)],
                input="\n".join(lines) + "\n",
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                ids = []
                for line in result.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        ids.append(parts[2])
                by_id = {t["id"]: t for t in pending}
                if len(ids) == len(pending) and all(i in by_id for i in ids):
                    return [by_id[i] for i in ids] + completed
        except OSError:
            pass
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    pending.sort(key=lambda t: (priority_rank.get(t["priority"], 3), t["due"], t["id"]))
    return pending + completed

def next_id(items):
    return str(max([int(x.get("id", 0)) for x in items] + [0]) + 1)

def add_task(data):
    print("\n--- Add Assignment / Task ---")
    title = input("Task title: ").strip()
    if not title:
        print("Task title cannot be empty.")
        return
    subject = input("Subject (e.g., Operating Systems): ").strip() or "General"
    due = valid_date("Deadline (YYYY-MM-DD): ")
    print("Priority: 1. High  2. Medium  3. Low")
    priority_choice = input("Choose priority [1-3]: ").strip()
    priority = {"1": "High", "2": "Medium", "3": "Low"}.get(priority_choice)
    if not priority:
        print("Invalid choice; priority set to Medium.")
        priority = "Medium"
    data["tasks"].append({
        "id": next_id(data["tasks"]),
        "title": title,
        "subject": subject,
        "due": due,
        "priority": priority,
        "completed": False,
        "created": date.today().isoformat()
    })
    save_data(data)
    print("Task saved successfully.")

def view_tasks(data, show_all=True):
    tasks = sorted_tasks(data["tasks"])
    if not show_all:
        tasks = [t for t in tasks if not t.get("completed", False)]
    if not tasks:
        print("\nNo tasks to show.")
        return
    today = date.today()
    print("\n--- Your Tasks (priority/deadline order) ---")
    for t in tasks:
        status = "COMPLETED" if t.get("completed") else "PENDING"
        try:
            due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
            if not t.get("completed") and due_date < today:
                status = "OVERDUE"
            days = (due_date - today).days
            due_note = "due today" if days == 0 else (f"{abs(days)} day(s) overdue" if days < 0 else f"in {days} day(s)")
        except (ValueError, KeyError):
            due_note = ""
        print(f'[{t["id"]}] {t["title"]}')
        print(f'    Subject: {t.get("subject", "General")} | Priority: {t.get("priority", "Medium")}')
        print(f'    Deadline: {t["due"]} ({due_note}) | Status: {status}')

def complete_task(data):
    view_tasks(data)
    task_id = input("\nEnter the task ID to mark complete: ").strip()
    for task in data["tasks"]:
        if task["id"] == task_id:
            if task.get("completed"):
                print("This task is already completed.")
            else:
                task["completed"] = True
                save_data(data)
                print("Great work! Task marked as completed.")
            return
    print("Task ID not found.")

def delete_task(data):
    view_tasks(data)
    task_id = input("\nEnter the task ID to delete: ").strip()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            confirm = input(f'Delete "{task["title"]}"? (y/n): ').strip().lower()
            if confirm == "y":
                data["tasks"].pop(i)
                save_data(data)
                print("Task deleted.")
            else:
                print("Delete cancelled.")
            return
    print("Task ID not found.")

def add_goal(data):
    print("\n--- Add Daily Study Goal ---")
    title = input("Study goal (e.g., Revise Unit 2): ").strip()
    if not title:
        print("Goal cannot be empty.")
        return
    minutes_text = input("Target study time in minutes: ").strip()
    try:
        minutes = int(minutes_text)
        if minutes <= 0:
            raise ValueError
    except ValueError:
        print("Please enter a positive whole number.")
        return
    data["goals"].append({
        "id": next_id(data["goals"]),
        "title": title,
        "minutes": minutes,
        "date": date.today().isoformat(),
        "completed": False
    })
    save_data(data)
    print("Study goal saved.")

def view_goals(data):
    goals = data["goals"]
    if not goals:
        print("\nNo study goals yet.")
        return
    print("\n--- Study Goals ---")
    for g in goals:
        status = "DONE" if g.get("completed") else "PENDING"
        print(f'[{g["id"]}] {g["title"]} — {g["minutes"]} minutes — {g["date"]} — {status}')

def complete_goal(data):
    view_goals(data)
    goal_id = input("\nEnter the goal ID to mark complete: ").strip()
    for goal in data["goals"]:
        if goal["id"] == goal_id:
            goal["completed"] = True
            save_data(data)
            print("Study goal marked complete.")
            return
    print("Goal ID not found.")

def show_summary(data):
    tasks = data["tasks"]
    goals = data["goals"]
    pending = sum(not t.get("completed", False) for t in tasks)
    completed = sum(t.get("completed", False) for t in tasks)
    overdue = 0
    today = date.today()
    for t in tasks:
        if not t.get("completed", False):
            try:
                overdue += datetime.strptime(t["due"], "%Y-%m-%d").date() < today
            except ValueError:
                pass
    goal_done = sum(g.get("completed", False) for g in goals)
    goal_pending = len(goals) - goal_done
    print("\n========== PRODUCTIVITY SUMMARY ==========")
    print(f"Total tasks: {len(tasks)}")
    print(f"Pending tasks: {pending}")
    print(f"Completed tasks: {completed}")
    print(f"Overdue tasks: {overdue}")
    print(f"Study goals: {len(goals)} (completed: {goal_done}, pending: {goal_pending})")
    print("==========================================")

def menu():
    data = load_data()
    while True:
        print("\n" + "=" * 48)
        print("       STUDENT PRODUCTIVITY ASSISTANT")
        print("=" * 48)
        print("1. Add assignment/task")
        print("2. View all tasks (sorted by priority)")
        print("3. View pending tasks")
        print("4. Mark task as completed")
        print("5. Delete a task")
        print("6. Add daily study goal")
        print("7. View study goals")
        print("8. Mark study goal as completed")
        print("9. View productivity summary")
        print("0. Save and exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_task(data)
        elif choice == "2":
            view_tasks(data)
        elif choice == "3":
            view_tasks(data, show_all=False)
        elif choice == "4":
            complete_task(data)
        elif choice == "5":
            delete_task(data)
        elif choice == "6":
            add_goal(data)
        elif choice == "7":
            view_goals(data)
        elif choice == "8":
            complete_goal(data)
        elif choice == "9":
            show_summary(data)
        elif choice == "0":
            save_data(data)
            print("Your data is saved. Keep learning and good luck!")
            break
        else:
            print("Invalid choice. Please select a number from 0 to 9.")

if __name__ == "__main__":
    menu()

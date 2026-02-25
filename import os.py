import os
import random
import subprocess
from datetime import datetime, timedelta

# Create a dummy file to modify
FILE_NAME = "data.txt"

def make_commits(num_commits):
    # Calculate the start of the current week (e.g., Monday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    for i in range(num_commits):
        # Generate a random time within this week
        random_days = random.randint(0, 6)
        random_hours = random.randint(0, 23)
        random_mins = random.randint(0, 59)
        
        commit_date = start_of_week + timedelta(days=random_days, hours=random_hours, minutes=random_mins)
        formatted_date = commit_date.strftime('%Y-%m-%dT%H:%M:%S')

        # Modify the file
        with open(FILE_NAME, "w") as file:
            file.write(f"Commit data: {formatted_date}\n")

        # Stage and commit using subprocess with the manipulated date
        subprocess.run(["git", "add", FILE_NAME])
        subprocess.run(
            ["git", "commit", "-m", f"Commit {i+1}"],
            env={**os.environ, "GIT_AUTHOR_DATE": formatted_date, "GIT_COMMITTER_DATE": formatted_date}
        )

    # Push all commits at once at the very end
    print(f"Created {num_commits} commits locally. Pushing to remote...")
    subprocess.run(["git", "push", "origin", "main"])

# Run the function for 10,000 commits
make_commits(10000)
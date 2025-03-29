import json
from datetime import datetime

def difficulty_cycle(i):
    # Cycle through difficulties based on the problem number
    if i % 3 == 1:
        return "Easy"
    elif i % 3 == 2:
        return "Medium"
    else:
        return "Hard"

problems = []

# Predefined detailed problems for pk 1 to 5
problems.append({
  "model": "problems.problem",
  "pk": 1,
  "fields": {
    "title": "Sum of Two Numbers",
    "description": "Given two non-negative integers separated by a space, return their sum. This problem tests basic arithmetic operations and input parsing skills.",
    "constraints": "Both numbers will be between 0 and 1000.",
    "sample_input": "2 3",
    "sample_output": "5",
    "difficulty": "Easy",
    "created_at": "2025-03-29T00:00:00Z"
  }
})
problems.append({
  "model": "problems.problem",
  "pk": 2,
  "fields": {
    "title": "Reverse a String",
    "description": "Given a string consisting of alphabets, return the reversed string. This problem tests your string manipulation skills.",
    "constraints": "The string will contain only lowercase alphabets.",
    "sample_input": "hello",
    "sample_output": "olleh",
    "difficulty": "Easy",
    "created_at": "2025-03-29T00:00:00Z"
  }
})
problems.append({
  "model": "problems.problem",
  "pk": 3,
  "fields": {
    "title": "Find Maximum Element",
    "description": "Given a list of integers separated by spaces, return the maximum element in the list. This problem tests your ability to iterate over a collection and compare values.",
    "constraints": "The list will contain between 1 and 100 integers, each between -1000 and 1000.",
    "sample_input": "3 5 2 9 1",
    "sample_output": "9",
    "difficulty": "Medium",
    "created_at": "2025-03-29T00:00:00Z"
  }
})
problems.append({
  "model": "problems.problem",
  "pk": 4,
  "fields": {
    "title": "Check Palindrome",
    "description": "Given a string, determine whether it is a palindrome (reads the same backward as forward). This problem tests your string manipulation and logical reasoning.",
    "constraints": "The string will be between 1 and 100 characters long and contain only alphanumeric characters.",
    "sample_input": "racecar",
    "sample_output": "True",
    "difficulty": "Easy",
    "created_at": "2025-03-29T00:00:00Z"
  }
})
problems.append({
  "model": "problems.problem",
  "pk": 5,
  "fields": {
    "title": "Fibonacci Sequence",
    "description": "Given an integer n, return the nth Fibonacci number. The sequence starts with 0 and 1, and each subsequent number is the sum of the previous two numbers.",
    "constraints": "n will be between 1 and 30.",
    "sample_input": "7",
    "sample_output": "13",
    "difficulty": "Medium",
    "created_at": "2025-03-29T00:00:00Z"
  }
})

# Generate additional problems from pk 6 to 100 with generic but detailed descriptions
for i in range(6, 101):
    problem = {
        "model": "problems.problem",
        "pk": i,
        "fields": {
            "title": f"Problem #{i}",
            "description": (
                f"Detailed description for Problem #{i}: Solve the following challenge to test your programming skills. "
                f"In this problem, you are required to implement an algorithm that processes input data and returns the correct output based on specified constraints."
            ),
            "constraints": (
                f"Constraints for Problem #{i}: The input will be provided as a space-separated string of integers. "
                f"Each integer will be in the range of 1 to 1000. Your solution should handle edge cases and be optimized for performance."
            ),
            "sample_input": f"{i} {i+1}",
            "sample_output": f"{2*i+1}",  # Dummy calculation for sample output
            "difficulty": difficulty_cycle(i),
            "created_at": "2025-03-29T00:00:00Z"
        }
    }
    problems.append(problem)

# Write the fixture to a JSON file
with open("problems_fixture.json", "w") as f:
    json.dump(problems, f, indent=2)

print(f"Generated problems_fixture.json with {len(problems)} problems.")

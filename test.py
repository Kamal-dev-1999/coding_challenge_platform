import json
import re

# Define a mapping for known titles
title_mapping = {
    "Sum of Two Numbers": "Two Sum: Simple Addition",
    "Reverse a String": "Reverse String: Leet Edition",
    "Find Maximum Element": "Maximum Element Finder",
    "Check Palindrome": "Palindrome Checker",
    "Fibonacci Sequence": "Nth Fibonacci Number"
}

def generate_catchy_title(old_title, description, pk):
    # If the title is one of the known ones, return the mapped title
    if old_title in title_mapping:
        return title_mapping[old_title]
    
    # For generic titles like "Problem #6", extract the number
    m = re.match(r"Problem\s*#\s*(\d+)", old_title, re.IGNORECASE)
    if m:
        num = m.group(1)
        return f"Algorithm Challenge #{num}: Conquer the Code"
    
    # Otherwise, try to use some keywords from the description
    description_lower = description.lower()
    if "sum" in description_lower:
        return "Two Sum: Simple Addition"
    elif "reverse" in description_lower:
        return "Reverse String: Leet Edition"
    elif "maximum" in description_lower:
        return "Maximum Element Finder"
    elif "palindrome" in description_lower:
        return "Palindrome Checker"
    elif "fibonacci" in description_lower:
        return "Nth Fibonacci Number"
    
    # Fallback: use the original title
    return old_title

def update_titles_in_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Iterate over each problem and update the title
    for entry in data:
        fields = entry.get("fields", {})
        old_title = fields.get("title", "")
        description = fields.get("description", "")
        pk = entry.get("pk")
        new_title = generate_catchy_title(old_title, description, pk)
        fields["title"] = new_title  # Replace the title with the catchy title
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated titles have been written to {output_file}")

if __name__ == "__main__":
    input_filename = "ip/problems_fixture.json"
    output_filename = "problems_fixture_updated.json"
    update_titles_in_file(input_filename, output_filename)

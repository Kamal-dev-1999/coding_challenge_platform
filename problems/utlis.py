import json

def parse_value(value_str):
    """
    Attempt to parse a string value:
      - If it looks like JSON (starts with [ or {), try to load it.
      - Otherwise, split by whitespace and convert numeric values if possible.
    If the result is a list with a single element, return that element.
    """
    value_str = value_str.strip()
    if value_str and value_str[0] in ['[', '{']:
        try:
            return json.loads(value_str)
        except Exception:
            pass
    parts = value_str.split()
    converted = []
    for part in parts:
        try:
            # Try converting to an integer or float.
            if '.' in part:
                converted.append(float(part))
            else:
                converted.append(int(part))
        except ValueError:
            # If conversion fails, keep as string.
            converted.append(part)
    if len(converted) == 1:
        return converted[0]
    return converted

def evaluate_submission(user_code, problem):
    """
    Evaluate the submitted code against a problem's sample test.
    This function now supports various input and output types,
    including booleans. If the expected output is the string "True"
    or "False", it is converted to a boolean for comparison.
    
    WARNING: Using exec is very dangerous. This is for demonstration only.
    """
    try:
        # Create a safe local environment for exec
        local_env = {}
        exec(user_code, {}, local_env)
        if 'solution' not in local_env:
            return "Runtime Error", "Your code must define a function called 'solution'."
        solution_func = local_env['solution']
        
        # Parse sample input and expected output using our helper
        input_data = parse_value(problem.sample_input)
        expected = parse_value(problem.sample_output)
        
        # Convert expected to a boolean if it is a string representation of a boolean.
        if isinstance(expected, str) and expected.lower() in ['true', 'false']:
            expected = expected.lower() == 'true'
        
        # Execute the solution function:
        # If input_data is a list or tuple, pass it as arguments.
        if isinstance(input_data, (list, tuple)):
            result = solution_func(*input_data)
        else:
            result = solution_func(input_data)
        
        # If result is boolean and expected is boolean, compare directly.
        if isinstance(result, bool) and isinstance(expected, bool):
            if result == expected:
                return "Accepted", f"Output: {result}"
            else:
                return "Wrong Answer", f"Your output: {result} | Expected: {expected}"
        
        # Otherwise, compare directly.
        if result == expected:
            return "Accepted", f"Output: {result}"
        else:
            return "Wrong Answer", f"Your output: {result} | Expected: {expected}"
    except Exception as e:
        return "Runtime Error", str(e)

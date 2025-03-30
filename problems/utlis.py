import json
import time
import sys
import traceback
import io
import platform
from contextlib import redirect_stdout
import threading
import multiprocessing
import signal
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Check if we're on a Unix-like system that supports the resource module
IS_UNIX = platform.system() in ("Linux", "Darwin", "FreeBSD")
if IS_UNIX:
    import resource
else:
    # Windows alternative (with limited functionality)
    pass

# Constants for execution limits
DEFAULT_TIME_LIMIT = 1.0  # seconds
DEFAULT_MEMORY_LIMIT = 512 * 1024 * 1024  # 512 MB in bytes
MAX_OUTPUT_LENGTH = 10000  # Maximum length of output to capture

class TimeoutException(Exception):
    """Exception raised when code execution times out."""
    pass

class MemoryLimitExceededException(Exception):
    """Exception raised when code execution exceeds memory limits."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Code execution timed out")

def memory_limit_handler(signum, frame):
    """Signal handler for memory limits."""
    raise MemoryLimitExceededException("Memory limit exceeded")

def set_memory_limit(limit_bytes: int) -> None:
    """
    Set the memory limit for the current process.
    Only works on Unix-like systems.
    """
    if IS_UNIX:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except (ValueError, resource.error):
            # If setting the limit fails, we'll continue without it
            pass
    else:
        # On Windows, we can't easily set memory limits
        # Instead, we'll just log that this feature is not available
        # print("Memory limits not supported on Windows")
        pass

def parse_value(value_str: str) -> Any:
    """
    Parse a string value into a Python object:
    - JSON arrays/objects
    - Lists of values (split by whitespace)
    - Individual values (int, float, string, bool)
    - Special handling for matrices and graphs

    Args:
        value_str: The string to parse
    
    Returns:
        Parsed Python object
    """
    value_str = value_str.strip()
    
    # Empty string handling
    if not value_str:
        return None
    
    # Boolean handling
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False
    
    # Try to parse as JSON
    if value_str and value_str[0] in ['[', '{']:
        try:
            return json.loads(value_str)
        except Exception:
            pass
    
    # Look for matrix pattern (multiple lines with same delimiter pattern)
    lines = value_str.strip().split('\n')
    if len(lines) > 1:
        # Check if this might be a matrix
        delimiter = None
        for char in [',', ' ', '\t']:
            if all(char in line for line in lines):
                delimiter = char
                break
        
        if delimiter:
            try:
                matrix = []
                for line in lines:
                    row = []
                    for item in line.split(delimiter):
                        item = item.strip()
                        if not item:
                            continue
                        try:
                            if '.' in item:
                                row.append(float(item))
                            else:
                                row.append(int(item))
                        except ValueError:
                            row.append(item)
                    if row:  # Only add non-empty rows
                        matrix.append(row)
                if matrix:
                    return matrix
            except Exception:
                pass
    
    # Check for graph representation (edge list format)
    if '\n' in value_str and re.search(r'\d+\s*[,-]\s*\d+', value_str):
        try:
            edges = []
            for line in value_str.strip().split('\n'):
                if not line.strip():
                    continue
                # Try to parse edges in format "1-2" or "1,2" or "1 2"
                match = re.search(r'(\d+)\s*[,-]\s*(\d+)', line)
                if match:
                    edges.append((int(match.group(1)), int(match.group(2))))
            if edges:
                return {"type": "graph", "edges": edges}
        except Exception:
            pass
    
    # Split by whitespace for standard input
    parts = value_str.split()
    converted = []
    for part in parts:
        try:
            # Try converting to an integer or float
            if '.' in part:
                converted.append(float(part))
            else:
                converted.append(int(part))
        except ValueError:
            # If conversion fails, keep as string
            converted.append(part)
    
    # Return single element if there's only one
    if len(converted) == 1:
        return converted[0]
    
    return converted

def safe_exec(code: str, inputs: Any, time_limit: float = DEFAULT_TIME_LIMIT, 
              memory_limit: int = DEFAULT_MEMORY_LIMIT) -> Tuple[Any, str, float, bool, str]:
    """
    Safely execute user code with proper isolation, timeout, and memory limits.
    
    Args:
        code: User's code to execute
        inputs: Parsed input data
        time_limit: Maximum execution time in seconds
        memory_limit: Maximum memory usage in bytes
    
    Returns:
        Tuple of (result, stdout, execution_time, success, error)
    """
    # Create a pipe for IPC between parent and child process
    parent_conn, child_conn = multiprocessing.Pipe()
    
    # Prepare the input data
    if not isinstance(inputs, (list, tuple)):
        inputs = [inputs]
    
    def run_code():
        try:
            # Set memory limit (only on Unix)
            set_memory_limit(memory_limit)
            
            # Redirect stdout to capture print statements
            captured_output = io.StringIO()
            
            start_time = time.time()
            
            # Execute the code in a safe environment
            local_env = {}
            with redirect_stdout(captured_output):
                exec(code, {"__builtins__": __builtins__}, local_env)
            
            # Check if the solution function exists
            if 'solution' not in local_env:
                child_conn.send((None, "", time.time() - start_time, False, 
                                "Your code must define a function called 'solution'."))
                return
            
            # Execute the solution function
            solution_func = local_env['solution']
            result = solution_func(*inputs)
            
            execution_time = time.time() - start_time
            stdout = captured_output.getvalue()
            
            # Limit the stdout length to prevent overwhelming the system
            if len(stdout) > MAX_OUTPUT_LENGTH:
                stdout = stdout[:MAX_OUTPUT_LENGTH] + "... (output truncated)"
            
            child_conn.send((result, stdout, execution_time, True, None))
        except TimeoutException:
            child_conn.send((None, "", time_limit, False, "Time limit exceeded"))
        except MemoryLimitExceededException:
            child_conn.send((None, "", time.time() - start_time, False, "Memory limit exceeded"))
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            child_conn.send((None, "", time.time() - start_time, False, f"Runtime Error: {error_msg}\n{tb}"))
    
    # Run the code in a separate process for isolation
    process = multiprocessing.Process(target=run_code)
    process.start()
    
    # Wait for the process to complete or timeout
    process.join(time_limit)
    
    # Check if the process is still running after the timeout
    if process.is_alive():
        process.terminate()
        process.join()
        return None, "", time_limit, False, "Time limit exceeded"
    
    # Get the result
    if parent_conn.poll():
        result, stdout, execution_time, success, error = parent_conn.recv()
        return result, stdout, execution_time, success, error
    
    return None, "", time_limit, False, "Execution failed"

def compare_outputs(result: Any, expected: Any, problem_type: str = "standard") -> Tuple[bool, str]:
    """
    Compare the result with the expected output based on problem type.
    
    Args:
        result: The actual result from user's code
        expected: The expected correct result
        problem_type: Type of problem for specialized comparisons
    
    Returns:
        Tuple of (is_correct, explanation)
    """
    if problem_type == "approximate":
        # For problems requiring approximate comparison (floating point)
        if isinstance(result, (int, float)) and isinstance(expected, (int, float)):
            # Allow small differences in floating point results
            epsilon = 1e-6
            if abs(result - expected) < epsilon:
                return True, f"Output: {result} (within epsilon of {expected})"
            else:
                return False, f"Your output: {result} | Expected: {expected} (difference exceeds epsilon)"
    
    elif problem_type == "unordered_array":
        # For problems where the order of elements doesn't matter
        if isinstance(result, list) and isinstance(expected, list):
            if sorted(result) == sorted(expected):
                return True, f"Output: {result} (matches expected elements)"
            else:
                return False, f"Your output: {result} | Expected: {expected} (elements don't match)"
    
    elif problem_type == "graph":
        # For graph problems, we might need to compare different representations
        if isinstance(result, dict) and isinstance(expected, dict):
            # Compare specific graph properties
            if result.get("type") == "graph" and expected.get("type") == "graph":
                result_edges = sorted(result.get("edges", []))
                expected_edges = sorted(expected.get("edges", []))
                if result_edges == expected_edges:
                    return True, f"Output: Graph with edges {result_edges}"
                else:
                    return False, f"Your output: Graph with edges {result_edges} | Expected: {expected_edges}"
    
    # Default comparison for most problem types
    if result == expected:
        return True, f"Output: {result}"
    
    # Special handling for booleans (case insensitive string comparison)
    if isinstance(result, bool) and isinstance(expected, str):
        if str(result).lower() == expected.lower():
            return True, f"Output: {result}"
    
    return False, f"Your output: {result} | Expected: {expected}"

def evaluate_multiple_test_cases(user_code: str, test_cases: List[Dict], 
                                problem_type: str = "standard") -> Tuple[str, str, List[Dict]]:
    """
    Evaluate user code against multiple test cases.
    
    Args:
        user_code: The user's submitted code
        test_cases: List of test cases, each with input and expected output
        problem_type: Type of problem for specialized comparisons
    
    Returns:
        Tuple of (result status, message, detailed test results)
    """
    all_passed = True
    detailed_results = []
    
    for idx, test_case in enumerate(test_cases):
        # Parse input and expected output
        input_data = parse_value(test_case.get("input", ""))
        expected = parse_value(test_case.get("output", ""))
        
        # Execute the code with current test case
        result, stdout, execution_time, success, error = safe_exec(
            user_code, input_data, 
            time_limit=test_case.get("time_limit", DEFAULT_TIME_LIMIT),
            memory_limit=test_case.get("memory_limit", DEFAULT_MEMORY_LIMIT)
        )
        
        if success:
            # Compare the result with expected output
            is_correct, explanation = compare_outputs(result, expected, problem_type)
            
            test_result = {
                "test_case": idx + 1,
                "passed": is_correct,
                "execution_time": f"{execution_time:.4f}s",
                "result": result,
                "expected": expected,
                "stdout": stdout,
                "explanation": explanation
            }
            
            if not is_correct:
                all_passed = False
        else:
            all_passed = False
            test_result = {
                "test_case": idx + 1,
                "passed": False,
                "execution_time": f"{execution_time:.4f}s",
                "error": error,
                "stdout": stdout
            }
        
        detailed_results.append(test_result)
    
    # Determine overall result
    if all_passed:
        return "Accepted", "All test cases passed successfully!", detailed_results
    else:
        # Count the number of failed test cases
        failed_count = sum(1 for result in detailed_results if not result.get("passed"))
        return "Wrong Answer", f"Failed {failed_count} out of {len(test_cases)} test cases.", detailed_results

def evaluate_submission(user_code: str, problem) -> Tuple[str, str, Optional[List[Dict]]]:
    """
    Main function to evaluate a code submission for a problem.
    Handles various problem types and multiple test cases.
    
    Args:
        user_code: User's submitted code
        problem: Problem object containing test cases and metadata
    
    Returns:
        Tuple of (result status, message, detailed results)
    """
    try:
        # Extract problem metadata
        problem_type = getattr(problem, "problem_type", "standard")
        time_limit = getattr(problem, "time_limit", DEFAULT_TIME_LIMIT)
        
        # Check if the problem has multiple test cases
        test_cases = getattr(problem, "test_cases", None)
        
        if test_cases:
            # Evaluate against multiple test cases
            return evaluate_multiple_test_cases(user_code, test_cases, problem_type)
        else:
            # Create a single test case from sample input/output
            test_case = {
                "input": problem.sample_input,
                "output": problem.sample_output,
                "time_limit": time_limit
            }
            
            status, message, detailed_results = evaluate_multiple_test_cases(
                user_code, [test_case], problem_type
            )
            
            # For single test case, simplify the message
            if status == "Accepted":
                return status, "Your solution passed the test case!", detailed_results
            else:
                if detailed_results and detailed_results[0].get("error"):
                    return status, detailed_results[0].get("error"), detailed_results
                return status, message, detailed_results
    
    except Exception as e:
        return "System Error", f"An error occurred during evaluation: {str(e)}", None

# Additional helper functions for complex problem types

def generate_test_cases_for_problem(problem_id: int) -> List[Dict]:
    """
    Generate comprehensive test cases for a specific problem.
    This would typically be called during problem creation/editing.
    
    Args:
        problem_id: ID of the problem
    
    Returns:
        List of test cases with inputs and expected outputs
    """
    # This is a simplified example - in a real system, you'd have more sophisticated
    # test case generation based on problem type, difficulty, etc.
    
    if problem_id == 1:  # Sum of two numbers
        return [
            {"input": "1 2", "output": "3"},
            {"input": "0 0", "output": "0"},  # Edge case
            {"input": "-5 10", "output": "5"},  # Negative numbers
            {"input": "999999 1", "output": "1000000"}  # Large numbers
        ]
    
    elif problem_id == 2:  # Check if number is prime
        return [
            {"input": "7", "output": "True"},
            {"input": "1", "output": "False"},  # Edge case
            {"input": "2", "output": "True"},   # Edge case
            {"input": "100", "output": "False"},
            {"input": "997", "output": "True"}  # Large prime
        ]
    
    elif problem_id == 3:  # Matrix multiplication
        return [
            {
                "input": "[[1, 2], [3, 4]]\n[[5, 6], [7, 8]]",
                "output": "[[19, 22], [43, 50]]"
            },
            {
                "input": "[[1, 0], [0, 1]]\n[[5, 6], [7, 8]]",
                "output": "[[5, 6], [7, 8]]"
            }
        ]
    
    # Default case - return a simple test
    return [{"input": "1", "output": "1"}]

def create_complex_problem_examples():
    """
    Create examples of more complex problem types that could be added to the system.
    These would be stored in the database as problem fixtures.
    """
    complex_problems = [
       
    ]
    
    return complex_problems

# Example solution templates for different problem types

def get_solution_template(problem_id: int) -> str:
    """
    Provide a starter template for the user based on the problem type.
    
    Args:
        problem_id: ID of the problem
    
    Returns:
        Template code as a string
    """
    templates = {
        # Basic problem template
        "standard": """def solution(a, b):
    # Your code here
    return a + b
""",
        # Template for graph problems
        "graph": """def solution(vertices, edges, start, end):
    # Create an adjacency list
    graph = [[] for _ in range(vertices)]
    for u, v, w in edges:
        graph[u].append((v, w))
    
    # Your implementation of Dijkstra's algorithm here
    
    # Return the shortest path
    return []
""",
        # Template for dynamic programming
        "dp": """def solution(n):
    # Initialize dp array
    dp = [0] * (n + 1)
    
    # Base cases
    dp[0] = 0
    dp[1] = 1
    
    # Fill dp array
    for i in range(2, n + 1):
        # Your recurrence relation here
        pass
    
    return dp[n]
"""
    }
    
    # Map problem ID to template type
    problem_template_map = {
        1: "standard",
        2: "standard",
        102: "graph",
        103: "standard",
        # Add more mappings as needed
    }
    
    template_type = problem_template_map.get(problem_id, "standard")
    return templates.get(template_type, templates["standard"])

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
import concurrent.futures

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
            # If setting the limit fails, continue without it
            pass
    else:
        pass

def parse_value(value_str: str) -> Any:
    """
    Parse a string value into a Python object:
    - JSON arrays/objects
    - Lists of values (split by whitespace)
    - Individual values (int, float, string, bool)
    - Special handling for matrices and graphs
    """
    value_str = value_str.strip()
    if not value_str:
        return None
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False
    if value_str and value_str[0] in ['[', '{']:
        try:
            return json.loads(value_str)
        except Exception:
            pass
    lines = value_str.strip().split('\n')
    if len(lines) > 1:
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
                    if row:
                        matrix.append(row)
                if matrix:
                    return matrix
            except Exception:
                pass
    if '\n' in value_str and re.search(r'\d+\s*[,-]\s*\d+', value_str):
        try:
            edges = []
            for line in value_str.strip().split('\n'):
                if not line.strip():
                    continue
                match = re.search(r'(\d+)\s*[,-]\s*(\d+)', line)
                if match:
                    edges.append((int(match.group(1)), int(match.group(2))))
            if edges:
                return {"type": "graph", "edges": edges}
        except Exception:
            pass
    parts = value_str.split()
    converted = []
    for part in parts:
        try:
            if '.' in part:
                converted.append(float(part))
            else:
                converted.append(int(part))
        except ValueError:
            converted.append(part)
    if len(converted) == 1:
        return converted[0]
    return converted

# Top-level helper function to run user code
def _run_user_code(code: str, inputs: Any, memory_limit: int) -> Tuple[Any, str, float, bool, str]:
    try:
        set_memory_limit(memory_limit)
        captured_output = io.StringIO()
        start_time = time.time()
        local_env = {}
        with redirect_stdout(captured_output):
            exec(code, {"__builtins__": __builtins__}, local_env)
        if 'solution' not in local_env:
            return (None, "", time.time() - start_time, False,
                    "Your code must define a function called 'solution'.")
        solution_func = local_env['solution']
        if not isinstance(inputs, (list, tuple)):
            inputs = [inputs]
        result = solution_func(*inputs)
        execution_time = time.time() - start_time
        stdout = captured_output.getvalue()
        if len(stdout) > MAX_OUTPUT_LENGTH:
            stdout = stdout[:MAX_OUTPUT_LENGTH] + "... (output truncated)"
        return (result, stdout, execution_time, True, None)
    except TimeoutException:
        return (None, "", DEFAULT_TIME_LIMIT, False, "Time limit exceeded")
    except MemoryLimitExceededException:
        return (None, "", time.time() - start_time, False, "Memory limit exceeded")
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        return (None, "", time.time() - start_time, False, f"Runtime Error: {error_msg}\n{tb}")

def safe_exec(code: str, inputs: Any, time_limit: float = DEFAULT_TIME_LIMIT, 
              memory_limit: int = DEFAULT_MEMORY_LIMIT) -> Tuple[Any, str, float, bool, str]:
    """
    Safely execute user code using a ProcessPoolExecutor to avoid Windows handle issues.
    Returns a tuple: (result, stdout, execution_time, success, error)
    """
    ctx = multiprocessing.get_context('spawn')
    with concurrent.futures.ProcessPoolExecutor(max_workers=1, mp_context=ctx) as executor:
        future = executor.submit(_run_user_code, code, inputs, memory_limit)
        try:
            result_tuple = future.result(timeout=time_limit)
            return result_tuple
        except concurrent.futures.TimeoutError:
            return (None, "", time_limit, False, "Time limit exceeded")
        except Exception as e:
            return (None, "", time_limit, False, str(e))

def compare_outputs(result: Any, expected: Any, problem_type: str = "standard") -> Tuple[bool, str]:
    if problem_type == "approximate":
        if isinstance(result, (int, float)) and isinstance(expected, (int, float)):
            epsilon = 1e-6
            if abs(result - expected) < epsilon:
                return True, f"Output: {result} (within epsilon of {expected})"
            else:
                return False, f"Your output: {result} | Expected: {expected} (difference exceeds epsilon)"
    elif problem_type == "unordered_array":
        if isinstance(result, list) and isinstance(expected, list):
            if sorted(result) == sorted(expected):
                return True, f"Output: {result} (matches expected elements)"
            else:
                return False, f"Your output: {result} | Expected: {expected} (elements don't match)"
    elif problem_type == "graph":
        if isinstance(result, dict) and isinstance(expected, dict):
            if result.get("type") == "graph" and expected.get("type") == "graph":
                result_edges = sorted(result.get("edges", []))
                expected_edges = sorted(expected.get("edges", []))
                if result_edges == expected_edges:
                    return True, f"Output: Graph with edges {result_edges}"
                else:
                    return False, f"Your output: Graph with edges {result_edges} | Expected: {expected_edges}"
    if result == expected:
        return True, f"Output: {result}"
    if isinstance(result, bool) and isinstance(expected, str):
        if str(result).lower() == expected.lower():
            return True, f"Output: {result}"
    return False, f"Your output: {result} | Expected: {expected}"

def evaluate_multiple_test_cases(user_code: str, test_cases: List[Dict], 
                                problem_type: str = "standard") -> Tuple[str, str, List[Dict]]:
    all_passed = True
    detailed_results = []
    for idx, test_case in enumerate(test_cases):
        input_data = parse_value(test_case.get("input", ""))
        expected = parse_value(test_case.get("output", ""))
        result, stdout, execution_time, success, error = safe_exec(
            user_code, input_data, 
            time_limit=test_case.get("time_limit", DEFAULT_TIME_LIMIT),
            memory_limit=test_case.get("memory_limit", DEFAULT_MEMORY_LIMIT)
        )
        if success:
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
    if all_passed:
        return "Accepted", "All test cases passed successfully!", detailed_results
    else:
        failed_count = sum(1 for result in detailed_results if not result.get("passed"))
        return "Wrong Answer", f"Failed {failed_count} out of {len(test_cases)} test cases.", detailed_results

def evaluate_submission(user_code: str, problem) -> Tuple[str, str, Optional[List[Dict]]]:
    try:
        problem_type = getattr(problem, "problem_type", "standard")
        time_limit = getattr(problem, "time_limit", DEFAULT_TIME_LIMIT)
        test_cases = getattr(problem, "test_cases", None)
        if test_cases:
            return evaluate_multiple_test_cases(user_code, test_cases, problem_type)
        else:
            test_case = {
                "input": problem.sample_input,
                "output": problem.sample_output,
                "time_limit": time_limit
            }
            status, message, detailed_results = evaluate_multiple_test_cases(
                user_code, [test_case], problem_type
            )
            if status == "Accepted":
                return status, "Your solution passed the test case!", detailed_results
            else:
                if detailed_results and detailed_results[0].get("error"):
                    return status, detailed_results[0].get("error"), detailed_results
                return status, message, detailed_results
    except Exception as e:
        return "System Error", f"An error occurred during evaluation: {str(e)}", None

def generate_test_cases_for_problem(problem_id: int) -> List[Dict]:
    if problem_id == 1:  # Sum of two numbers
        return [
            {"input": "1 2", "output": "3"},
            {"input": "0 0", "output": "0"},
            {"input": "-5 10", "output": "5"},
            {"input": "999999 1", "output": "1000000"}
        ]
    elif problem_id == 2:  # Check if number is prime
        return [
            {"input": "7", "output": "True"},
            {"input": "1", "output": "False"},
            {"input": "2", "output": "True"},
            {"input": "100", "output": "False"},
            {"input": "997", "output": "True"}
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
    return [{"input": "1", "output": "1"}]

def create_complex_problem_examples():
    complex_problems = []
    return complex_problems

def get_solution_template(problem_id: int) -> str:
    templates = {
        "standard": """def solution(a, b):
    # Your code here
    return a + b
""",
        "graph": """def solution(vertices, edges, start, end):
    # Create an adjacency list
    graph = [[] for _ in range(vertices)]
    for u, v, w in edges:
        graph[u].append((v, w))
    # Your implementation of Dijkstra's algorithm here
    return []
""",
        "dp": """def solution(n):
    dp = [0] * (n + 1)
    dp[0] = 0
    dp[1] = 1
    for i in range(2, n + 1):
        # Your recurrence relation here
        pass
    return dp[n]
"""
    }
    problem_template_map = {
        1: "standard",
        2: "standard",
        102: "graph",
        103: "standard",
    }
    template_type = problem_template_map.get(problem_id, "standard")
    return templates.get(template_type, templates["standard"])

import requests
import json
import time
import os
import re
import argparse
import hashlib
from collections import Counter

# Default configuration 
DEFAULT_API_ENDPOINT = "http://localhost:8000/api/query"
DEFAULT_INPUT_FILE = "perguntas.json"
DEFAULT_OUTPUT_FILE = "majority_vote_results.json"
DEFAULT_RUNS = 5
DEFAULT_TIMEOUT = 90

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run majority vote testing for SQL generation')
    
    parser.add_argument('-e', '--endpoint', 
                        default=DEFAULT_API_ENDPOINT,
                        help=f'API endpoint URL (default: {DEFAULT_API_ENDPOINT})')
    
    parser.add_argument('-i', '--input', 
                        default=DEFAULT_INPUT_FILE,
                        help=f'Input JSON file with questions (default: {DEFAULT_INPUT_FILE})')
    
    parser.add_argument('-o', '--output', 
                        default=DEFAULT_OUTPUT_FILE,
                        help=f'Output JSON file for results (default: {DEFAULT_OUTPUT_FILE})')
    
    parser.add_argument('-r', '--runs', 
                        type=int, 
                        default=DEFAULT_RUNS,
                        help=f'Number of runs per question (default: {DEFAULT_RUNS})')
    
    parser.add_argument('-t', '--timeout', 
                        type=int, 
                        default=DEFAULT_TIMEOUT,
                        help=f'Request timeout in seconds (default: {DEFAULT_TIMEOUT})')
    
    return parser.parse_args()

def load_questions(file_path: str) -> list:
    """Load questions from JSON input file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            if not isinstance(questions, list):
                print(f"Error: File '{file_path}' must contain a JSON list.")
                return []
            return questions
    except FileNotFoundError:
        print(f"Error: Questions file '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file '{file_path}'.")
        return []
    except Exception as e:
        print(f"Unexpected error loading questions: {e}")
        return []

def save_results(file_path: str, results_data: list):
    """Save the results to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=4)
        print(f"\nResults saved successfully to '{file_path}'")
    except IOError as e:
        print(f"Error saving results to file '{file_path}': {e}")
    except Exception as e:
        print(f"Unexpected error saving results: {e}")

def execute_query(question_text: str, api_endpoint: str, timeout: int) -> dict:
    """Send a question to the API and return the result."""
    payload = {"question": question_text}
    result = {
        "query": None,
        "results": None,
        "error": None
    }

    try:
        response = requests.post(api_endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.HTTPError as http_err:
        err_msg = f"HTTP Error: {http_err}"
        print(f"    {err_msg}")
        result["error"] = err_msg
        # Try to get the response body even in case of error, may contain details
        if http_err.response is not None:
            try:
                error_response = http_err.response.json()
                if "detail" in error_response:
                    result["error"] = error_response["detail"]
            except json.JSONDecodeError:
                result["error"] = http_err.response.text
    except requests.exceptions.ConnectionError as conn_err:
        err_msg = f"Connection Error: {conn_err}"
        print(f"    {err_msg} - Check if FastAPI is running at {api_endpoint}")
        result["error"] = err_msg
    except requests.exceptions.Timeout as timeout_err:
        err_msg = f"Timeout (after {timeout}s): {timeout_err}"
        print(f"    {err_msg}")
        result["error"] = err_msg
    except requests.exceptions.RequestException as req_err:
        err_msg = f"Request Error: {req_err}"
        print(f"    {err_msg}")
        result["error"] = err_msg
    except json.JSONDecodeError as json_err:
        err_msg = f"Error decoding API response JSON: {json_err}"
        print(f"    {err_msg}")
        result["error"] = err_msg

    return result

def results_to_string(results):
    """Convert results list to a sorted, normalized string for comparison."""
    if not results:
        return "EMPTY_RESULTS"
    
    # Create a serialized version of the results for comparison
    # For each result row, we sort the keys to ensure consistent ordering
    normalized_rows = []
    for row in results:
        if isinstance(row, dict):
            # Sort dictionary items by key for consistent serialization
            sorted_row = {k: row[k] for k in sorted(row.keys())}
            normalized_rows.append(sorted_row)
        else:
            normalized_rows.append(row)
    
    return json.dumps(normalized_rows, sort_keys=True)

def get_result_key(result):
    """Create a key for the result to identify similar results by their output."""
    # If there was an error, use the error as the key
    if result.get("error"):
        return f"ERROR:{result['error']}"
    
    # If there's no result data but there's a query (possibly with no output),
    # use a hash of the query as the key
    if not result.get("results") and result.get("query"):
        return f"QUERY_ONLY:{result['query'][:100]}"
    
    # For actual result data, create a normalized string representation
    # and hash it for a consistent, length-limited key
    results_str = results_to_string(result.get("results", []))
    results_hash = hashlib.md5(results_str.encode()).hexdigest()
    
    return f"RESULTS:{results_hash}"

def prefer_non_error_result(runs, most_common_key):
    """Choose a representative result, preferring those without errors."""
    # First look for results matching the key that have a query (not error)
    for run in runs:
        if (get_result_key(run) == most_common_key and 
            run.get("query") and 
            not run.get("error")):
            return run
    
    # Then look for any result matching the key
    for run in runs:
        if get_result_key(run) == most_common_key:
            return run
    
    # Fallback (shouldn't happen)
    return runs[0] if runs else None

def process_question(question_item: dict, api_endpoint: str, runs_per_question: int, timeout: int) -> dict:
    """Process a single question with majority voting."""
    question_id = question_item.get("id", "no_id")
    question_text = question_item.get("question")

    if not question_text:
        print(f"  ID: {question_id} - Empty question, skipping.")
        return {
            "id": question_id,
            "question": question_text,
            "majority_result": None,
            "error": "Question not provided in test item.",
            "runs": []
        }

    print(f"  ID: {question_id} - Processing question: \"{question_text}\"")
    
    # Run the question multiple times
    runs = []
    results_counter = Counter()
    
    for run_num in range(1, runs_per_question + 1):
        print(f"    Run {run_num}/{runs_per_question}...")
        run_result = execute_query(question_text, api_endpoint, timeout)
        runs.append(run_result)
        
        # Count occurrences of each result
        result_key = get_result_key(run_result)
        results_counter[result_key] += 1
        print(f"      Result key: {result_key[:30]}...")
    
    # Get the most common result
    most_common_results = results_counter.most_common()
    print(f"    Vote counts: {[(k[:20]+'...', v) for k, v in most_common_results]}")
    
    # Create the final result
    final_result = {
        "id": question_id,
        "question": question_text,
        "runs": runs,
        "vote_counts": [{"result": k, "count": v} for k, v in most_common_results]
    }
    
    # If we have a majority vote (appears at least twice)
    if most_common_results and most_common_results[0][1] >= 2:
        most_common_key = most_common_results[0][0]
        count = most_common_results[0][1]
        
        # Find the best representative result with this key
        representative_result = prefer_non_error_result(runs, most_common_key)
        if representative_result:
            final_result["majority_result"] = representative_result
            final_result["confidence"] = count / runs_per_question
                
        print(f"    Majority result found with {count}/{runs_per_question} votes.")
    else:
        final_result["majority_result"] = None
        final_result["confidence"] = 0
        final_result["error"] = "No clear majority result (all results different or all errors)."
        print(f"    No clear majority result found among {runs_per_question} runs.")

    return final_result

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set configuration from arguments
    api_endpoint = args.endpoint
    input_file = args.input
    output_file = args.output
    runs_per_question = args.runs
    timeout = args.timeout
    
    print(f"Starting majority vote test with {runs_per_question} runs per question...")
    print(f"Using API at: {api_endpoint}")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    questions = load_questions(input_file)
    if not questions:
        print("No questions loaded. Exiting.")
        return 1

    print(f"\n{len(questions)} questions loaded from '{input_file}'.")
    
    final_results = []

    for i, question_item in enumerate(questions):
        print(f"\nProcessing question {i+1}/{len(questions)}...")
        result = process_question(question_item, api_endpoint, runs_per_question, timeout)
        final_results.append(result)

    save_results(output_file, final_results)
    print("\nMajority vote testing completed.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 
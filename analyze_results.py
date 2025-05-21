#!/usr/bin/env python3
import json
import os
import sys
import argparse
from typing import Dict, List, Any

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Analyze majority vote test results')
    
    parser.add_argument('-i', '--input', 
                        default='backend/majority_vote_results.json',
                        help='Input JSON file with test results (default: backend/majority_vote_results.json)')
    
    parser.add_argument('-v', '--verbose', 
                        action='store_true',
                        help='Display detailed results for each question')
    
    parser.add_argument('-s', '--show-results',
                        action='store_true',
                        help='Show the actual result data in verbose mode (can be large)')
    
    return parser.parse_args()

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load test results from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
            if not isinstance(results, list):
                print(f"Error: File '{file_path}' does not contain a valid results list.")
                return []
            return results
    except FileNotFoundError:
        print(f"Error: Results file '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file '{file_path}'.")
        return []
    except Exception as e:
        print(f"Unexpected error loading results: {e}")
        return []

def analyze_confidence(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the confidence of the results."""
    
    if not results:
        return {
            "total_questions": 0,
            "successful_questions": 0,
            "failed_questions": 0,
            "success_rate": 0,
            "confidence_levels": {},
            "questions_by_confidence": {}
        }
    
    total_questions = len(results)
    successful_questions = sum(1 for r in results if r.get("majority_result") is not None)
    failed_questions = total_questions - successful_questions
    
    confidence_levels = {
        "high": sum(1 for r in results if r.get("confidence", 0) >= 0.8),
        "medium": sum(1 for r in results if 0.5 <= r.get("confidence", 0) < 0.8),
        "low": sum(1 for r in results if 0.2 <= r.get("confidence", 0) < 0.5),
        "very_low": sum(1 for r in results if 0 < r.get("confidence", 0) < 0.2),
        "none": sum(1 for r in results if r.get("confidence", 0) == 0)
    }
    
    questions_by_confidence = {
        "high": [r for r in results if r.get("confidence", 0) >= 0.8],
        "medium": [r for r in results if 0.5 <= r.get("confidence", 0) < 0.8],
        "low": [r for r in results if 0.2 <= r.get("confidence", 0) < 0.5],
        "very_low": [r for r in results if 0 < r.get("confidence", 0) < 0.2],
        "none": [r for r in results if r.get("confidence", 0) == 0]
    }
    
    return {
        "total_questions": total_questions,
        "successful_questions": successful_questions,
        "failed_questions": failed_questions,
        "success_rate": successful_questions / total_questions if total_questions > 0 else 0,
        "confidence_levels": confidence_levels,
        "questions_by_confidence": questions_by_confidence
    }

def analyze_errors(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the types of errors in the results."""
    error_types = {}
    
    for result in results:
        if result.get("error"):
            error_type = result["error"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        elif result.get("majority_result") and result["majority_result"].get("error"):
            error_type = result["majority_result"]["error"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
    
    return error_types

def format_vote_result(result_key, max_length=80):
    """Format the vote result key for display."""
    if result_key.startswith("ERROR:"):
        # For errors, show the error message
        return f"ERROR: {result_key[6:max_length]}"
    elif result_key.startswith("QUERY_ONLY:"):
        # For query-only results, show the query
        return f"QUERY ONLY: {result_key[11:max_length]}"
    elif result_key.startswith("RESULTS:"):
        # For results, show the hash
        return f"RESULTS HASH: {result_key[8:max_length]}"
    else:
        return result_key[:max_length]

def summarize_results(result_data):
    """Create a short summary of result data."""
    if not result_data:
        return "No data"
    
    if isinstance(result_data, list):
        row_count = len(result_data)
        col_count = len(result_data[0]) if row_count > 0 and isinstance(result_data[0], dict) else 0
        return f"{row_count} rows x {col_count} columns"
    
    return str(result_data)[:50] + "..." if len(str(result_data)) > 50 else str(result_data)

def print_question_details(question, verbose=False, show_results=False):
    """Print details for a single question."""
    print(f"Question ID: {question.get('id')}")
    print(f"  - Question: {question.get('question')}")
    
    majority_result = question.get("majority_result")
    confidence = question.get("confidence", 0)
    
    if majority_result:
        confidence_percent = confidence * 100
        confidence_level = ""
        if confidence >= 0.8:
            confidence_level = "HIGH"
        elif confidence >= 0.5:
            confidence_level = "MEDIUM"
        elif confidence >= 0.2:
            confidence_level = "LOW"
        else:
            confidence_level = "VERY LOW"
        
        print(f"  - Confidence: {confidence_percent:.1f}% ({confidence_level})")
        
        if majority_result.get("query"):
            print(f"  - SQL Query: {majority_result['query']}")
        
        if majority_result.get("error"):
            print(f"  - Error: {majority_result['error']}")
        else:
            results_summary = summarize_results(majority_result.get("results"))
            print(f"  - Results: {results_summary}")
            if show_results and majority_result.get("results"):
                print("  - Actual result data:")
                print(json.dumps(majority_result["results"], indent=4)[:500])
                if len(json.dumps(majority_result["results"], indent=4)) > 500:
                    print("    ... (truncated)")
        
        if verbose and "vote_counts" in question:
            print("  - Vote distribution:")
            for vote in question["vote_counts"]:
                vote_text = format_vote_result(vote["result"])
                print(f"      * {vote['count']} votes: {vote_text}")
            
            if "runs" in question:
                print(f"  - Ran {len(question['runs'])} times")
                
                if verbose:
                    print("  - Run details:")
                    for i, run in enumerate(question["runs"]):
                        print(f"    Run #{i+1}:")
                        if run.get("error"):
                            print(f"      ERROR: {run['error']}")
                        else:
                            print(f"      Query: {run.get('query', 'N/A')}")
                            if run.get("results") and show_results:
                                print(f"      Results: {summarize_results(run['results'])}")
    else:
        print("  - No majority result found")
        print(f"  - Error: {question.get('error', 'Unknown error')}")
    
    print()

def print_summary(analysis):
    """Print a summary of the analysis."""
    total = analysis["total_questions"]
    success = analysis["successful_questions"]
    failed = analysis["failed_questions"]
    success_rate = analysis["success_rate"] * 100
    
    print("=" * 80)
    print("SUMMARY OF MAJORITY VOTE RESULTS")
    print("=" * 80)
    print(f"Total questions: {total}")
    print(f"Successful questions: {success} ({success_rate:.1f}%)")
    print(f"Failed questions: {failed} ({100 - success_rate:.1f}%)")
    print()
    
    print("Confidence levels:")
    print(f"  - High (80-100%): {analysis['confidence_levels']['high']} questions")
    print(f"  - Medium (50-79%): {analysis['confidence_levels']['medium']} questions")
    print(f"  - Low (20-49%): {analysis['confidence_levels']['low']} questions")
    print(f"  - Very low (1-19%): {analysis['confidence_levels']['very_low']} questions")
    print(f"  - None (0%): {analysis['confidence_levels']['none']} questions")
    print()
    
    error_analysis = analyze_errors(analysis["questions_by_confidence"]["none"])
    if error_analysis:
        print("Common errors in failed questions:")
        for error, count in sorted(error_analysis.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {error[:80]}... ({count} occurrences)")
    
    print("=" * 80)

def main():
    args = parse_arguments()
    results = load_results(args.input)
    
    if not results:
        print("No results to analyze.")
        return 1
    
    analysis = analyze_confidence(results)
    print_summary(analysis)
    
    if args.verbose:
        print("\nDETAILED RESULTS\n")
        print("=" * 80)
        print("HIGH CONFIDENCE RESULTS (80-100%)")
        print("=" * 80)
        for question in analysis["questions_by_confidence"]["high"]:
            print_question_details(question, args.verbose, args.show_results)
        
        print("=" * 80)
        print("MEDIUM CONFIDENCE RESULTS (50-79%)")
        print("=" * 80)
        for question in analysis["questions_by_confidence"]["medium"]:
            print_question_details(question, args.verbose, args.show_results)
        
        print("=" * 80)
        print("LOW CONFIDENCE RESULTS (20-49%)")
        print("=" * 80)
        for question in analysis["questions_by_confidence"]["low"]:
            print_question_details(question, args.verbose, args.show_results)
        
        print("=" * 80)
        print("VERY LOW CONFIDENCE RESULTS (1-19%)")
        print("=" * 80)
        for question in analysis["questions_by_confidence"]["very_low"]:
            print_question_details(question, args.verbose, args.show_results)
        
        print("=" * 80)
        print("FAILED QUESTIONS (No majority result)")
        print("=" * 80)
        for question in analysis["questions_by_confidence"]["none"]:
            print_question_details(question, args.verbose, args.show_results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
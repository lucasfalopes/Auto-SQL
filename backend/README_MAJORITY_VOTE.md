# Majority Vote Testing for Auto-SQL

This system implements a majority vote approach to increase the reliability of SQL generation by running each query multiple times and selecting the most common result.

## How It Works

1. Each question is sent to the SQL generation model multiple times (default: 5)
2. **The actual results (table data) returned by each query are compared**, not just the SQL query text
3. If any result appears at least twice, it's selected as the correct answer
4. If all results are different, the system marks the result as inconclusive
5. Results without errors are preferred over results with errors

## Why Compare Results Instead of SQL

Different SQL queries can produce identical results. By comparing the actual query results (the returned data) instead of the SQL queries, we get a more accurate measure of whether the LLM is generating functionally equivalent queries, even if the syntax varies.

## Running the Tests

1. Make sure the backend API is running:
   ```
   cd backend
   python main.py
   ```

2. Run the majority vote test script:
   ```
   # From the project root:
   python run_majority_vote.py
   
   # Or from the backend directory:
   python majority_vote_test.py
   ```

3. Analyze the results:
   ```
   # From the project root:
   python analyze_results.py
   
   # For detailed output:
   python analyze_results.py --verbose
   ```

4. View the raw results in the generated `majority_vote_results.json` file

## Configuration

You can modify the settings using command-line arguments:

```
# Run with 10 attempts per question
python run_majority_vote.py --runs 10

# Customize the input questions file
python run_majority_vote.py --input custom_questions.json

# Customize the output file
python run_majority_vote.py --output custom_results.json
```

Available command-line arguments:

- `-r, --runs`: Number of runs per question (default: 5)
- `-t, --timeout`: Request timeout in seconds (default: 90)
- `-i, --input`: Input file with questions
- `-o, --output`: Output file for results
- `-w, --wait`: Maximum wait time for server in seconds (default: 30)
- `--no-server`: Don't start the server automatically

## Results Format

The test results are saved in JSON format with the following structure:

```json
[
  {
    "id": "test_001",
    "question": "List all active patients...",
    "runs": [
      { "query": "SELECT ...", "results": [...], "error": null },
      { "query": "SELECT ...", "results": [...], "error": null },
      ...
    ],
    "vote_counts": [
      { "result": "RESULTS:a1b2c3...", "count": 3 },
      { "result": "RESULTS:d4e5f6...", "count": 2 }
    ],
    "majority_result": { "query": "SELECT ...", "results": [...], "error": null },
    "confidence": 0.6
  },
  ...
]
```

## Benefits

- Increases reliability by using the consensus of multiple runs
- Compares actual query results, not just SQL syntax
- Provides confidence scores based on the frequency of each result
- Captures all individual runs for inspection and analysis
- Helps identify when the model is inconsistent in its responses

## Limitations

- Longer execution time due to multiple runs per question
- May still be inconclusive if there's high variability in model outputs
- Doesn't resolve issues where the model consistently gives wrong answers 
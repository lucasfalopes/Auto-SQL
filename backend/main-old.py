from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pg8000
from dotenv import load_dotenv
import os
import ollama

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    return pg8000.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    try:
        # Get database schema
        conn = get_db_connection()
        tables = []
        for row in conn.run("select TABLE_NAME from information_schema.tables WHERE table_schema='public' order by table_name"):
            tables.append(row[0])

        schema = f"All tables listed: {tables}\n\n"
        for table in tables:
            schema += f"Current table: {table}\n"
            for row in conn.run(f"select column_name, data_type from information_schema.columns where table_name = '{table}'"):
                schema += f"{row}\n"
        conn.close()

        # Generate SQL query using Ollama
        system_prompt = f"""
        You are an assistant specialized in SQL. Your role is to generate correct SQL queries for PostgreSQL based on the structure below.

        Important:
        - Always use the exact table and column names provided.
        - Never make up tables or columns.
        - All queries must be in pure PostgreSQL format.
        - If the question cannot be answered with the provided data, reply ONLY with "N/A".
        - The response must be ONLY an SQL query with no explanations or extra words.

        Example:
        Question: "Which movies are rated 'PG'?"
        Answer:
        SELECT title FROM film WHERE rating = 'PG';

        Database structure:

        {schema}
        """

        response = ollama.chat(
            model='llama3:instruct',
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': request.question,
                    'temperature': 0
                }
            ]
        )

        sql_query = response['message']['content']

        # Execute the query
        conn = get_db_connection()
        cursor = conn.run(sql_query)
        results = []
        for row in cursor:
            results.append(row)
        conn.close()

        return {
            "query": sql_query,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
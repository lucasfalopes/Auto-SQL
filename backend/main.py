from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pg8000
from dotenv import load_dotenv
import os
import ollama
import time # Necessário para TTL manual, mas TTLCache cuida disso. Útil para logging.
import asyncio # Para rodar código síncrono bloqueante em uma thread separada
from cachetools import cached, TTLCache
from contextlib import asynccontextmanager
import re

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(current_app: FastAPI): # 'current_app' é o nome convencional para a instância do FastAPI
    # <<< INÍCIO DA LÓGICA DO SEU ANTIGO startup_event >>>
    # Opcional: Carregar o schema na inicialização para "aquecer" o cache
    # Isso é útil se a primeira chamada não puder ter a latência da busca do schema.
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Aplicação (FastAPI) iniciando - Lifespan: Startup")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tentando aquecer o cache do schema...")
    try:
        # Como get_cached_schema_string agora chama uma função síncrona bloqueante,
        # rodamos em uma thread para não bloquear o startup do FastAPI.
        await asyncio.to_thread(get_cached_schema_string) # Certifique-se que get_cached_schema_string está definida
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cache do schema aquecido com sucesso.")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Falha ao aquecer o cache do schema na inicialização: {e}")
    # <<< FIM DA LÓGICA DO SEU ANTIGO startup_event >>>
    
    yield  # A aplicação FastAPI roda aqui
    
    # Código para shutdown (se necessário)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Aplicação (FastAPI) encerrando - Lifespan: Shutdown")


# app = FastAPI()
app = FastAPI(lifespan=lifespan)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua pela URL do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection ( permanece o mesmo)
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

# --- Configuração do Cache para o Schema ---
# Cache para no máximo 1 item (nosso schema string), com TTL de 3600 segundos (1 hora)
schema_cache = TTLCache(maxsize=1, ttl=3600)

# Esta é a função que efetivamente busca e formata o schema do banco.
# Ela não será decorada diretamente se a intenção é que o @cached gerencie a chamada.
# Ou, se ela for a função a ser cacheada, ela não deve ter argumentos que variam
# se você quer sempre a mesma chave de cache (ou usar um key=lambda).
def _fetch_and_build_detailed_schema_string():
    """
    Busca os metadados do banco de dados e constrói a string de schema formatada.
    Esta função realiza as chamadas de I/O ao banco.
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CACHE MISS ou TTL EXPIRADO: Buscando schema do banco de dados...")
    conn = None
    try:
        conn = get_db_connection()
        tables_info = {}
        table_names = []

        # 1. Get all table names in the public schema (pode continuar com conn.run se quiser, ou mudar também)
        with conn.cursor() as cursor: # Usando cursor explícito
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
            for row in cursor:
                table_names.append(row[0])

        for table_name in table_names:
            print(f"[DB_SCHEMA_DEBUG] Processando tabela: '{table_name}'") # Para depuração
            tables_info[table_name] = {'columns': [], 'pk': None, 'fks': []}

            # 2. Get Primary Key
            pk_query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_name = %s
              AND tc.table_schema = 'public';
            """
            with conn.cursor() as cursor: # Usando cursor explícito
                cursor.execute(pk_query, (table_name,))
                pk_column_result = cursor.fetchall() # .fetchall() para caso haja PK composta, embora estejamos pegando só a primeira coluna
                if pk_column_result and len(pk_column_result) > 0:
                    tables_info[table_name]['pk'] = pk_column_result[0][0] # Pega a primeira coluna da primeira linha

            # 3. Get Columns and their types
            column_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema='public'
            ORDER BY ordinal_position;
            """
            with conn.cursor() as cursor: # Usando cursor explícito
                cursor.execute(column_query, (table_name,))
                for col_row in cursor:
                    column_name, data_type = col_row
                    tables_info[table_name]['columns'].append(
                        {'name': column_name, 'type': data_type, 'is_pk': column_name == tables_info[table_name].get('pk')}
                    )

            # 4. Get Foreign Keys for the current table
            fk_query = """
            SELECT
                kcu.column_name AS fk_column,
                rc.unique_constraint_schema AS referenced_schema,
                rel_kcu.table_name AS referenced_table,
                rel_kcu.column_name AS referenced_column
            FROM
                information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints rc
                ON tc.constraint_name = rc.constraint_name AND tc.table_schema = rc.constraint_schema
            JOIN information_schema.key_column_usage rel_kcu
                ON rc.unique_constraint_name = rel_kcu.constraint_name AND rc.unique_constraint_schema = rel_kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s;
            """
            with conn.cursor() as cursor: # Usando cursor explícito
                cursor.execute(fk_query, (table_name,))
                for fk_row in cursor:
                    tables_info[table_name]['fks'].append({
                        'from_column': fk_row[0],
                        'references_table': fk_row[2],
                        'references_column': fk_row[3]
                    })

        # 5. Format the schema string (lógica de formatação permanece a mesma)
        schema_str = "PostgreSQL Schema:\n"
        for table_name, info in tables_info.items():
            schema_str += f"Table: {table_name}"
            if info['pk']:
                schema_str += f" (PK: {info['pk']})"
            schema_str += "\nColumns:\n"
            for col in info['columns']:
                pk_indicator = " (PK)" if col['is_pk'] else ""
                schema_str += f"  - {col['name']} ({col['type']}){pk_indicator}\n"
            if info['fks']:
                schema_str += "Foreign Keys:\n"
                for fk in info['fks']:
                    schema_str += f"  - {table_name}.{fk['from_column']} REFERENCES {fk['references_table']}({fk['references_column']})\n"
            schema_str += "\n"
        
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Schema do banco construído com sucesso.")
        return schema_str
    except pg8000.dbapi.Error as db_api_err: # Captura erros DB-API mais genéricos aqui também
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO DB-API em _fetch_and_build_detailed_schema_string: {db_api_err}")
        # Você pode querer relançar a exceção ou retornar None/string de erro para ser tratada pela função chamadora
        raise # Relança a exceção para ser pega pelo try...except no lifespan ou no endpoint
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO Inesperado em _fetch_and_build_detailed_schema_string: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if conn:
            conn.close()

# Função decorada para cachear o schema.
# Usamos 'key=lambda: "global_schema_key"' para garantir que sempre usamos a mesma chave
# de cache, já que esta função não recebe argumentos que diferenciam chamadas.
@cached(cache=schema_cache, key=lambda: "global_schema_key")
def get_cached_schema_string():
    """
    Retorna a string do schema, utilizando o cache.
    Se o schema não estiver no cache ou o TTL tiver expirado,
    a função _fetch_and_build_detailed_schema_string será chamada.
    """
    return _fetch_and_build_detailed_schema_string()


@app.post("/admin/clear-schema-cache") # Proteja este endpoint!
async def clear_schema():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Limpando cache do schema manualmente...")
    schema_cache.clear() # Limpa todos os itens do cache
    # Opcionalmente, re-popule o cache imediatamente:
    # await asyncio.to_thread(get_cached_schema_string)
    return {"message": "Cache do schema limpo. Será recarregado na próxima necessidade."}

def compress_schema(schema_str, question):
    """
    Comprime o schema para reduzir o tamanho do contexto enviado ao LLM.
    Estratégias:
    1. Identifica palavras-chave relevantes na pergunta
    2. Filtra apenas tabelas potencialmente relevantes
    3. Reduz a verbosidade da representação
    """
    print(f"[API LOG] Comprimindo schema para a pergunta: {question}")
    
    # Extrai todas as tabelas do schema
    tables = {}
    current_table = None
    table_section_lines = []
    
    for line in schema_str.splitlines():
        if line.startswith("Table: "):
            # Salva a tabela anterior se existir
            if current_table and table_section_lines:
                tables[current_table] = "\n".join(table_section_lines)
            
            # Inicia nova tabela
            # Extrai o nome da tabela, considerando o formato "Table: nome_tabela (PK: ...)"
            table_parts = line.replace("Table: ", "").split(" (PK:")
            current_table = table_parts[0].strip()
            table_section_lines = [line]
        elif current_table and line.strip():
            table_section_lines.append(line)
    
    # Adiciona a última tabela
    if current_table and table_section_lines:
        tables[current_table] = "\n".join(table_section_lines)
    
    # Palavras-chave e termos de busca da pergunta (convertidas para lowercase)
    keywords = question.lower().split()
    
    # Conjunto de tabelas fundamentais que sempre incluímos
    core_tables = {
        'core_patient', 'core_user', 'core_equipment', 'core_department', 
        'core_bed', 'core_monitoringrealtime', 'core_monitoring',
        'core_alarming', 'core_alarm'
    }
    
    # Pontuação de relevância para cada tabela
    table_scores = {table: 0 for table in tables}
    
    # Atribui pontuação com base em correspondência de palavras-chave
    for table in tables:
        table_content = tables[table].lower()
        
        # Tabelas principais sempre recebem pontuação alta
        if table in core_tables:
            table_scores[table] = 100
            continue
            
        # Pontuação baseada em correspondência de palavras-chave
        for keyword in keywords:
            if keyword in table.lower() or keyword in table_content:
                table_scores[table] += 10
        
        # Tabelas com palavras específicas do domínio da aplicação recebem maior relevância
        domain_terms = ['patient', 'equipment', 'device', 'department', 'bed', 'monitor', 'alarm']
        for term in domain_terms:
            if term in table.lower() or term in table_content:
                table_scores[table] += 5
    
    # Seleciona as N tabelas mais relevantes (ajuste este valor conforme necessário)
    max_tables = 20
    top_tables = sorted(table_scores.keys(), key=lambda t: table_scores[t], reverse=True)[:max_tables]
    
    # Constrói schema comprimido apenas com tabelas relevantes
    compressed_schema_lines = ["PostgreSQL Schema:"]
    for table in top_tables:
        compressed_schema_lines.append(tables[table])
    
    compressed_schema = "\n".join(compressed_schema_lines)
    
    # Log das tabelas selecionadas
    print(f"[API LOG] Tabelas selecionadas para schema comprimido ({len(top_tables)} de {len(tables)}): {', '.join(top_tables)}")
    
    return compressed_schema

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    try:
        # Obtém o schema (do cache ou buscando no banco se necessário)
        # Como get_cached_schema_string é síncrona e pode bloquear (I/O do banco na primeira vez),
        # usamos asyncio.to_thread para executá-la em uma thread separada e não bloquear o event loop.
        print("[API LOG] Obtendo schema...")
        schema_definition = await asyncio.to_thread(get_cached_schema_string)
        print(f"[API LOG] Schema obtido: {schema_definition[:200]}...") # Imprime parte do schema

        # Comprime o schema antes de enviar para o LLM
        compressed_schema = compress_schema(schema_definition, request.question)
        print(f"[API LOG] Tamanho do schema original: {len(schema_definition)} caracteres")
        print(f"[API LOG] Tamanho do schema comprimido: {len(compressed_schema)} caracteres")

        print("[API LOG] Preparando prompt para Ollama...")
        system_prompt = f"""
            You are a PostgreSQL SQL generator. Given a natural language question and a database schema, your job is to generate a single valid SQL query that answers the question.

            Rules (NO EXCEPTIONS):
            ONLY output the SQL query. DO NOT add any explanations, text, comments, or formatting. NO markdown. NO quotations. NO code blocks. NOTHING but the SQL.
            ONLY use the tables and columns that exist in the provided schema. NEVER invent table names or column names.
            ALWAYS follow foreign key relationships exactly as defined. Use INNER JOIN only when a direct relationship exists.
            If the question CANNOT be answered using the schema, output EXACTLY: N/A

            Final output MUST be a single-line, executable PostgreSQL SQL query. Example format:
            SELECT T1.title FROM film AS T1 INNER JOIN film_actor AS T2 ON T1.film_id = T2.film_id INNER JOIN actor AS T3 ON T2.actor_id = T3.actor_id WHERE T3.first_name = 'JOHN' AND T3.last_name = 'DOE';
            
            Database schema:

            {compressed_schema}
            """

        print(f"[API LOG] Enviando para Ollama com a pergunta: {request.question}")
        try:
            print("[API LOG] Configurando chamada do Ollama...")
            
            # Simplificando a chamada do Ollama
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': request.question, 'temperature': 0}
            ]
            
            print(f"[API LOG] Mensagens: {messages}")
            print(f"[API LOG] Modelo: mistral-small3.1")
            
            response = ollama.chat(
                model='mistral-nemo:latest',
                messages=messages
            )
            
            print(f"[API LOG] Resposta do Ollama: {response}")
            
            if not response:
                raise ValueError("Resposta vazia do Ollama")
            if 'message' not in response:
                raise ValueError("Resposta do Ollama não contém 'message'")
            if 'content' not in response['message']:
                raise ValueError("Resposta do Ollama não contém 'content'")
                
            sql_query_raw = response['message']['content'].strip()
            print(f"[API LOG] Query SQL bruta: {sql_query_raw}")
            # Função para extrair apenas o SQL puro
            def extract_sql(text):
                match = re.search(r'```sql\s*([\s\S]+?)\s*```', text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                match = re.search(r'```\s*([\s\S]+?)\s*```', text)
                if match:
                    return match.group(1).strip()
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if line.strip().lower().startswith(('select', 'with', 'insert', 'update', 'delete')):
                        return '\n'.join(lines[i:]).strip()
                return text.strip()
            sql_query = extract_sql(sql_query_raw)
            print(f"[API LOG] Query SQL limpa: {sql_query}")
            if sql_query.upper() == "N/A":
                return {
                    "query": "N/A",
                    "results": "The model determined the question cannot be answered with the provided schema."
                }
                
        except Exception as e:
            error_msg = f"Erro ao gerar SQL com Ollama: {str(e)}"
            print(f"[API LOG] {error_msg}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=error_msg)

        # Conexão para executar a query SQL gerada
        conn_exec = None
        try:
            conn_exec = get_db_connection()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Executando query: {sql_query}")
            
            results = []
            column_names = []
            with conn_exec.cursor() as cursor: # Use a cursor object
                cursor.execute(sql_query)
                if cursor.description: # Check if there's a description (e.g., for SELECT)
                    column_names = [desc[0] for desc in cursor.description]
                    for row_data in cursor: # Renamed 'row' to 'row_data'
                        results.append(dict(zip(column_names, row_data)))
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Query executada, {len(results)} resultados obtidos.")
                else:
                    # Handles cases like DDL or DML without RETURNING, or if SELECT is malformed.
                    # rowcount might be useful for DML.
                    rowcount_str = str(cursor.rowcount) if hasattr(cursor, 'rowcount') else 'N/A'
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Query executada. Não retornou descrição de colunas. Linhas afetadas (se aplicável): {rowcount_str}")
                    # Results will remain an empty list.
        finally:
            if conn_exec:
                conn_exec.close()

        return {
            "query": sql_query,
            "results": results
        }

    except pg8000.dbapi.ProgrammingError as db_err: # Alterado de pg8000.exceptions para pg8000.dbapi
        error_detail = f"Database programming error with query: '{sql_query if 'sql_query' in locals() else 'N/A'}'. Error: {str(db_err)}"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_detail}")
        # Se conn_exec foi definida e a conexão está aberta antes do erro, feche-a.
        if 'conn_exec' in locals() and conn_exec:
            try:
                conn_exec.close()
            except pg8000.exceptions.InterfaceError:
                # Connection is already closed
                pass
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        error_detail = f"An unexpected error occurred: {str(e)}"
        if 'sql_query' in locals():
             error_detail += f" Attempted SQL query: '{sql_query}'"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_detail}")
        # Ensure connection is closed properly in generic exception case too
        if 'conn_exec' in locals() and conn_exec:
            try:
                conn_exec.close()
            except pg8000.exceptions.InterfaceError:
                # Connection is already closed
                pass
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    # Adicione 'loop="asyncio"' se estiver no Windows e encontrar problemas com o event loop padrão
    uvicorn.run(app, host="0.0.0.0", port=8000)
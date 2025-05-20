import requests
import json
import time # Para logging e possíveis delays
import os   # Para manipulação de diretórios

# --- Configurações ---
API_ENDPOINT_URL = "http://localhost:8000/api/query"  # URL da sua API FastAPI
INPUT_QUESTIONS_FILE = "perguntas.json"
TESTS_DIRECTORY = "tests"  # Diretório para armazenar os resultados dos testes
NUM_TEST_RUNS = 10  # Número de vezes que o teste será executado
REQUEST_TIMEOUT_SECONDS = 90  # Timeout para cada requisição à API (LLMs podem demorar)

def carregar_perguntas(caminho_arquivo: str) -> list:
    """Carrega as perguntas do arquivo JSON de entrada."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            perguntas = json.load(f)
            if not isinstance(perguntas, list):
                print(f"Erro: O arquivo '{caminho_arquivo}' deve conter uma lista JSON.")
                return []
            return perguntas
    except FileNotFoundError:
        print(f"Erro: Arquivo de perguntas '{caminho_arquivo}' não encontrado.")
        return []
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar JSON do arquivo '{caminho_arquivo}'.")
        return []
    except Exception as e:
        print(f"Erro inesperado ao carregar perguntas: {e}")
        return []

def salvar_respostas(caminho_arquivo: str, dados_respostas: list):
    """Salva as perguntas e suas respectivas respostas em um arquivo JSON."""
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_respostas, f, ensure_ascii=False, indent=4)
        print(f"\nRespostas salvas com sucesso em '{caminho_arquivo}'")
    except IOError as e:
        print(f"Erro ao salvar respostas no arquivo '{caminho_arquivo}': {e}")
    except Exception as e:
        print(f"Erro inesperado ao salvar respostas: {e}")


def executar_teste_pergunta(pergunta_item: dict) -> dict:
    """Envia uma única pergunta para a API e retorna o resultado."""
    id_pergunta = pergunta_item.get("id", "sem_id")
    texto_pergunta = pergunta_item.get("question")

    if not texto_pergunta:
        print(f"  ID: {id_pergunta} - Pergunta vazia, pulando.")
        return {
            "id": id_pergunta,
            "question": texto_pergunta,
            "api_response": None,
            "error": "Pergunta não fornecida no item de teste."
        }

    print(f"  ID: {id_pergunta} - Enviando pergunta: \"{texto_pergunta}\"")
    payload = {"question": texto_pergunta}
    resultado = {
        "id": id_pergunta,
        "question": texto_pergunta,
        "api_response": None,
        "error": None
    }

    try:
        response = requests.post(API_ENDPOINT_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()  # Levanta exceção para erros HTTP (4xx ou 5xx)
        resultado["api_response"] = response.json()
        print(f"    Status: {response.status_code} - Resposta recebida.")
    except requests.exceptions.HTTPError as http_err:
        err_msg = f"Erro HTTP: {http_err}"
        print(f"    {err_msg}")
        resultado["error"] = err_msg
        # Tenta obter o corpo da resposta mesmo em caso de erro, pode conter detalhes
        if http_err.response is not None:
            try:
                resultado["api_response"] = http_err.response.json()
            except json.JSONDecodeError:
                resultado["api_response"] = http_err.response.text
    except requests.exceptions.ConnectionError as conn_err:
        err_msg = f"Erro de Conexão: {conn_err}"
        print(f"    {err_msg} - Verifique se a API FastAPI está rodando em {API_ENDPOINT_URL}")
        resultado["error"] = err_msg
    except requests.exceptions.Timeout as timeout_err:
        err_msg = f"Timeout (após {REQUEST_TIMEOUT_SECONDS}s): {timeout_err}"
        print(f"    {err_msg}")
        resultado["error"] = err_msg
    except requests.exceptions.RequestException as req_err:
        err_msg = f"Erro na Requisição: {req_err}"
        print(f"    {err_msg}")
        resultado["error"] = err_msg
    except json.JSONDecodeError as json_err: # Caso a API retorne sucesso mas não seja JSON
        err_msg = f"Erro ao decodificar JSON da resposta da API: {json_err}"
        print(f"    {err_msg}")
        resultado["error"] = err_msg
        resultado["api_response"] = response.text if 'response' in locals() else "Resposta não disponível"


    return resultado

def criar_diretorio_testes():
    """Cria o diretório de testes se não existir."""
    if not os.path.exists(TESTS_DIRECTORY):
        try:
            os.makedirs(TESTS_DIRECTORY)
            print(f"Diretório '{TESTS_DIRECTORY}' criado com sucesso.")
        except OSError as e:
            print(f"Erro ao criar diretório '{TESTS_DIRECTORY}': {e}")
            return False
    return True

def main():
    print("Iniciando script de testes automatizados...")
    print(f"Usando API em: {API_ENDPOINT_URL}")
    print(f"Executando {NUM_TEST_RUNS} testes sequenciais")
    
    if not criar_diretorio_testes():
        print("Não foi possível criar o diretório de testes. Encerrando.")
        return
    
    perguntas_para_testar = carregar_perguntas(INPUT_QUESTIONS_FILE)
    if not perguntas_para_testar:
        print("Nenhuma pergunta carregada. Encerrando.")
        return

    print(f"\n{len(perguntas_para_testar)} perguntas carregadas de '{INPUT_QUESTIONS_FILE}'.")
    
    for run in range(1, NUM_TEST_RUNS + 1):
        output_file = os.path.join(TESTS_DIRECTORY, f"test{run}.json")
        print(f"\n--- Iniciando teste {run}/{NUM_TEST_RUNS} ---")
        
        resultados_finais = []

        for i, item_pergunta in enumerate(perguntas_para_testar):
            print(f"\nProcessando pergunta {i+1}/{len(perguntas_para_testar)}...")
            resultado_teste = executar_teste_pergunta(item_pergunta)
            resultados_finais.append(resultado_teste)
            # Adicionar um pequeno delay pode ser útil para não sobrecarregar a API
            # ou para respeitar limites de taxa, se houver.
            # time.sleep(0.5) 

        salvar_respostas(output_file, resultados_finais)
        print(f"\nTeste {run}/{NUM_TEST_RUNS} concluído.")
    
    print("\nTodos os testes automatizados foram concluídos.")

if __name__ == "__main__":
    main()
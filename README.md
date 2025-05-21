# Auto-SQL

Aplicação web que permite gerar queries SQL a partir de perguntas em linguagem natural usando IA.

<div align="center">
  <img src="inicial-page.png" alt="Página inicial da aplicação" width="400" />
</div>

## Pré-requisitos

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Ollama (para o modelo de IA)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/chatbot-db.git
cd chatbot-db
```

2. Configure o banco de dados PostgreSQL:
- Crie um banco de dados chamado `pagila`
- Importe o schema do banco de dados (você pode usar o arquivo `pagila-schema.sql`)

3. Instale as dependências do backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Instale as dependências do frontend:
```bash
cd ../frontend
npm install
```

5. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env` no diretório backend
- Ajuste as configurações do banco de dados no arquivo `.env`

## Executando a aplicação

1. Inicie o servidor backend:
```bash
cd backend
source venv/bin/activate  # No Windows: venv\Scripts\activate
python main.py
```

2. Em outro terminal, inicie o servidor frontend:
```bash
cd frontend
npm start
```

3. Acesse a aplicação em `http://localhost:3000`

## Uso

1. Digite sua pergunta em linguagem natural no campo de texto
2. Clique em "Ask" para gerar a query SQL
3. A query gerada será exibida e executada automaticamente
4. Os resultados serão mostrados em uma tabela abaixo
5. Você pode copiar a query SQL ou exportar os resultados para CSV

## Sistema de Votação por Maioria

Para lidar com possíveis inconsistências nas respostas do modelo, foi implementado um sistema de votação por maioria que executa cada pergunta várias vezes e seleciona o resultado mais frequente.

### Como funciona

1. Cada pergunta é enviada ao modelo múltiplas vezes (padrão: 5 vezes)
2. **Os resultados reais (dados da tabela) retornados por cada consulta são comparados**, não apenas o texto da consulta SQL
3. Se algum resultado aparecer pelo menos duas vezes, ele é selecionado como correto
4. Se todos os resultados forem diferentes, o sistema marca o resultado como inconclusivo
5. Resultados sem erros são preferidos em relação a resultados com erros

### Executando os testes com votação por maioria

Para executar o sistema de votação por maioria:

```bash
python run_majority_vote.py

# Com opções customizadas:
python run_majority_vote.py --runs 10 --timeout 120
```

Os resultados serão salvos em `backend/majority_vote_results.json`. Para analisar os resultados:

```bash
python analyze_results.py

# Para exibir resultados detalhados:
python analyze_results.py --verbose
```

Para mais informações, consulte o arquivo `backend/README_MAJORITY_VOTE.md`.

## Tecnologias utilizadas

- Frontend: React, Tailwind CSS
- Backend: Python, FastAPI
- Banco de dados: PostgreSQL
- IA: Ollama com modelo Llama 3 
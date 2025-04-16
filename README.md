# Auto-SQL

Aplicação web que permite gerar queries SQL a partir de perguntas em linguagem natural usando IA.

![Página inicial da aplicação](inicial-page.png)

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

## Tecnologias utilizadas

- Frontend: React, Tailwind CSS
- Backend: Python, FastAPI
- Banco de dados: PostgreSQL
- IA: Ollama com modelo Llama 3 
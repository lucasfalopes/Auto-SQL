import ollama

schema = """All tables listed: ['actor', 'actor_info', 'address', 'category', 'city', 'country', 'customer', 'customer_list', 'film', 'film_actor', 'film_category', 'film_list', 'inventory', 'language', 'nicer_but_slower_film_list', 'payment', 'payment_p2022_01', 'payment_p2022_02', 'payment_p2022_03', 'payment_p2022_04', 'payment_p2022_05', 'payment_p2022_06', 'payment_p2022_07', 'rental', 'sales_by_film_category', 'sales_by_store', 'staff', 'staff_list', 'store']
Current table: actor
['actor_id', 'integer']
['first_name', 'text']
['last_name', 'text']
['last_update', 'timestamp with time zone']
Current table: actor_info
['actor_id', 'integer']
['first_name', 'text']
['last_name', 'text']
['film_info', 'text']
Current table: address
['address_id', 'integer']
['address', 'text']
['address2', 'text']
['district', 'text']
['city_id', 'integer']
['postal_code', 'text']
['phone', 'text']
['last_update', 'timestamp with time zone']
Current table: category
['category_id', 'integer']
['name', 'text']
['last_update', 'timestamp with time zone']
Current table: city
['city_id', 'integer']
['city', 'text']
['country_id', 'integer']
['last_update', 'timestamp with time zone']
Current table: country
['country_id', 'integer']
['country', 'text']
['last_update', 'timestamp with time zone']
Current table: customer
['customer_id', 'integer']
['store_id', 'integer']
['first_name', 'text']
['last_name', 'text']
['email', 'text']
['address_id', 'integer']
['activebool', 'boolean']
['create_date', 'date']
['last_update', 'timestamp with time zone']
['active', 'integer']
Current table: customer_list
['id', 'integer']
['name', 'text']
['address', 'text']
['zip code', 'text']
['phone', 'text']
['city', 'text']
['country', 'text']
['notes', 'text']
['sid', 'integer']
Current table: film
['film_id', 'integer']
['title', 'text']
['description', 'text']
['release_year', 'integer']
['language_id', 'integer']
['original_language_id', 'integer']
['rental_duration', 'smallint']
['rental_rate', 'numeric']
['length', 'smallint']
['replacement_cost', 'numeric']
['rating', 'USER-DEFINED']
['last_update', 'timestamp with time zone']
['special_features', 'ARRAY']
['fulltext', 'tsvector']
Current table: film_actor
['actor_id', 'integer']
['film_id', 'integer']
['last_update', 'timestamp with time zone']
Current table: film_category
['film_id', 'integer']
['category_id', 'integer']
['last_update', 'timestamp with time zone']
Current table: film_list
['fid', 'integer']
['title', 'text']
['description', 'text']
['category', 'text']
['price', 'numeric']
['length', 'smallint']
['rating', 'USER-DEFINED']
['actors', 'text']
Current table: inventory
['inventory_id', 'integer']
['film_id', 'integer']
['store_id', 'integer']
['last_update', 'timestamp with time zone']
Current table: language
['language_id', 'integer']
['name', 'character']
['last_update', 'timestamp with time zone']
Current table: nicer_but_slower_film_list
['fid', 'integer']
['title', 'text']
['description', 'text']
['category', 'text']
['price', 'numeric']
['length', 'smallint']
['rating', 'USER-DEFINED']
['actors', 'text']
Current table: payment
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_01
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_02
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_03
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_04
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_05
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_06
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: payment_p2022_07
['payment_id', 'integer']
['customer_id', 'integer']
['staff_id', 'integer']
['rental_id', 'integer']
['amount', 'numeric']
['payment_date', 'timestamp with time zone']
Current table: rental
['rental_id', 'integer']
['rental_date', 'timestamp with time zone']
['inventory_id', 'integer']
['customer_id', 'integer']
['return_date', 'timestamp with time zone']
['staff_id', 'integer']
['last_update', 'timestamp with time zone']
Current table: sales_by_film_category
['category', 'text']
['total_sales', 'numeric']
Current table: sales_by_store
['store', 'text']
['manager', 'text']
['total_sales', 'numeric']
Current table: staff
['staff_id', 'integer']
['first_name', 'text']
['last_name', 'text']
['address_id', 'integer']
['email', 'text']
['store_id', 'integer']
['active', 'boolean']
['username', 'text']
['password', 'text']
['last_update', 'timestamp with time zone']
['picture', 'bytea']
Current table: staff_list
['id', 'integer']
['name', 'text']
['address', 'text']
['zip code', 'text']
['phone', 'text']
['city', 'text']
['country', 'text']
['sid', 'integer']
Current table: store
['store_id', 'integer']
['manager_staff_id', 'integer']
['address_id', 'integer']
['last_update', 'timestamp with time zone']"""

system_prompt = f"""
Você é um assistente especialista em SQL. Seu papel é gerar queries SQL corretas para PostgreSQL com base na estrutura abaixo.

Importante:
- Sempre use os nomes exatos de tabelas e colunas fornecidos.
- Nunca invente tabelas ou colunas.
- Todas as queries devem estar no formato PostgreSQL puro.
- Se a pergunta não puder ser respondida com os dados fornecidos, responda APENAScom "N/A".
- A resposta deve ser APENAS uma query SQL sem explicações e nem palavras adicionais.

Estrutura do banco de dados:

{schema}

Responda sempre com apenas a query SQL dentro de uma marcação de código, assim:

```sql
SELECT ...
FROM ...
WHERE ...;
```

"""

pedido = input("Digite sua pergunta: ")

response = ollama.chat(
    model='llama3:instruct',
    messages=[
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': pedido,
            'temperature': 0.1
        }
    ]
)

print(response['message']['content'])
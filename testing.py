import requests
import json

auth_url = 'http://localhost:5000/auth'
auth_data = {
    "agent_id": 1234  # Example agent_id
}

auth_response = requests.post(auth_url, json=auth_data)
auth_result = auth_response.json()

if 'error' in auth_result:
    print(f"Error during authentication: {auth_result['error']}")
else:
    token = auth_result['token']
    print(f"Authentication successful! Token: {token}")

    create_table_url = 'http://localhost:5000/createtable'
    
    create_table_data = {
        "id": "2f55e742-75e6-47c6-b665-6cdf148f0aa1",
        "agent_id": "1234",
        "table_name": "ecommerce_products",
        "table_description": "Table containing information about products in an eCommerce store.",
        "table_schema": {
            "columns": [
                {"name": "product_id", "type": "INT", "description": "Unique product ID"},
                {"name": "product_name", "type": "VARCHAR(255)", "description": "Name of the product"},
                {"name": "price", "type": "DECIMAL(10, 2)", "description": "Price of the product"},
                {"name": "stock_quantity", "type": "INT", "description": "Quantity of the product in stock"}
            ]
        }
    }

    create_table_response = requests.post(create_table_url, json=create_table_data)

    if create_table_response.status_code == 200:
        print(f"Table created successfully! Schema ID: {create_table_response.json()['schema_id']}")
    else:
        print(f"Error creating table: {create_table_response.text}")

    query_url = 'http://localhost:5000/query'

    query_data = {
        "question": "stock_quantity of each product",
        "agent_id": "1234"  # The same agent_id used previously
    }

    query_response = requests.post(query_url, json=query_data)

    if query_response.status_code == 200:
        print(f"Query executed successfully! SQL Query: {query_response.json()['query']}")
    else:
        print(f"Error querying table: {query_response.text}")

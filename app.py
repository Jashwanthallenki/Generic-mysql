from flask import Flask, request, jsonify
import mysql.connector
import uuid
from dotenv import load_dotenv
import os
import json
from google.generativeai import GenerativeModel
import google.generativeai as genai
from transformers import pipeline
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from huggingface_hub import login

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

app = Flask(__name__)
genai.configure(api_key=GENAI_API_KEY)


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    agent_id = data.get('agent_id')
    
    if not agent_id:
        return jsonify({"error": "Agent ID is required."}), 400
    
    token = str(uuid.uuid4())
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO auth_token (id, agent_id, token) VALUES (%s, %s, %s)",
            (str(uuid.uuid4()), agent_id, token)
        )
        connection.commit()
        return jsonify({"token": token}), 200
    except Exception as e:
        return jsonify({"error": "Error generating auth token.", "details": str(e)}), 500

@app.route('/createtable', methods=['POST'])
def create_table():
    data = request.json
    table_name = data.get('table_name')
    table_description = data.get('table_description')
    table_schema = data.get('table_schema')
    agent_id = data.get('agent_id')
    
    if not table_name or not table_schema or not agent_id:
        return jsonify({"error": "Table name, schema, and agent ID are required."}), 400
    
    schema_id = str(uuid.uuid4())
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO table_schemas (id, agent_id, table_name, table_description, table_schema) VALUES (%s, %s, %s, %s, %s)",
            (schema_id, agent_id, table_name, table_description, json.dumps(table_schema))
        )
        connection.commit()
        return jsonify({"message": "Table schema saved successfully.", "schema_id": schema_id}), 200
    except Exception as e:
        return jsonify({"error": "Error saving schema.", "details": str(e)}), 500
    finally:
        if connection.is_connected():
            connection.close()

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    agent_id = data.get('agent_id')
    
    if not question or not agent_id:
        return jsonify({"error": "Question and agent ID are required."}), 400
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT table_schema FROM table_schemas WHERE agent_id = %s", (agent_id,))
        print("working")
        schema_row = cursor.fetchone()
        
        if not schema_row:
            return jsonify({"error": "No schema found for the agent."}), 400
        
        table_schema = schema_row["table_schema"]
        prompt = f"""
        Your an expert in converting english text to mysql queries
        Based on the table schema: {table_schema}, convert the following question to mysql query:
        "{question}"
        """

        model = genai.GenerativeModel(model_name="gemini-1.5-pro")

        response = model.generate_content(prompt)

        sql_query = response.text

        if sql_query.startswith("```sql"):
            sql_query = sql_query[7:].strip()
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3].strip()

        sql_query = sql_query.replace("\n", " ").strip()
        sql_query = sql_query.replace(",", " ").strip()
        
        return jsonify({"query": sql_query}), 200
    except Exception as e:
        return jsonify({"error": "Error executing query.", "details": str(sql_query)}), 500

if __name__ == '__main__':
    app.run(debug=True)

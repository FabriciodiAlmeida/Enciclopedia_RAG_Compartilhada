# api/rag_endpoint.py (API Serverless)
import os
import json
from flask import Flask, jsonify, request
from supabase import create_client
from google import genai
from google.genai.errors import APIError
from langchain_core.prompts import ChatPromptTemplate

# Define o objeto Flask que será executado pelo Vercel
app = Flask(__name__) 

# --- CONFIGURAÇÃO ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
TABLE_NAME = "champlim"


# --------------------------------------------------------------------------
# FUNÇÃO DE BUSCA RAG (Lógica Central)
# --------------------------------------------------------------------------
def ask_rag(query):
    
    # 1. INICIALIZAÇÃO DE CLIENTES
    if not SUPABASE_URL or not SUPABASE_KEY or not GEMINI_API_KEY:
        missing = [k for k, v in [("SUPABASE_URL", SUPABASE_URL), ("SUPABASE_KEY", SUPABASE_KEY), ("GEMINI_API_KEY", GEMINI_API_KEY)] if not v]
        error_msg = f"FALHA CRÍTICA: Variáveis de ambiente faltando: {', '.join(missing)}. Configure-as no Vercel."
        return error_msg
        
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        return f"FALHA CRÍTICA: Erro ao criar clientes Supabase/Gemini: {e}"


    # 2. CRIAÇÃO DO EMBEDDING 
    try:
        embedding_response = gemini_client.models.embed_content(
            model='models/embedding-001', 
            contents=[query] 
        )
        query_vector = embedding_response['embedding']
    except APIError as e:
        return f"Erro na API do Google ao criar o vetor: {e}"


    # 3. CHAMADA RPC AO SUPABASE 
    try:
        rpc_params = {
            'query_embedding': query_vector,
            'match_count': 90    
        }
        response = supabase_client.rpc('vector_search', rpc_params).execute()

        context = ""
        if response.data:
            for item in response.data:
                metadata = item.get('metadata', {})
                page = metadata.get('page')
                file_name_col = item.get('file_name', 'R. N. Champlin - Enciclopédia')
                source = f" (Fonte: {file_name_col}, Página: {page})" if page is not None else f" (Fonte: {file_name_col})"
                context += item.get('content', '') + source + "\n\n---\n\n"
        else:
            return "Desculpe, a busca vetorial não encontrou contexto relevante nos volumes indexados."
    except Exception as e:
        return f"Erro ao acessar o Supabase RPC: {e}"


    # 4. CHAMADA AO MODELO
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente de estudo bíblico. Use o CONTEXTO fornecido para responder à PERGUNTA. Se a resposta não estiver no contexto, diga 'CONTEXTO NÃO ENCONTRADO'. Inclua as fontes (Página e Arquivo) no final de cada resposta."),
        ("user", "CONTEXTO: {context}\n\nPERGUNTA: {question}")
    ])
    
    prompt_formatted = prompt.format(context=context, question=query)
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_formatted
        )
        return response.text
    except APIError as e:
        return f"Erro na API do Google ao gerar a resposta: {e}"


# --- ROTA DA API ---

@app.route("/rag_endpoint", methods=["POST"])
def rag_endpoint_route(): 
    
    try:
        if request.method != 'POST':
            return jsonify({'answer': 'Método não permitido.'}), 405

        request_data = request.json
        if request_data is None:
            request_body_text = request.data.decode('utf-8')
            request_data = json.loads(request_body_text)

        if request_data is None or 'query' not in request_data or not request_data['query']:
            return jsonify({'answer': 'Nenhuma pergunta válida fornecida.'}), 400

        user_query = request_data['query']
            
    except Exception as e:
        return jsonify({'answer': f'Erro interno ao ler JSON: {e}'}), 500

    final_answer = ask_rag(user_query)

    if final_answer.startswith("FALHA CRÍTICA") or final_answer.startswith("Erro"):
        return jsonify({"answer": final_answer}), 500
        
    return jsonify({"answer": final_answer}), 200

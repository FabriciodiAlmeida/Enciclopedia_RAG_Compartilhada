# api/rag_endpoint.py (VERSÃO FINAL LEVE PARA VERCEL)
import os
import json
from flask import Flask, jsonify, request
from supabase import create_client
import requests # NOVO: Cliente HTTP leve
from langchain_core.prompts import ChatPromptTemplate

# Define o objeto Flask
app = Flask(__name__) 

# --- CONFIGURAÇÃO ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
TABLE_NAME = "champlim"
# URL do endpoint de embedding do Gemini
EMBEDDING_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent"
# URL do endpoint de geração de conteúdo do Gemini
GENERATION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
HEADERS = {
    "Content-Type": "application/json"
}

# --------------------------------------------------------------------------
# FUNÇÃO DE BUSCA RAG (Lógica Central)
# --------------------------------------------------------------------------
def ask_rag(query):
    
    # 1. INICIALIZAÇÃO DE CLIENTES (Checagem de chaves)
    if not SUPABASE_URL or not SUPABASE_KEY or not GEMINI_API_KEY:
        missing = [k for k, v in [("SUPABASE_URL", SUPABASE_URL), ("SUPABASE_KEY", SUPABASE_KEY), ("GEMINI_API_KEY", GEMINI_API_KEY)] if not v]
        error_msg = f"FALHA CRÍTICA: Variáveis de ambiente faltando: {', '.join(missing)}."
        return error_msg
        
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return f"FALHA CRÍTICA: Erro ao criar cliente Supabase: {e}"


    # 2. CRIAÇÃO DO EMBEDDING (USANDO REQUESTS)
    try:
        embedding_payload = {
            "requests": [
                {
                    "model": "embedding-001",
                    "content": {"parts": [{"text": query}]}
                }
            ]
        }
        
        # Chamada HTTP para criar o vetor
        response = requests.post(
            f"{EMBEDDING_URL}?key={GEMINI_API_KEY}", 
            headers=HEADERS, 
            json=embedding_payload
        )
        response.raise_for_status()
        
        # Extrai o vetor
        response_json = response.json()
        query_vector = response_json['embeddings'][0]['values']
        
    except requests.exceptions.HTTPError as e:
        return f"Erro HTTP no Embedding (código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro desconhecido ao criar embedding: {e}"


    # 3. CHAMADA RPC AO SUPABASE (Inalterado)
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


    # 4. CHAMADA AO MODELO (USANDO REQUESTS)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente de estudo bíblico. Use o CONTEXTO fornecido para responder à PERGUNTA. Se a resposta não estiver no contexto, diga 'CONTEXTO NÃO ENCONTRADO'. Inclua as fontes (Página e Arquivo) no final de cada resposta."),
        ("user", "CONTEXTO: {context}\n\nPERGUNTA: {question}")
    ])
    
    prompt_formatted = prompt.format(context=context, question=query)
    
    try:
        generation_payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt_formatted}]}
            ]
        }
        
        # Chamada HTTP para gerar o conteúdo
        response = requests.post(
            f"{GENERATION_URL}?key={GEMINI_API_KEY}", 
            headers=HEADERS, 
            json=generation_payload
        )
        response.raise_for_status()
        
        # Extrai o texto da resposta
        response_json = response.json()
        return response_json['candidates'][0]['content']['parts'][0]['text']
        
    except requests.exceptions.HTTPError as e:
        return f"Erro HTTP na Geração (código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro desconhecido ao gerar a resposta: {e}"


# --- ROTA DA API (Inalterado) ---

@app.route("/rag_endpoint", methods=["POST"])
def rag_endpoint_route(): 
    
    try:
        if request.method != 'POST':
            return jsonify({'answer': 'Método não permitido.'}), 405

        request_data = request.json
        if request_data is None:
            # Tenta decodificar o corpo da requisição bruta se request.json for None
            request_body_text = request.data.decode('utf-8')
            request_data = json.loads(request_body_text)

        if request_data is None or 'query' not in request_data or not request_data['query']:
            # Seu frontend Streamlit está no Cloud, mas o backend (o Cloud Run, que agora é o Vercel)
            # estava retornando erro, ou o frontend parou de enviar o JSON correto
            return jsonify({'answer': 'Nenhuma pergunta válida fornecida. O Streamlit precisa enviar um JSON com {"query": "sua pergunta"}.'}), 400

        user_query = request_data['query']
            
    except Exception as e:
        return jsonify({'answer': f'Erro interno ao ler JSON: {e}'}), 500

    final_answer = ask_rag(user_query)

    if final_answer.startswith("FALHA CRÍTICA") or final_answer.startswith("Erro"):
        return jsonify({"answer": final_answer}), 500
        
    return jsonify({"answer": final_answer}), 200

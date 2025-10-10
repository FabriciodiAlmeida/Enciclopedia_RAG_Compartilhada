# app.py: CÓDIGO FINAL E ESTÁVEL PARA STREAMLIT
# Substitua TODO o seu arquivo app.py por este código.

import os
import streamlit as st
from supabase.client import Client, create_client
from google import genai
from google.genai.errors import APIError
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Carrega variáveis de ambiente (para teste local)
load_dotenv()

# --------------------------------------------------------------------------
# 1. CONFIGURAÇÕES E CHAVES (Leitura do Streamlit Secrets)
# Usamos try/except para tentar ler as chaves que você configurou
# --------------------------------------------------------------------------

# Tenta ler as chaves em MAIÚSCULAS e MINÚSCULAS
try:
    GEMINI_API_KEY_SECRET = st.secrets.get("gemini_api_key") or st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets.get("supabase_url") or st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets.get("supabase_key") or st.secrets["SUPABASE_KEY"]
except KeyError:
    # Se der erro no secrets, tenta ler as variáveis de ambiente (para teste local)
    GEMINI_API_KEY_SECRET = os.environ.get("GEMINI_API_KEY") 
    SUPABASE_URL = os.environ.get("SUPABASE_URL") 
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") 
    
if not GEMINI_API_KEY_SECRET or not SUPABASE_URL:
    st.error("Erro: As chaves de API (GEMINI/SUPABASE) não foram configuradas corretamente nos Streamlit Secrets.")
    st.stop()

# Define a variável de ambiente (necessária para o cliente Gemini)
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY_SECRET
TABLE_NAME = "champlim"


# --------------------------------------------------------------------------
# 2. CLIENTES E EMBEDDER (Usando o Cliente Puro do Google)
# --------------------------------------------------------------------------
@st.cache_resource
def initialize_clients():
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Inicializa o cliente Google com a chave lida (muito mais estável)
    gemini_client = genai.Client(api_key=GEMINI_API_KEY_SECRET)
    
    return supabase_client, gemini_client

supabase, gemini_client = initialize_clients()


# --------------------------------------------------------------------------
# 3. FUNÇÃO DE BUSCA RAG (Lógica Final Estável)
# --------------------------------------------------------------------------
def ask_rag(query):
    
    # 1. CRIAÇÃO DO EMBEDDING (Substitui o HuggingFace)
    try:
        embedding_response = gemini_client.models.embed_content(
            model='models/embedding-001', 
            content=query
        )
        # O formato da resposta é ligeiramente diferente do HuggingFace
        query_vector = embedding_response['embedding']
    except APIError as e:
        return f"Erro na API do Google ao criar o vetor de busca: {e}"


    # 2. CHAMADA RPC AO SUPABASE (Busca Vetorial k=40)
    rpc_params = {
        'query_embedding': query_vector,
        'match_count': 40  # K=40, o valor estável para o free tier
    }
    response = supabase.rpc('vector_search', rpc_params).execute()

    context = ""
    if response.data:
        for item in response.data:
            metadata = item.get('metadata', {})
            page = metadata.get('page')
            
            # Fonte CORRIGIDA: Lendo a coluna 'file_name' (que corrigimos no SQL)
            file_name_col = item.get('file_name', 'R. N. Champlin - Enciclopédia')
            
            source = f" (Fonte: {file_name_col}, Página: {page})" if page is not None else f" (Fonte: {file_name_col})"
            
            context += item.get('content', '') + source + "\n\n---\n\n"
    else:
        return "Desculpe, a busca vetorial não encontrou contexto relevante nos volumes indexados."


    # 3. CHAMADA AO MODELO (Usando o cliente puro do Google)
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


# --------------------------------------------------------------------------
# 4. INTERFACE STREAMLIT
# --------------------------------------------------------------------------
st.set_page_config(page_title="Enciclopédia Bíblica RAG", layout="wide")
st.title("📚 Café com Biblia")
st.markdown("Faça uma pergunta ou deixe uma referência biblica.")

# Coluna para a entrada do usuário
user_query = st.text_area("Sua Pergunta de Estudo Bíblico:", key="query_input")

if st.button("Buscar Resposta", use_container_width=True):
    if user_query:
        with st.spinner("Buscando e analisando o contexto nos 13 volumes..."):
            # Chama a função principal
            answer = ask_rag(user_query)
        
        # Exibe a resposta formatada
        st.subheader("Resposta da Enciclopédia:")
        st.markdown(answer)
    else:
        st.warning("Por favor, digite uma pergunta.")

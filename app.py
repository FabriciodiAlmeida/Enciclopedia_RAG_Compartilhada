# app.py (Código RAG Estável Final)

# 1. INSTALAÇÕES E CONFIGURAÇÕES
import os
import streamlit as st
from supabase.client import Client, create_client
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Carrega variáveis de ambiente (se estiver usando .env localmente)
load_dotenv()

# --- 2. VARIÁVEIS DE AMBIENTE E SECRETS ---
# Use st.secrets para implantar no Streamlit Cloud ou os.environ para rodar localmente
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or st.secrets["GOOGLE_API_KEY"] 

os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
TABLE_NAME = "champlim"

# Inicializar clientes (usando st.cache_resource para não recriar a cada interação)
# Isso é crucial para o desempenho do Streamlit
@st.cache_resource
def initialize_clients():
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Reutilize o embedder all-MiniLM-l6-v2
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-l6-v2")
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return supabase_client, embedder, model

supabase, embedder, model = initialize_clients()

# -------------------------------------------------------------
# 3. FUNÇÃO DE BUSCA RAG (k=40) - Lógica de Backend
# -------------------------------------------------------------
def ask_rag(query):
    query_vector = embedder.embed_query(query)

    rpc_params = {
        'query_embedding': query_vector,
        'match_count': 40  # K=40 para evitar timeout no free tier (problema resolvido)
    }

    # Chama RPC (função vector_search)
    response = supabase.rpc('vector_search', rpc_params).execute()

    context = ""
    if response.data:
        for item in response.data:
            metadata = item.get('metadata', {})
            page = metadata.get('page')
            
            # Fonte CORRIGIDA: Lendo a coluna 'file_name' (que corrigimos no SQL)
            file_name_col = item.get('file_name', 'R. N. Champlin - Enciclopédia')
            
            # Formatação final da fonte
            source = f" (Fonte: {file_name_col}, Página: {page})" if page is not None else f" (Fonte: {file_name_col})"
            
            context += item.get('content', '') + source + "\n\n---\n\n"
    else:
        # Retorna mensagem se a busca não encontrar nada
        return "Desculpe, não encontrei informações relevantes em meus volumes indexados."


    # Prompt e Chamada ao Gemini
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente de estudo bíblico. Use o CONTEXTO fornecido para responder à PERGUNTA. Priorize a informação que corresponde a qualquer referência bíblica ou tema específico mencionado na PERGUNTA. Se a resposta não estiver no contexto, diga 'CONTEXTO NÃO ENCONTRADO'. Inclua as fontes (Página e Arquivo) no final de cada resposta."),
        ("user", "CONTEXTO: {context}\n\nPERGUNTA: {question}")
    ])
    
    chain = prompt | model
    result = chain.invoke({"context": context, "question": query})

    return result.content


# -------------------------------------------------------------
# 4. INTERFACE STREAMLIT
# -------------------------------------------------------------
st.set_page_config(page_title="Enciclopédia Bíblica RAG", layout="wide")
st.title("📚 Enciclopédia Bíblica R. N. Champlin")
st.markdown("Faça uma pergunta profunda sobre qualquer um dos 13 volumes indexados.")

# Coluna para a entrada do usuário
user_query = st.text_input("Sua Pergunta de Estudo Bíblico:", key="query_input")

if st.button("Buscar Resposta"):
    if user_query:
        # Use um container para o spinner e para a resposta
        with st.spinner("Buscando e analisando o contexto nos 13 volumes..."):
            # Chama a função principal de RAG
            answer = ask_rag(user_query)
        
        # Exibe a resposta formatada
        st.subheader("Resposta da Enciclopédia:")
        st.markdown(answer)
    else:
        st.warning("Por favor, digite uma pergunta.")

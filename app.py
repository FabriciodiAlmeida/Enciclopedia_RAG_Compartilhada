# app.py (CÓDIGO COMPLETO FINAL PARA O STREAMLIT)

import streamlit as st
import requests  # NECESSÁRIO para chamar o Cloud Run
import os

# --- CONFIGURAÇÃO DA CHAVE SECRETA (AGORA É SOMENTE A URL DO ENDPOINT) ---

# Pega a URL do servidor RAG do Streamlit Secrets
# O Streamlit monta os secrets em um dicionário acessível via st.secrets.get()
RAG_ENDPOINT_URL = st.secrets.get("RAG_ENDPOINT_URL")

# --- FUNÇÃO PRINCIPAL (AGORA É APENAS UM CLIENTE HTTP) ---
def ask_rag(query):
    """
    Faz uma chamada HTTP POST para o servidor Cloud Run/GCF.
    """
    if not RAG_ENDPOINT_URL:
        return "Erro de Configuração: RAG_ENDPOINT_URL não encontrado nos segredos do Streamlit. Por favor, adicione a URL do Cloud Run."
        
    try:
        # Adiciona o segmento de rota para o endpoint que configuramos
        url_com_endpoint = RAG_ENDPOINT_URL + "/rag_endpoint"
        
        # Envia a pergunta do usuário como JSON para o servidor
        response = requests.post(
            url_com_endpoint, 
            json={'query': query}
        )
        response.raise_for_status() # Lança exceção para erros 4xx/5xx

        # Retorna a resposta JSON (que contém a chave 'answer' enviada pelo Cloud Run)
        return response.json().get('answer', "Resposta inválida do servidor.")

    except requests.exceptions.HTTPError as e:
        # Captura erros do servidor Cloud Run (ex: 500)
        return f"Erro no Servidor RAG (HTTP): {e}. Verifique os logs do Cloud Run para detalhes."
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: O servidor RAG não está acessível. Verifique se a URL do endpoint está correta."
    except Exception as e:
        return f"Erro inesperado ao conectar ao Servidor RAG: {e}"

# -------------------------------------------------------------
# ESTRUTURA E LAYOUT DO STREAMLIT 
# -------------------------------------------------------------

# Esta é a linha onde o erro de sintaxe está ocorrendo no seu código (provavelmente porque foi colocado 
# após um 'try' sem um 'except' ou 'finally' correspondente).
st.set_page_config(page_title="Enciclopédia RAG Champlin", layout="centered")

# --- Cabeçalho ---
st.title("📖 Café com Bíblia")
st.write("Faça uma pergunta ou deixe uma referência bíblica.")
st.caption("Sua Pergunta de Estudo Bíblico:")

# --- Caixa de Chat e Lógica de Entrada ---
user_query = st.text_input(
    label="Sua Pergunta de Estudo Bíblico:",
    label_visibility="collapsed",
    placeholder="Qual a explicação para o fratricídio de Caim contra Abel conforme a enciclopédia?",
    key="user_query"
)

# --- Botão e Chamada RAG ---
if st.button("Buscar Resposta"):
    if user_query:
        # Certifique-se de que a URL do endpoint foi configurada
        if not RAG_ENDPOINT_URL:
            st.error("Erro: A URL do servidor RAG não foi configurada nos segredos do Streamlit.")
        else:
            with st.spinner("Buscando e processando a resposta do Cloud Run..."):
                answer = ask_rag(user_query)
            
            # Exibe a resposta formatada
            st.subheader("Resposta da Enciclopédia:")
            st.write(answer)
    else:
        st.error("Por favor, digite uma pergunta.")

# --- Fim do layout ---

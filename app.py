import streamlit as st
import requests  # Certifique-se de ter 'requests' no seu requirements.txt do Streamlit

# --- CONFIGURAÇÃO DA CHAVE SECRETA (AGORA É SOMENTE A URL DO ENDPOINT) ---
# Você deve criar uma nova linha no seu secrets.toml para esta URL.
# O Streamlit já tem 'requests' e o novo código abaixo o usa.

# 1. PEGAR A URL DO SERVIDOR RAG NO GOOGLE CLOUD
RAG_ENDPOINT_URL = st.secrets.get("RAG_ENDPOINT_URL")

# --- FUNÇÃO PRINCIPAL (AGORA É APENAS UM CLIENTE HTTP) ---
def ask_rag(query):
    """
    Faz uma chamada HTTP POST para o servidor Cloud Run/GCF para obter a resposta RAG.
    """
    if not RAG_ENDPOINT_URL:
        return "Erro de Configuração: RAG_ENDPOINT_URL não encontrado nos segredos do Streamlit."
        
    try:
        # Adiciona o segmento de rota para o endpoint que configuramos
        url_com_endpoint = RAG_ENDPOINT_URL + "/rag_endpoint"
        
        # Envia a pergunta do usuário como JSON para o servidor
        response = requests.post(
            url_com_endpoint, 
            json={'query': query}
        )
        response.raise_for_status() # Lança exceção para erros 4xx/5xx

        # Retorna a resposta JSON (que contém a chave 'answer')
        return response.json().get('answer', "Resposta inválida do servidor.")

    except requests.exceptions.HTTPError as e:
        # Captura erros do servidor Cloud Run (ex: 500)
        return f"Erro no Servidor RAG (HTTP): {e}. Tente novamente."
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: O servidor RAG não está acessível ou a URL está errada."
    except Exception as e:
        return f"Erro inesperado ao conectar ao Servidor RAG: {e}"

# O restante do seu Streamlit app.py (layout, st.chat_input, etc.) continua o mesmo!

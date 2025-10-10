# app.py (Seu Frontend Streamlit)
import streamlit as st
import requests
import json
import os

# --- CONFIGURAÇÃO DA API ---
# AGORA COM A URL CORRETA DO VERCEL
VERCEL_API_URL = "https://enciclopedia-rag-compartilhada.vercel.app/rag_endpoint" 


# --- FUNÇÃO DE CHAMADA (O restante do código que funciona) ---
def buscar_resposta(pergunta):
    """Envia a pergunta para a API RAG no Vercel."""
    
    # 1. Checagem de URL (Removida a checagem que causava erro)

    # 2. Chamada HTTP
    try:
        payload = {"query": pergunta}
        response = requests.post(VERCEL_API_URL, json=payload, timeout=90)
        response.raise_for_status() 
        
        # 3. Processamento da Resposta
        resposta_json = response.json()
        return resposta_json.get("answer", "A API não retornou o campo 'answer'.")

    except requests.exceptions.HTTPError as e:
        if response.status_code == 500:
            return f"Erro no Servidor RAG (500): {response.json().get('answer', 'Erro interno do servidor Vercel. Verifique os logs.')}"
        else:
            return f"Erro na Requisição RAG ({response.status_code}): {response.text}"
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: Não foi possível alcançar a API do Vercel. Verifique a URL e o status do deploy."
    except Exception as e:
        return f"Erro Inesperado: {e}"


# --- INTERFACE STREAMLIT (Inalterada) ---
st.set_page_config(page_title="Café com Bíblia", layout="centered")
st.title("📚 Café com Bíblia 📚")
st.markdown("Faça uma pergunta ou deixe uma referência bíblica.")

pergunta_usuario = st.text_input("Sua Pergunta de Estudo Bíblico:", 
                                 placeholder="")

if st.button("Buscar Resposta"):
    if pergunta_usuario:
        with st.spinner("Consultando Enciclopédia Champlin..."):
            resposta = buscar_resposta(pergunta_usuario)
            
            st.subheader("Resposta da Enciclopédia:")
            st.write(resposta)
    else:
        st.error("Por favor, digite uma pergunta válida.")

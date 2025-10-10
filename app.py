# app.py (Novo Frontend Streamlit)
import streamlit as st
import requests
import json
import os

# --- CONFIGURAÇÃO DA API ---
# COLOQUE SUA URL REAL DO VERCEL AQUI, ADICIONANDO /rag_endpoint NO FINAL
VERCEL_API_URL = "https://enciclopedia-rag-compartilhada.vercel.app/rag_endpoint" 


# --- FUNÇÃO DE CHAMADA ---
def buscar_resposta(pergunta):
    """Envia a pergunta para a API RAG no Vercel."""
    
    # 1. Checagem de URL (Verifique se a URL foi substituída)
    if VERCEL_API_URL.startswith("https://SEU-DOMÍNIO-VERCEL"):
        # Se o usuário não substituiu a URL, retorna um erro de configuração
        return "Erro de Configuração: Por favor, substitua 'SEU-DOMÍNIO-VERCEL' na linha 9 do código por sua URL real."

    # 2. Chamada HTTP
    try:
        # A API espera um corpo JSON com a chave 'query'
        payload = {"query": pergunta}
        
        # Faz a chamada POST para o Vercel
        response = requests.post(VERCEL_API_URL, json=payload, timeout=90)
        
        # Levanta exceção para códigos de status 4xx/5xx
        response.raise_for_status() 
        
        # 3. Processamento da Resposta
        resposta_json = response.json()
        return resposta_json.get("answer", "A API não retornou o campo 'answer'.")

    except requests.exceptions.HTTPError as e:
        # Erros 4xx/5xx (que incluem os erros da API)
        if response.status_code == 500:
            # Retorna a mensagem de erro que a API enviou (Ex: FALHA CRÍTICA)
            return f"Erro no Servidor RAG (500): {response.json().get('answer', 'Erro interno do servidor Vercel. Verifique os logs.')}"
        else:
            return f"Erro na Requisição RAG ({response.status_code}): {response.text}"
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: Não foi possível alcançar a API do Vercel. Verifique a URL e o status do deploy."
    except Exception as e:
        return f"Erro Inesperado: {e}"


# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Café com Bíblia", layout="centered")
st.title("📚 Café com Bíblia ☕")
st.markdown("Faça uma pergunta ou deixe uma referência bíblica.")

# Caixa de entrada do usuário
pergunta_usuario = st.text_input("Sua Pergunta de Estudo Bíblico:", 
                                 placeholder="Ex: Qual o nome do Filho do Sacerdote Zacarias?")

# Botão de busca
if st.button("Buscar Resposta"):
    if pergunta_usuario:
        with st.spinner("Consultando Enciclopédia Champlin..."):
            resposta = buscar_resposta(pergunta_usuario)
            
            st.subheader("Resposta da Enciclopédia:")
            # Exibe a resposta (ou o erro)
            st.write(resposta)
    else:
        st.error("Por favor, digite uma pergunta válida.")

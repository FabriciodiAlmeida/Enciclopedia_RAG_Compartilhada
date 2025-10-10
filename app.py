import streamlit as st
import requests
import json

# --- CONFIGURAÇÃO DA API ---
# SUBSTITUA ESTA URL PELA SUA URL REAL DO VERCEL
VERCEL_API_URL = "https://enciclopedia-rag-compartilhada.vercel.app/rag_endpoint" 


# --- FUNÇÃO DE CHAMADA ---
def buscar_resposta(pergunta):
    """Envia a pergunta para a API RAG no Vercel."""
    
    # 1. Checagem de URL
    if VERCEL_API_URL.startswith("https://[SEU-DOMÍNIO-VERCEL]"):
        return "Erro de Configuração: Por favor, substitua [SEU-DOMÍNIO-VERCEL] na linha 9 do código."

    # 2. Chamada HTTP
    try:
        # A API espera um corpo JSON com a chave 'query'
        payload = {"query": pergunta}
        
        response = requests.post(VERCEL_API_URL, json=payload, timeout=60)
        
        # Levanta exceção para códigos de status 4xx/5xx
        response.raise_for_status() 
        
        # 3. Processamento da Resposta
        resposta_json = response.json()
        return resposta_json.get("answer", "A API não retornou o campo 'answer'.")

    except requests.exceptions.HTTPError as e:
        # Erros 4xx/5xx
        return f"Erro no Servidor RAG ({response.status_code}): {response.json().get('answer', 'Erro interno do servidor.')}"
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: Não foi possível alcançar a API do Vercel. Verifique a URL e o status do deploy."
    except Exception as e:
        return f"Erro Inesperado: {e}"


# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Café com Bíblia", layout="centered")
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Stack_of_books_01.svg/1200px-Stack_of_books_01.svg.png", width=60)
st.title("📚 Café com Bíblia 📚")
st.markdown("Faça uma pergunta ou deixe uma referência bíblica.")

# Caixa de entrada do usuário
pergunta_usuario = st.text_input("Sua Pergunta de Estudo Bíblico:", 
                                 placeholder="")

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

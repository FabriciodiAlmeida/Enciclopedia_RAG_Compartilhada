import streamlit as st
import requests  # Importar esta biblioteca!

# --- CONFIGURAÇÃO DA CHAVE SECRETA (AGORA É SOMENTE A URL DO ENDPOINT) ---

# 1. PEGAR A URL DO SERVIDOR RAG NO GOOGLE CLOUD
# Esta chave deve ser criada no painel Secrets do Streamlit
RAG_ENDPOINT_URL = st.secrets.get("RAG_ENDPOINT_URL")

# --- FUNÇÃO PRINCIPAL (AGORA É APENAS UM CLIENTE HTTP) ---
def ask_rag(query):
    """
    Faz uma chamada HTTP POST para o servidor Cloud Run/GCF para obter a resposta RAG.
    """
    if not RAG_ENDPOINT_URL:
        # Mensagem de erro clara se a chave não estiver configurada
        return "Erro de Configuração: RAG_ENDPOINT_URL não encontrado nos segredos do Streamlit. Por favor, adicione a URL do Cloud Run."
        
    try:
        # Adiciona o segmento de rota para o endpoint que configuramos
        # Se sua URL do Cloud Run for '...run.app', a chamada será '...run.app/rag_endpoint'
        url_com_endpoint = RAG_ENDPOINT_URL + "/rag_endpoint"
        
        # Envia a pergunta do usuário como JSON para o servidor
        response = requests.post(
            url_com_endpoint, 
            json={'query': query}
        )
        response.raise_for_status() # Lança exceção para erros 4xx/5xx

        # Seu código app.py deve ter a função ask_rag de cliente HTTP que te passei ANTES desta seção.

# -------------------------------------------------------------
# ESTRUTURA E LAYOUT DO STREAMLIT (Adicione isso se não existir)
# -------------------------------------------------------------

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
        with st.spinner("Buscando e processando a resposta do Cloud Run..."):
            # A chamada agora usa a função que envia a requisição HTTP
            answer = ask_rag(user_query)
        
        # Exibe a resposta formatada
        st.subheader("Resposta da Enciclopédia:")
        st.write(answer)
    else:
        st.error("Por favor, digite uma pergunta.")

# --- Fim do layout ---

        # Retorna a resposta JSON (que contém a chave 'answer' enviada pelo Cloud Run)
        return response.json().get('answer', "Resposta inválida do servidor.")

    except requests.exceptions.HTTPError as e:
        # Captura erros do servidor Cloud Run (ex: 500)
        return f"Erro no Servidor RAG (HTTP): {e}. Verifique os logs do Cloud Run para detalhes."
    except requests.exceptions.ConnectionError:
        return "Erro de Conexão: O servidor RAG não está acessível. Verifique se a URL do endpoint está correta."
    except Exception as e:
        return f"Erro inesperado ao conectar ao Servidor RAG: {e}"

# O restante do seu Streamlit app.py (layout, st.chat_input, etc.) continua o mesmo!


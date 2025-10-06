import streamlit as st
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DE CHAVES E CONEXÃO (LENDO DE secrets do Streamlit de forma simples) ---
try:
    # Lendo as chaves como variáveis de ambiente planas
    # Estas chaves devem estar no painel de Secrets do Streamlit Cloud no formato: CHAVE="VALOR"
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    SUPABASE_TABLE_NAME = st.secrets["SUPABASE_TABLE_NAME"]
    
except KeyError as e:
    # Se a leitura falhar, exibe a mensagem de erro e evita que o programa continue.
    st.error(f"Erro ao ler chave essencial: {e}. Verifique o painel de Secrets no Streamlit Cloud (Settings -> Secrets) e use APENAS o formato plano (chave=valor).")
    st.stop()
except Exception as e:
    st.error(f"Ocorreu um erro inesperado na leitura das chaves: {e}")
    st.stop()


# --- 2. CONFIGURAÇÃO DO MODELO RAG ---

# Inicializa o cliente Supabase para o Vector Store
# O cliente usa as chaves lidas acima.
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"O sistema não pode se conectar ao banco de dados. Verifique a URL e a KEY do Supabase no painel de Secrets. Erro: {e}")
    st.stop()

# Inicializa o Vector Store com o nome do argumento que a versão 0.1.15 aceita
embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004", google_api_key=GEMINI_API_KEY)
vectorstore = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name=SUPABASE_TABLE_NAME,
    query_content_column="content", # Argumento CORRETO para a versão LangChain
)
retriever = vectorstore.as_retriever()

# Configura o modelo Gemini para a resposta
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.0)

# Cria a cadeia de Recuperação e Geração (RAG)
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=False  # Não retorna os documentos de origem na aplicação
)

# --- 3. INTERFACE STREAMLIT ---

st.set_page_config(page_title="Enciclopédia Bíblica: Pergunte ao Gemini", layout="wide")

st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            height: 3em;
            background-color: #6495ED; 
            color: white;
            font-size: 1.1em;
            border-radius: 8px;
            border: none;
        }
    </style>
""", unsafe_allow_html=True)


st.title("📚 Enciclopédia Bíblica: Pergunte ao Gemini")
st.markdown("Acesse todo o conteúdo da enciclopédia para obter respostas detalhadas e verificadas.")

# Campo de entrada para a pergunta do usuário
pergunta = st.text_input("Digite sua pergunta aqui:", placeholder="Ex: Qual a importância da Arca da Aliança e onde ela é mencionada pela última vez?")

# Botão de busca
if st.button("Buscar Resposta"):
    if pergunta:
        with st.spinner("Buscando e gerando resposta..."):
            try:
                # Executa a cadeia RAG
                resposta = qa.invoke(pergunta)
                
                # Exibe a resposta formatada
                st.subheader("Resposta do Gemini")
                st.markdown(resposta["result"])

            except Exception as e:
                # Se o Supabase falhar *após* a conexão inicial, o erro aparece aqui
                st.error(f"Erro ao gerar a resposta. Por favor, tente novamente ou verifique as chaves de API e Supabase. Detalhe do erro: {e}")
    else:
        st.warning("Por favor, digite uma pergunta.")

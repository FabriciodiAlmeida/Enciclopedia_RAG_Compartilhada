# app.py: CÓDIGO FINAL E COMPLETO PARA APLICAÇÃO WEB (STREAMLIT)

import os
import streamlit as st
from supabase import create_client
from langchain_community.vectorstores import SupabaseVectorStore 
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# --- 1. CONFIGURAÇÃO DE CHAVES E CONEXÃO (LENDO DE secrets do Streamlit de forma SIMPLES) ---
try:
    # Lendo as chaves como variáveis de ambiente planas e EXIGINDO a leitura aninhada
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # A leitura ABAIXO só funciona se o painel tiver a seção [supabase]
    SUPABASE_URL = st.secrets["supabase"]["URL"]
    SUPABASE_KEY = st.secrets["supabase"]["KEY"]
    SUPABASE_TABLE_NAME = st.secrets["supabase"]["TABLE_NAME"]
    
except KeyError as e:
    st.error(f"Erro ao ler chave essencial: {e}. Verifique se o painel de Secrets (Settings -> Secrets) contém a chave exata e se o formato TOML é estrito (sem espaços após o sinal de =).")
    # Defina chaves vazias para evitar que o programa pare de rodar
    GEMINI_API_KEY = ""
    SUPABASE_URL = ""
    SUPABASE_KEY = ""
    SUPABASE_TABLE_NAME = "champlim"

# Cliente Supabase e Modelo de Embeddings
# O decorador @st.cache_resource garante que esta função seja rodada apenas uma vez.
@st.cache_resource
def setup_vector_store():
    """Inicializa clientes e o Vector Store, rodando apenas uma vez."""
    # Garante que as chaves estão preenchidas antes de tentar conectar
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
        
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        # Inicializa o Vector Store: Forçamos a busca pela função 'match_documents'
        vector_store = SupabaseVectorStore(
            client=supabase, 
            table_name=SUPABASE_TABLE_NAME,
            embedding=embeddings,
            query_name='match_documents' 
        )
        return vector_store
    except Exception as e:
        # st.exception(e) # Exibe o erro completo para debug
        st.error(f"Erro ao conectar ao Supabase: Verifique o URL/KEY e o índice no banco de dados.")
        return None

vector_store = setup_vector_store()

# --- 2. FUNÇÃO CENTRAL RAG ---

def ask_rag(question: str, vector_store):
    """Realiza a busca RAG e retorna a resposta do Gemini."""
    
    if not vector_store or not GEMINI_API_KEY:
        return "Erro de conexão. Verifique as configurações.", []

    # Configura o Modelo de Linguagem (Gemini)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", 
                                 temperature=0.2, 
                                 api_key=GEMINI_API_KEY)

    # ⚠️ PERSONA DO SISTEMA: Aqui você pode colocar as instruções detalhadas 
    # que você criou para seu GEM no Google AI Studio.
    system_prompt = (
        "Você é um assistente de IA especialista em teologia e história. "
        "Use o contexto fornecido da enciclopédia Champlim para responder à pergunta. "
        "Sua resposta deve ser acadêmica, clara e concisa. "
        "Se a resposta NÃO estiver no contexto fornecido, responda apenas: 'Não foi possível encontrar informação suficiente na enciclopédia para responder a esta pergunta.'"
        "\n\nContexto: {context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Configura o Retriever (Busca otimizada)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8}) 
    
    rag_chain = create_retrieval_chain(retriever, document_chain)
    
    # Executa a Cadeia
    response = rag_chain.invoke({"input": question})
    
    return response["answer"], response["context"]

# --- 3. INTERFACE STREAMLIT ---

st.set_page_config(page_title="Enciclopédia Bíblica RAG (Gemini + Supabase)", layout="wide")

st.title("📚 Enciclopédia Bíblica: Pergunte ao Gemini")
st.markdown("Acesse todo o conteúdo da enciclopédia para obter respostas detalhadas e verificadas.")

# Campo de entrada de texto
user_input = st.text_area("Digite sua pergunta aqui:", placeholder="Ex: Qual a importância da Arca da Aliança e onde ela é mencionada pela última vez?")

if st.button("Buscar Resposta"):
    if user_input:
        if not vector_store:
            st.warning("O sistema não pôde se conectar ao banco de dados. Verifique as chaves em 'secrets.toml'.")
        else:
            with st.spinner("Buscando e analisando o contexto na enciclopédia..."):
                answer, context_docs = ask_rag(user_input, vector_store)
            
            # Exibir a Resposta
            st.subheader("🤖 Resposta do Especialista")
            st.write(answer)
            
            # Exibir o Contexto Utilizado
            with st.expander("Ver Contexto Encontrado (Provas)"):
                if context_docs:
                    for doc in context_docs:
                        st.success(f"**[Fonte: {doc.metadata.get('file_name', SUPABASE_TABLE_NAME)}]**")
                        st.text(doc.page_content[:500] + "...") # Limita o preview do texto
                else:

                    st.warning("Nenhum contexto relevante foi encontrado. Tente reformular a pergunta.")











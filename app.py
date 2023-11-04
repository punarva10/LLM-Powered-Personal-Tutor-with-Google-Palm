import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator = "\n",
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = HuggingFaceBgeEmbeddings(model_name='BAAI/bge-large-en-v1.5')
    vectorstore = FAISS.from_texts(texts = text_chunks, embedding = embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = HuggingFaceHub(repo_id = "google/flan-t5-xxl", model_kwargs = {"temperature": 0.5, "max_length": 512})
    memory = ConversationBufferMemory(memory_key = 'chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = vectorstore.as_retriever(),
        memory = memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html = True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html = True)

def main():
    load_dotenv()
    st.set_page_config(page_title='DoraemonGPT')

    st.write(css, unsafe_allow_html = True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
 
    st.header("DoraemonGPT")
    user_question = st.text_input("Ask a question about the pdf:")
    if user_question:
        handle_userinput(user_question)

    #st.write(user_template.replace("{{MSG}}", "Hello doraemon"), unsafe_allow_html = True)
    #st.write(bot_template.replace("{{MSG}}", "Hello punarv"), unsafe_allow_html = True)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'", accept_multiple_files=True)

        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)
                st.write(text_chunks)

                #create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain
                st.session_state.conversation = get_conversation_chain(vectorstore)
        
if __name__ == '__main__':
    main()
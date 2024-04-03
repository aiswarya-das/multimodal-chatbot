import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.llms import OpenAI
from htmlTemplates import css, bot_template, user_template
from langchain.chains.summarize import load_summarize_chain
import os
import tempfile
import re
from langchain_community.document_loaders import PyPDFLoader
from openai import OpenAI
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()  # Concatenate text from all pages
    return text  

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain
# def handle_system_description(system_description):
#     # Process the entered system description here
#     # You can perform any required processing or analysis
#     # For now, let's just print the entered description
#     # Load environment variables from .env file
# # load_dotenv()

# # Retrieve the API key from the environment
#     openai_api_key = os.getenv("OPENAI_API_KEY")

# # Initialize OpenAI client
#     client = OpenAI(api_key=openai_api_key)
#     if "openai_model" not in st.session_state:
#         st.session_state["openai_model"] = "gpt-3.5-turbo"

#     if "messages" not in st.session_state:
#         st.session_state.messages = []

#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
#     if prompt := st.chat_input("What is up?"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)
#         with st.chat_message("assistant"):
#             stream = client.chat.completions.create(
#                 model=st.session_state["openai_model"],
#                 messages=[
#                 {"role": m["role"], "content": m["content"]}
#                 for m in st.session_state.messages
#             ],
#              stream=True,
#             )
#             response = st.write_stream(stream)
#         st.session_state.messages.append({"role": "assistant", "content": response})


#     st.write(f"System Description: {system_description}")

# def handle_userinput(user_question):
def handle_userinput(user_question):
    max_chunk_length = 500  # Adjust as needed
    chunks = [user_question[i:i+max_chunk_length] for i in range(0, len(user_question), max_chunk_length)]
    
    for chunk in chunks:
        response = st.session_state.conversation({'question': chunk})
        st.session_state.chat_history = response['chat_history']

        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)



def Generate_summary(pdfs_folder):
    llm = OpenAI()
    summaries = []
    for pdf_file in pdfs_folder:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(pdf_file.read())
        
        loader = PyPDFLoader(temp_path)
        if loader:
            docs = loader.load_and_split()
            chain = load_summarize_chain(llm, chain_type="map_reduce")
            summary = chain.run(docs)
            summaries.append(summary)
        else:
            st.error(f"Failed to load and split PDF: {pdf_file.name}")

        # Delete the temporary file
        os.remove(temp_path)
    
    return summaries


def main():
    load_dotenv()
    st.set_page_config(page_title="chatbot", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.sidebar.header("Your documents")
    pdf_docs = st.sidebar.file_uploader("Upload your PDFS here and click on 'Process'", accept_multiple_files=True)
    if pdf_docs is not None:
        if st.sidebar.button("Process"):
            with st.spinner("Processing"):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                vectorstore = get_vectorstore(text_chunks)
                st.session_state.conversation = get_conversation_chain(vectorstore)

    st.header("chatbot :books:")
    user_question = st.text_input("Ask a question")
    if user_question:
        handle_userinput(user_question)

    if pdf_docs is not None:
        if st.sidebar.button("Generate Summary"):
            summaries = Generate_summary(pdf_docs)
            if summaries:
                for i, summary in enumerate(summaries):
                    st.write(f"Summary for PDF {i+1}:")
                    # st.write(summary)
                    st.write(bot_template.replace("{{MSG}}", summary), unsafe_allow_html=True)
    # system_description = st.sidebar.text_area("Enter System Description")
    # if st.sidebar.button("Process System Description"):
    #     handle_system_description(system_description)
    #     openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    client = OpenAI(api_key=openai_api_key)
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
             stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == '__main__':
    main()

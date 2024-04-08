import streamlit as st
from dotenv import load_dotenv
import streamlit.components.v1 as components
import base64
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
import pyperclip
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

def mermaid(code: str) -> None:
    components.html(
        f"""
        <div id="mermaid-container" class="mermaid" style="height: auto;">
            {code}
        </div>

        <button id="download-btn">Download SVG</button>

        <script type="module">
            // Import Mermaid library from CDN
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            // Initialize Mermaid with specified options
            mermaid.initialize({{ startOnLoad: true ,securityLevel: 'loose',}});
            
            // Event listener for download button click
            document.getElementById('download-btn').onclick = function() {{
                // Extract SVG content from container
                const svgContent = document.getElementById('mermaid-container').innerHTML;
                // Create Blob from SVG content
                const svgBlob = new Blob([svgContent], {{ type: 'image/svg+xml' }});
                // Generate URL for Blob object
                const svgUrl = URL.createObjectURL(svgBlob);
                // Create a download link
                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;  // Set download link href
                downloadLink.download = 'diagram.svg';  // Set download file name
                // Append download link to body
                document.body.appendChild(downloadLink);
                // Simulate click on download link
                downloadLink.click();
                // Remove download link from body
                document.body.removeChild(downloadLink);
            }};

            // Dynamically adjust height of the Mermaid container
            function adjustHeight() {{
                const container = document.getElementById('mermaid-container');
                const svg = container.querySelector('svg');
                if (svg) {{
                    container.style.height = svg.getBoundingClientRect().height + 'px';
                }}
            }}

            // Adjust height when page loads
            adjustHeight();

            // Adjust height when window is resized
            window.addEventListener('resize', adjustHeight);
        </script>
        """,
        height=1500  # Default height for the Mermaid diagram
    )

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


# code for asking bot to generate mermaid diagram
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    client = OpenAI(api_key=openai_api_key)
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Input diagram description"):
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
        generate_button_visible = True  # Set to True after prompt is generated

    if st.button("Generate Diagram"):
        mermaid_code = None
    # Loop through messages in reverse order
        for message in reversed(st.session_state.messages):
            if message["role"] == "assistant":
                content = message["content"]
            # Use regular expression to find Mermaid code
                mermaid_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
                if mermaid_match:
                    mermaid_code = mermaid_match.group(1).strip()
                st.sidebar.text(mermaid_code)
                break  # Stop after finding the latest occurrence of Mermaid code

        if mermaid_code:
            # Render the Mermaid diagram using the extracted code
            mermaid(mermaid_code)
        else:
            st.sidebar.text("Mermaid code not found in the latest response")
         # Render the Mermaid diagram using the extracted code
        
if __name__ == '__main__':
    main()

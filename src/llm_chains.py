import os
import yaml
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, OpenAI

# from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


load_dotenv()

abs_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(abs_path, "../config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def get_vectordb_from_url(url: str, load_db: bool = False):
    """Stores or loads vectordb of website HTML embeddings

    Parameters
    ----------
    url : str
        Website URL
    load_db : bool, optional
        Loads existing vectordb instead of saving, by default False
    """
    # Load web HTML in document form
    loader = WebBaseLoader(url)
    documents = loader.load()

    # Split document into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["text_splitter_config"]["chunk_size"],
        chunk_overlap=config["text_splitter_config"]["chunk_overlap"],
    )
    document_chunks = text_splitter.split_documents(documents=documents)
    embeddings = OpenAIEmbeddings()

    # Store chunk embedding to vector db
    vectordb_path = config["chromadb"]["path"]
    if not os.path.exists(vectordb_path):
        os.makedirs(vectordb_path)

    if load_db:
        vectordb = Chroma(
            persist_directory=config["chromadb"]["path"],
            embedding_function=embeddings,
        )
    else:  # Save db
        vectordb = Chroma.from_documents(
            document_chunks, embeddings, persist_directory=config["chromadb"]["path"]
        )

    return vectordb


def get_context_retriever_chain(vectordb):
    """
    Creates retriever chain with memory (chat history) to get most
    relevant context from vector db.
    """
    llm = ChatOpenAI()
    retriever = vectordb.as_retriever()
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            (
                "user",
                "Given the above conversation, generate a search query to look up in order to get information relevant to information",
            ),
        ]
    )

    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    return retriever_chain


def get_rag_chain(retriever_chain):
    """
    Creates RAG chain with memory to answer user query.
    """
    llm = ChatOpenAI()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the user's question based on the below context:\n\n{context}",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ]
    )

    qry_with_documents_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever_chain, qry_with_documents_chain)

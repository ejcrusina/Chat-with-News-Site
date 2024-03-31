import os
import yaml
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

abs_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(abs_path, "../config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def validate_url_accessibility(url: str) -> bool:
    """Validates if web URL is accessible

    Parameters
    ----------
    url : str
        Website URL

    Returns
    -------
    bool
        Answers if web URL is accessible
    """
    loader = WebBaseLoader(url)
    loader.requests_kwargs = {"verify": False}
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["text_splitter_config"]["chunk_size"],
        chunk_overlap=config["text_splitter_config"]["chunk_overlap"],
    )
    document_chunks = text_splitter.split_documents(documents=documents)

    if len(document_chunks) <= 1:
        url_accessible = False
    else:
        url_accessible = True

    return url_accessible

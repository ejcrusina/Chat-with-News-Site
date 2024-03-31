import os
import json
import yaml
from dotenv import load_dotenv
from datetime import datetime

from langchain.schema.messages import HumanMessage, AIMessage
from langchain_openai import OpenAI

load_dotenv()

abs_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(abs_path, "../config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def save_chat_history_json(chat_history: list, session_id: str, url: str) -> None:
    """Saves chat history convo and its corresponding website URL in JSON

    Parameters
    ----------
    chat_history : list
        List of convos in session
    session_id : str
    url : str
    """
    chat_session_path = config["chat_session_path"]
    if not os.path.exists(chat_session_path):
        os.makedirs(chat_session_path)
    save_path = f"{chat_session_path}/{session_id}.json"

    with open(save_path, "w") as f:
        # Compile chat history convo
        json_data = [message.dict() for message in chat_history]
        # Add website info at end
        json_data.append({"website_url": url})
        json.dump(json_data, f)


def load_chat_history_json(session_id: str):
    """Loads chat history from past session

    Parameters
    ----------
    session_id : str
    """
    chat_session_path = config["chat_session_path"]
    load_path = f"{chat_session_path}/{session_id}.json"

    with open(load_path, "r") as f:
        json_data = json.load(f)
        # Extract convo
        chat_history = [
            HumanMessage(**message)
            if message["type"] == "human"
            else AIMessage(**message)
            for message in json_data
            if "website_url" not in message
        ]

        # Extract url
        url = json_data[-1]["website_url"]
        return chat_history, url


def delete_chat_history(session_id: str) -> None:
    """Deletes json with chat history of past session

    Parameters
    ----------
    session_id : str
        _description_
    """
    chat_session_path = config["chat_session_path"]
    if not os.path.exists(chat_session_path):
        os.makedirs(chat_session_path)

    file_path = f"{chat_session_path}/{session_id}.json"
    if os.path.exists(file_path):
        os.remove(file_path)


def generate_session_title(user_qry: str, url: str) -> str:
    """Creates a short title to be shown in selectbox of chat session

    Parameters
    ----------
    user_qry : str
        First query of user in a chat session
    url : str
        Website URL
    """
    llm = OpenAI()
    prompt = f"Generate a descriptive, 1 to 3 words short title for a chat session that starts with this user input:\n\n{user_qry}\n\nAnd this website URL:\n\n{url}"
    session_title = llm(prompt)
    return session_title


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

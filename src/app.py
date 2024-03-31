import os
import re
import yaml
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from llm_chains import (
    get_vectordb_from_url,
    get_context_retriever_chain,
    get_rag_chain,
)
from utils import (
    save_chat_history_json,
    load_chat_history_json,
    delete_chat_history,
    generate_session_title,
)
from validators import validate_url_accessibility


abs_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(abs_path, "../config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def get_chatbot_response(user_qry):
    retriver_chain = get_context_retriever_chain(st.session_state["vectordb"])
    conversational_rag_chain = get_rag_chain(retriver_chain)
    response = conversational_rag_chain.invoke(
        {"chat_history": st.session_state.chat_history, "input": user_qry}
    )
    return response["answer"]


def default_chatbot_intro():
    return AIMessage(
        content="Hello! I am a chatbot that knows the content of website URL. How can I help you?"
    )


def display_chat_convo():
    # Conversation
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)

        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)


def populate_chat_history(user_qry):
    if user_qry is not None and user_qry != "":
        with st.spinner("Generating response..."):
            response = get_chatbot_response(user_qry)
            st.session_state.chat_history.append(HumanMessage(content=user_qry))
            st.session_state.chat_history.append(AIMessage(content=response))


def save_chat_history(user_qry):
    # User provides input after the default AI message (1 count in history)
    if len(st.session_state.chat_history) > 1:
        if st.session_state.session_id == "New session":
            session_title = generate_session_title(
                user_qry, st.session_state.latest_web_url
            )
            cleaned_session_title = re.sub(r"[^a-zA-Z0-9 ]", "", session_title)
            st.session_state.new_session_id = cleaned_session_title
            save_chat_history_json(
                st.session_state.chat_history,
                st.session_state.new_session_id,
                st.session_state.latest_web_url,
            )
        else:
            save_chat_history_json(
                st.session_state.chat_history,
                st.session_state.session_id,
                st.session_state.latest_web_url,
            )


# Page config
st.set_page_config(page_title="Chat with Website", page_icon=":robot_face:")
st.title("Chat with Website")


# Initialize session states
if "sent_valid_website" not in st.session_state:
    st.session_state.sent_valid_website = False
    st.session_state.latest_web_url = None
    st.session_state.web_url_tracker = None
    st.session_state.new_web_url_sent = False

if "session_id" not in st.session_state:
    st.session_state.session_id = "New session"
    st.session_state.new_session_id = None
    st.session_state.session_index_tracker = "New session"


# SIDE BAR DISPLAY
with st.sidebar:
    st.header("Settings")

    # Sidebar elements
    web_url = st.text_input("Website URL")
    send_url_button = st.button("Send URL")
    st.session_state.web_url_tracker = web_url

    # Check if the user has entered a value for website_url
    if send_url_button:
        # Check if the web URL in input changed after reclicking send
        if (st.session_state.latest_web_url != st.session_state.web_url_tracker) and (
            st.session_state.latest_web_url is not None
        ):
            st.session_state.new_web_url_sent = True

        # Check if website URL is valid
        URL_REGEX = "^((https?|ftp|smtp):\/\/)?(www.)?[a-z0-9]+\.[a-z]+(\.[a-z]+)?(\/[a-zA-Z0-9#=\_\$\-\?]+\/?)*$"
        if not re.match(URL_REGEX, web_url):
            st.warning("Invalid input. Please enter a valid website URL")
        else:
            # URL is valid
            st.session_state.sent_valid_website = True
            if st.session_state.latest_web_url is None:
                # For 1st session
                st.session_state.latest_web_url = web_url
            elif st.session_state.new_web_url_sent:
                # Set new URL as latest URL
                st.session_state.latest_web_url = web_url

    # Default when no URL input yet
    if not st.session_state.sent_valid_website:
        st.info("Please enter a website URL")


# Run the main page
if st.session_state.sent_valid_website:
    # Default
    delete_button_clicked = False
    is_url_accessible = True

    # PRE-HANDLING: Prepare vectordb
    if ("vectordb" not in st.session_state) or (st.session_state.new_web_url_sent):
        is_url_accessible = validate_url_accessibility(web_url)
        if is_url_accessible:
            with st.spinner("Ingesting website content. Please wait."):
                st.session_state.vectordb = get_vectordb_from_url(web_url)

    # INTERACTIVITY SCENARIO 1: A session is selected
    # Load past convo if selected session is not new AND web url didnt changed
    if (
        (st.session_state.session_id != "New session")
        and (not st.session_state.new_web_url_sent)
        and (not delete_button_clicked)
    ):
        st.session_state.chat_history, st.session_state.latest_web_url = (
            load_chat_history_json(st.session_state.session_id)
        )
        # Reload vector DB with ALL embeddings from past sessions
        with st.spinner("Reingesting website content. Please wait."):
            st.session_state.vectordb = get_vectordb_from_url(web_url, load_db=True)

        # Show delete button
        delete_button_clicked = st.sidebar.button("Delete session")
    else:
        # Fresh convo
        st.session_state.chat_history = [default_chatbot_intro()]

    # INTERACTIVITY SCENARIO 2: Web URL was changed
    # When web url changed, set back to new session with fresh convo
    if st.session_state.new_web_url_sent:
        # Set session back to "New session" when new web url is sent.
        st.session_state.session_id = "New session"
        st.session_state.chat_history = [default_chatbot_intro()]

        # Reset back since the new web url is not new anymore
        st.session_state.new_web_url_sent = False

    # MAIN PAGE DISPLAY

    if delete_button_clicked:
        with st.spinner("Deleting current session. Just a moment..."):
            delete_chat_history(st.session_state.session_id)
            st.session_state.session_index_tracker = "New session"
            st.session_state.chat_history = [default_chatbot_intro()]

            st.session_state.latest_web_url = web_url
            st.write("Provided URL: " + st.session_state.latest_web_url)

            user_qry = st.chat_input("Type your message here...")

            # Show fresh chat convo
            populate_chat_history(user_qry)
            display_chat_convo()
    elif not is_url_accessible:
        st.subheader(
            "\nSorry, I cannot reach the website. Please input another website by resending the URL."
        )
    else:  # Default display
        st.write("Provided URL: " + st.session_state.latest_web_url)

        user_qry = st.chat_input("Type your message here...")

        # Show and save chat convo
        populate_chat_history(user_qry)
        display_chat_convo()
        save_chat_history(user_qry)

        # Index the new session title in select box
        if (
            st.session_state.session_id == "New session"
            and st.session_state.new_session_id is not None
        ):
            st.session_state.session_index_tracker = st.session_state.new_session_id
            # Reset since selected session is not new anymore
            st.session_state.new_session_id = None

    # Get all session IDs from chat session dir
    chat_session_path = config["chat_session_path"]
    if not os.path.exists(chat_session_path):
        os.makedirs(chat_session_path)

    session_files = [
        os.path.splitext(file)[0]
        for file in os.listdir(chat_session_path)
        if file.endswith(".json")
    ]
    chat_session_titles = ["New session"] + session_files

    index = chat_session_titles.index(st.session_state.session_index_tracker)
    st.sidebar.selectbox(
        "Select a chat session", chat_session_titles, key="session_id", index=index
    )

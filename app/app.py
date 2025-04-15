import streamlit as st

from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

from prompts import PERSONA, INITIAL_PROMPT

# Add custom CSS for styling
st.markdown(
    """
    <style>
    /* Style the sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffe6f0; /* Light pink background */
    }

    /* Style the main background */
    [data-testid="stAppViewContainer"] {
        background-color: #f5fff5; /* Very light green background */
    }

    /* Style the input bar */
    div[data-baseweb="input"] > div {
        background-color: #ffe6f0; /* Light pink background */
        border-radius: 5px;
    }

    /* Style the input bar text */
    div[data-baseweb="input"] input {
        color: #333333; /* Dark text for contrast */
    }

    /* Style the top and bottom bars */
    header[data-testid="stHeader"] {
        background-color: #f5fff5; /* Very light green background */
    }
    footer {
        background-color: #f5fff5; /* Very light green background */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.header("Clarity AI")
st.subheader("I'm Clarity, your virtual dermatologist. How can I help you?")

# Sidebar for managing chats
st.sidebar.header("Chats")

# Initialize chats in session state
if "chats" not in st.session_state:
    st.session_state.chats = {"Default Chat": {"messages": [], "title": "Default Chat"}}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Default Chat"

# Function to switch chats
def switch_chat(chat_name):
    st.session_state.current_chat = chat_name

# Function to create a new chat
def create_new_chat():
    new_chat_name = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[new_chat_name] = {"messages": [], "title": "New Chat"}
    switch_chat(new_chat_name)

# Function to delete a chat
def delete_chat(chat_name):
    if chat_name in st.session_state.chats:
        del st.session_state.chats[chat_name]
        # Switch to the default chat if the current chat is deleted
        if st.session_state.current_chat == chat_name:
            st.session_state.current_chat = "Default Chat"

# Sidebar button to create a new chat
if st.sidebar.button("New Chat"):
    create_new_chat()

# Display chat tabs in the sidebar
for chat_name in list(st.session_state.chats.keys()):
    col1, col2 = st.sidebar.columns([4, 1])  # Create two columns for the tab and delete button
    with col1:
        if st.sidebar.button(chat_name, key=f"switch_{chat_name}"):
            switch_chat(chat_name)
    with col2:
        if st.sidebar.button("❌", key=f"delete_{chat_name}", help="Delete this chat"):
            delete_chat(chat_name)

# Display the current chat title in the sidebar
st.sidebar.subheader("Current Chat")
st.sidebar.markdown(f"**{st.session_state.chats[st.session_state.current_chat]['title']}**")

# Sync messages with the current chat
if "messages" not in st.session_state:
    st.session_state.messages = st.session_state.chats[st.session_state.current_chat]["messages"]
st.session_state.messages = st.session_state.chats[st.session_state.current_chat]["messages"]

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# File uploader for attachments
uploaded_file = st.file_uploader("Upload a file, photo, or video for a skin analysis", type=["jpg", "jpeg", "png", "mp4", "pdf"])
if uploaded_file:
    # Display the uploaded file
    st.markdown("### Uploaded File:")
    st.markdown(f"**{uploaded_file.name}**")
    
    # Example: Analyze the uploaded file (placeholder logic)
    if uploaded_file.type.startswith("image/"):
        response = "I see you've uploaded an image. Let me analyze it for skincare advice."
    elif uploaded_file.type.startswith("video/"):
        response = "I see you've uploaded a video. I'll analyze it for relevant skincare insights."
    elif uploaded_file.type == "application/pdf":
        response = "You've uploaded a PDF. I'll extract and analyze the content for skincare advice."
    else:
        response = "Unsupported file type. Please upload an image, video, or PDF."

    # Display the AI's response
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Get user input
if user_skin := st.chat_input("Ask me anything!"):
    with st.chat_message("user"):
        st.markdown(user_skin)
    st.session_state.messages.append({"role": "user", "content": user_skin})

    # Auto-generate a title for the chat if it's the first user input
    if len(st.session_state.messages) == 1:
        st.session_state.chats[st.session_state.current_chat]["title"] = user_skin[:30] + "..." if len(user_skin) > 30 else user_skin

    # Handle greetings or insufficient input
    if user_skin.lower() in ["hi", "hello", "hey"]:
        response = "Hi! Can you tell me about your skin type and whether you'd like a skincare routine or advice?"
    elif len(user_skin.split()) < 3:  # Check if input is too short
        response = "Can you provide more details about your skin type or issues so I can assist you better?"
    else:
        # Create an OpenAI LLM instance
        llm = OpenAI(
            api_key=st.secrets["openai"]["API_KEY"],
            temperature=0,
            max_tokens=1000
        )

        # Create a chat prompt template with initial messages
        prompt = ChatPromptTemplate(
            input_variables=["chat_history", "input"],
            messages=[
                SystemMessagePromptTemplate.from_template(
                    """
                    Your name is Clarity and you are an expert virtual dermatologist who specializes in creating skincare routines for patients.
                    Your goal is to create a skincare routine with recommended products for the given patient's skin type and skin issues.
                    Generate a step-by-step skincare routine with recommended products for the patient based on their skin type and skin issues.
                    Please be specific and detailed in your recommendations.
                    Provide a detailed and structured response that is easy to read. 
                    Use bullet points, numbered lists, or sections where appropriate. 
                    Only give a skincare routine or advice when the user provides details about their skin.
                    Always recommend that the user applies SPF during the daytime.
                    Always refer to yourself as Clarity
                    Only use the information given to you about the user's skin from the user, never make assumptions about the user's skin.
                    Do not predict or simulate what the user might say next.
                    """
                ),
                HumanMessagePromptTemplate.from_template("{input}")
            ]
        )

        # Create an LLMChain with the LLM, prompt, and memory
        chain = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=st.session_state.memory
        )

        # Get a prediction from the chain
        chat_history = "\n".join([msg["content"] for msg in st.session_state.messages])
        response = chain.predict(chat_history=chat_history, input=user_skin)

    # Format the response for better readability
    formatted_response = f"""
    ### Clarity's Response:
    {response}
    """

    with st.chat_message("assistant"):
        st.markdown(formatted_response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update memory context
    st.session_state.memory.save_context({"input": user_skin}, {"output": response})

# Save messages back to the current chat
st.session_state.chats[st.session_state.current_chat]["messages"] = st.session_state.messages

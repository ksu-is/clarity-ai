import streamlit as st

from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

from prompts import PERSONA, INITIAL_PROMPT

st.header("Clarity AI")

if "messages" not in st.session_state:
    st.subheader("I'm Clarity, your virtual dermatologist. How can I help you today?")
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
if user_skin := st.chat_input("Ask me anything!"):
    with st.chat_message("user"):
        st.markdown(user_skin)
    st.session_state.messages.append({"role": "user", "content": user_skin})

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

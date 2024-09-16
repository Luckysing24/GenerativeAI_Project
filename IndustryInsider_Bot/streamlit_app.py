import os
import traceback 
import glob
import logging
from datetime import datetime
from typing import List 
import tiktoken
from langchain_google_genai.chat_models  import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever 
from langchain.retrievers import EnsembleRetriever
from langchain.chains import create_history_aware_retriever,create_retrieval_chain 
from langchain_core.messages import HumanMessage, AIMessage 
from langchain_community.chat_message_histories import ChatMessageHistory 
from langchain.chains.combine_documents import create_stuff_documents_chain 
from langchain_core.chat_history import BaseChatMessageHistory 
from langchain_core.runnables.history import RunnableWithMessageHistory

from dotenv import load_dotenv 
load_dotenv(override=True)

import streamlit as st

from promptstore import prompt_store

#DEFAULT parameters
TOKEN_HISTORY_PADDING=int(os.environ["TOKEN_HISTORY_PADDING"])
TOKEN_PROMPT_PADDING=int(os.environ["TOKEN_PROMPT_PADDING"])
MAX_TOKENS=int(os.environ["MAX_TOKENS"])

#Initializing the embedding to be used
embeddings=HuggingFaceInferenceAPIEmbeddings(
            api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
            model_name=os.environ["EMBEDDING_MODEL"]
        )

#Loading text embeddings from vectorDB
vector_db=Chroma(persist_directory=os.environ["VECTOR_PATH"],embedding_function= embeddings)
#Create a retriever to retrieve data from vectorDB
vector_retriever=vector_db.as_retriever()

#Loading retriever for full text search
keyword_retriever = BM25Retriever.from_texts(vector_db.get()['documents'])
keyword_retriever.k = 5

#Hybrid search: using vector and keyword retriever by reranking the retrieved chunks
retriever=EnsembleRetriever(retrievers=[vector_retriever,keyword_retriever],weight=[0.7,0.3])

#Initialize the LLM
llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"],google_api_key=os.environ["GEMINI_API_KEY"],temperature=0)
#Initializing the tiktoken to count the token length.
tokenembed=tiktoken.get_encoding(os.environ ["TIKTOKEN_MODEL"])
#Initializing promots to be used in order to generate response #Prompt1: To rephrase the original question into standalone question
QUESTION_MAKER_PROMPT=prompt_store.prompt_store.question_maker_prompt()
#Prompt2: To generate response using the context and providing system instructions for multilingúal questions
PROMPT=prompt_store.prompt_store.prompt()


def _log_file_creation():
    '''Function to create log file and logger object'''
    log_dir=os.path.join(os.environ["LOG_DIR"],"Chatbot" )
    if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    list_of_log_files= glob.glob(f"{log_dir}/*.log")
    if list_of_log_files:
        latest_log_file=max([f for f in list_of_log_files if f.startswith('Chatbot')],key=os.path.getctime)
        if os.stat(latest_log_file).st_size >= int(os.environ["LOG_FILE_SIZE"]):
            logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Chatbot_%Y%m%d%S.log')))
        else:
            logfilepath=latest_log_file
    else:
        logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Chatbot_%Y%m%d%S.log')))
    #Configure logging to write to a file in the log directory
    fileh=logging.FileHandler(logfilepath,'a')
    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileh.setFormatter(formatter)
    logger=logging.getLogger()
    logger.setLevel(logging.INFO)
    #remove all old handler
    for hdlr in logger.handlers[:]:
        logger.removeHandler(hdlr)
    #set new handler
    logger.addHandler(fileh)
    return logger

def truncate(history: List,total_: int):
    '''Function to remove the initial conversations from history''' 
    token_limit=int(os.environ["MAX_TOKENS"])-500
    while total_ >= token_limit and history:
        total_=len(tokenembed.encode(history[0].content)) + len(tokenembed.encode(history[1].content) )+2*TOKEN_HISTORY_PADDING
        del history[:2]
    return history

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    '''Fnction to fetch historic conversation based on session ID'''
    if session_id not in st.session_state:
        st.session_state[session_id] = ChatMessageHistory()
    return st.session_state[session_id]


def generate_response(request: str):
    '''Function to generate streaming LLM response''' 
    try:
        currenttotal_token_count=0
        # sum the token length of all the chat_history + padding for conversation narative
        # eg. AI message and Human
        if session_id in st.session_state.keys():
            currenttotal_token_count =sum(len(tokenembed.encode(i.content))+ TOKEN_HISTORY_PADDING for i in st.session_state[session_id].messages) 
        #add question token length to the chat history
        #Now we have token length for entire prompt #(chathistory + question + sys prompt)
        tokenlen_input_question=len(tokenembed.encode(request))
        tokenlen_Question_prompt=len(tokenembed.encode(QUESTION_MAKER_PROMPT.pretty_repr()))
        tokenlen_rag_prompt=len(tokenembed.encode(PROMPT.pretty_repr()))
        Buffer=TOKEN_PROMPT_PADDING
        currenttotal_token_count += tokenlen_input_question+tokenlen_Question_prompt+tokenlen_rag_prompt+Buffer
        #Set the max token length to restrict the response within the range based on prompt tokens.
        llm.max_output_tokens=abs(MAX_TOKENS - (currenttotal_token_count))
        #1. Chain to create standalone question from original question and retriave documents using that question 
        history_aware_retriever=create_history_aware_retriever(llm, retriever, QUESTION_MAKER_PROMPT)
        #2. To generate documents 
        question_answer_chain=create_stuff_documents_chain(llm, PROMPT)
        #Combining 1 & 2 to generate response from LLM using context and chat_history 
        rag_chain=create_retrieval_chain(history_aware_retriever, question_answer_chain)
        conversational_rag_chain=RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
            )

        #variable to store the entire response response=""
        response=""
        #Generating streaming tokens from LLM response
        for token in conversational_rag_chain.stream({"input": request},config={"configurable":{"session_id": session_id}}):
            if answer_chunk := token.get("answer"):
                response+=answer_chunk
                yield answer_chunk
        # #count response token length
        response_token_count=len(tokenembed.encode(response))
        #Need to the total token used
        # (question + response + chat history)
        current_overall_token_count=response_token_count + currenttotal_token_count
        # #pass total token used to check if need to remove the initial conversation
        # in order to avoid context token limit issue
        st.session_state[session_id].messages=truncate(st.session_state[session_id].messages,current_overall_token_count)
        logger.info("Successfully generated the response!")
    except Exception as e:
        stack_trc=traceback.format_exc()
        # • logging.error(f"An error occurred in generating response using RetrievalQA chai
        logger.error(f"An error occurred in generating response using RetrievalA chain: {str(stack_trc)}")

if __name__=="__main__":

        #Creating a log file
        logger=_log_file_creation()
        #Session state (set it to default for time being)
        session_id=10
        if session_id not in st.session_state:
            st.session_state[session_id]=ChatMessageHistory()
        #Display on streamlit app
        st.set_page_config(page_title="Assistant")#🎊👍
        st.title("IndustryInsider Assistant 🤖")
        st.markdown("##### 🎊 Welcome to Manufacturing and SupplyChain Assistant Bot! 🎊")#🎉")
        st.markdown("""#### What is IndustryInsider Assistant?
        The IndustryInsider is an intelligent assistant designed to provide insightfulanswers to your queris about industrial operations landscape.💼""")
        st.markdown(" *Explore the trends specific to Indian Manufacturing and SupplyChain sector* ")
        st .markdown ("""
        ###### What You Can Do:
        -👉 Ask industry-domain specific questions.            
        -👉 Generate summaries for the articles.""")

        with st.container():
            col1,col2=st.columns([7,1])
            # button to start new conversation
            with col2:
                if st.button("Refresh"):
                    st.session_state[session_id].clear()
                    print(st.session_state)

        #Show conversation in streamlit app 
        for message in st.session_state[session_id].messages:
        # print ("message", message)
            if isinstance(message, HumanMessage):
                with st.chat_message ("Human"): 
                    st.markdown(message.content)
            elif isinstance(message,AIMessage):
                with st.chat_message("AI"):
                    st.markdown(message.content)

        #user input
        user_query=st.chat_input("Ask me anything...")
        if user_query is not None and user_query!="": 
            with st.chat_message("Human"):
                st.markdown(user_query)

            with st.chat_message("AI"):
                st.write_stream(generate_response(user_query))
        
        #Autoscrolling with every new conversation
        st.markdown("<script>window.scrollTo(0,document.body.scrollHeight);</script>",unsafe_allow_html=True)
        logger.info("Successfully displayed the response!")
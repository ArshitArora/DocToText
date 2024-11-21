from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from langchain.prompts import HumanMessagePromptTemplate, PromptTemplate, SystemMessagePromptTemplate
import redis
import os
import time
import google.generativeai as genai
import json

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key='api_key')
os.environ['GOOGLE_API_KEY'] = api_key
connection_start = time.time()

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en")
LLM = ChatGoogleGenerativeAI(model='gemini-1.5-flash',
                             temperature=0.4,
                             max_output_tokens=512)
REDISCONNECTION = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
REDISCONNECTION.flushdb()
connection_end = time.time()
print(f"Connection time : {connection_end - connection_start}")



def load_to_vector_store(user,text):
    chunk_size = 2000
    chunk_overlap = 500
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = text_splitter.split_text(text)

    chroma_vector_store = Chroma(
        persist_directory=f"{user}_db",
        collection_name='vector_index',
        embedding_function=EMBEDDING_MODEL,
    )

    chroma_vector_store.add_texts(texts)
    print(f"Documents stored successfully in Database for user: {user}")

def conversational_retriever(retriever):
    system_message_for_contextualization = SystemMessagePromptTemplate(prompt=PromptTemplate(
        template="Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."))
    prompt_for_contextualization = ChatPromptTemplate(
        [
            system_message_for_contextualization,
            MessagesPlaceholder("chat_history"),
            HumanMessagePromptTemplate(prompt=PromptTemplate(template="{input}", input_variables=['input']),
                                       input_variables=['input'])
        ],
        input_variables=['input']
    )
    history_aware_retriever = create_history_aware_retriever(LLM, retriever, prompt_for_contextualization)
    return history_aware_retriever


def conversational_chain(history_aware_retriever):
    system_message_for_qa = SystemMessagePromptTemplate(prompt=PromptTemplate(
        template="You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Respond normally to Greetings."))
    human_message_for_qa = HumanMessagePromptTemplate(
        prompt=PromptTemplate(template="Context: {context} \nQuestion : {input} \nAnswer:",
                              input_variables=['input', 'context']), input_variables=['input', 'context'])
    prompt_for_qa = ChatPromptTemplate(
        [
            system_message_for_qa,
            MessagesPlaceholder('chat_history'),
            human_message_for_qa
        ],
        input_variables=['input', 'chat_history', 'context']
    )
    qa_chain = create_stuff_documents_chain(LLM, prompt_for_qa)
    rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)
    return rag_chain


def chat(user, prompt, retriever):

    if not REDISCONNECTION.exists(f"chat_history:{user}"):
        REDISCONNECTION.set(f"chat_history:{user}", json.dumps([]))
    chat_history_json = REDISCONNECTION.get(f"chat_history:{user}")
    chat_history = json.loads(chat_history_json) if chat_history_json else []
    history_aware_retriever = conversational_retriever(retriever)
    rag_chain = conversational_chain(history_aware_retriever)
    print("invoking chain")
    ai_message = rag_chain.invoke({'input': prompt, 'chat_history': chat_history})
    print("chain invoked succesfully")
    answer = ai_message['answer']

    chat_history.extend([
        ('human', prompt),
        ('ai', answer)
    ])
    REDISCONNECTION.set(f"chat_history:{user}", json.dumps(chat_history))
    print("chat history updated")
    return answer


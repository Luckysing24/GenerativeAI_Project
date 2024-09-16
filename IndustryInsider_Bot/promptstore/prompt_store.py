from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
class prompt_store:
    @staticmethod 
    def prompt():
        system_prompt="""You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know.
        Context: {context}
        """

        messages=[SystemMessagePromptTemplate.from_template(system_prompt),
                  MessagesPlaceholder(variable_name="chat_history"),
                  HumanMessagePromptTemplate.from_template("{input}"),
                ]
        prompt=ChatPromptTemplate.from_messages(messages)
        return prompt
    
    def question_maker_prompt():
        system_prompt="""Given a chat history and the latest user question\ 
            which might reference context in the chat history, formulate a standalone question\
            which can be understood without the chat history. Do NOT answer the question,\
            just reformulate it if needed and otherwise return it as is."""
        messages=[
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
                ]
        prompt=ChatPromptTemplate.from_messages(messages)
        return prompt

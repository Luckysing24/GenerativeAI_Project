## IndustryInsider Assistant: Manufacturing and Supply Chain Chatbot 🤖

#### (Create a hybrid search RAG based LLM application that can answer industry specific question)

### Objective
---------------
The primary goal is to build Minimal Viable Product (MVP) conversational chatbot that assists users with queries related to the manufacturing industry and supply chain management. The chatbot will leverage data from articles from The Economic Times to provide contextually relevant response. By integrated with this industry-specific data, the chatbot will offer insights into recent trends, technologies and key players in the manufacturing sector.

### General Overview
---------------------
    -	Industry: Manufacturing and Supply chain
    -	User Persona: Supply Chain Analyst, Manufacturing Director, Sustainability Consultant
    -	Approach: Hybrid search Retrieval Augmented Generation LLM chatbot.
    -	Knowledge Base Type: Static dataset
    -	Source: https://economictimes.indiatimes.com/industry/indl-goods/svs/engineering

### Technical Overview
-----------------------
    -	Total articles: 47
    -	Used pretrained model: Gemini-1.5-pro-latest
    -	Embedding Model: BGE
    -	Frameworks: Streamlit and langchain
    -	Storage: ChromaDB
  
### Scope of Work
-------------------
The scope of this project is to develop a Manufacturing and supply chain Assistant Chatbot that can assist users with queries related to the mentioned industry. The chatbot will be powered by a pre-trained language model which will make use of Hybrid search Retrieval Augmented Generation (RAG) approach. This chatbot will be built using streamlit, a user-friendly tool that enables rapid development of LLM-based application. The bot should be able to answer the question related to the industry it has knowledge of and also should be able to summarise the articles.
Following are the few features:
1.	Memory: The chatbot will be able to have a continuous conversation even with the follow-up questions due to memory integration.
2.	Streaming response: It delivers answers in real-time, allowing users to see the reply as it’s being generated for a faster, smoother experience.
3.	New conversation: User can anytime start a fresh conversation with the chatbot.


### Sneek-Peek of IndustryInsider Assistant
--------------------------------------------

![image](https://github.com/user-attachments/assets/369c0337-b187-4cec-99e5-56250c2f324e)

### Project Timeline
----------------------
1.	**Research**: Dedicated time to understanding the unique requirements of the manufacturing industry and identifying suitable technologies and tools for chatbot development.
2.	**Prototype Development**: Time Spent on creating basic version of the chatbot along with prompt engineering to test the core functionalities and gather feedback.
3.	**Feature Implementation**: Time spent on adding specific features tailored to the chatbot context, such as memory and streaming integration.
4.	**User Interface Designing**: Time spent on designing and integrating the user interface with the backend.
5.	**Testing and Refinement**: Time on thorough testing along with extensive analysis to identify and address any issues, followed by iterative refinements to improve the chatbot’s performance and accuracy.

### Architecture
-------------------
1.	**Data Gathering**: To acquire a comprehensive dataset of relevant information, articles on manufacturing and supply chain industry from specified website were scraped using Python libraries like Selenium, AsyncHTMLoader and BeautifulSoup. This process involved first extracting urls of all the articles and then identifying the HTML elements within those articles containing the desired content and extracting the text efficiently.

2.	**Data Chunking**: To improve retrieval efficiency and reduce the computational cost of language model processing, information in the extracted articles is then divided into smaller, semantically coherent chunks using Semantic Chunking.

3.	**Embedding Generations**: Embeddings were generated for each chunk using pre trained language model like BGE (BAAI General Embedding). These embeddings capture the semantic meaning of the text and facilitate efficient retrieval.

4.	**Storage**: The embeddings were stored in a vector database which has in-built storage for original chunks as well. ChromaDB is used as the vector store which supports the mentioned requirements. 

5.	**Retrieval and Hybrid Search**: A hybrid search approach was implemented, combining full text search and semantic search to leverage the strengths of both strategies.
    -	*Key-word Based Search*: Users could search for specific keywords or phrases using the document store’s built in search capabilities. For this, we made use of BM25 Retriever that fetched original documents/chunks from ChromaDB.
    -	*Semantic search*: To retrieve more relevant results, semantic search was employed using the vector database, ChromaDB This involved calculating the cosine similarity between the query embedding and the embeddings of the stored documents. 
    -	*Result ranking*: The retrieved results were ranked based on their similarity to the query, combining the scores from both keyword-based and semantic search. For this, Ensemble Retriever was used that uses Reciprocal Rank Fusion (RRF) behind the scenes.
    -	*Retriever component*: A dedicated retriever component was developed to get the best matching sets of documents from the vector store by combining the retrievers from both keyword and Semantic and re ranking the retrieved documents.
6.	**Information Retrieval**: Using the hybrid search we get the top best set of documents aligning with the query asked by user.

7.	**Response Generation**: The language model then generates a response using a pre trained generative language model like gemini-1.5-pro-latest to generate human like text responses based on the retrieved information and understood query. 


<img src="https://github.com/user-attachments/assets/ac48bc3c-de1d-44ed-b742-fdcc991621f3" width="900" height="400">
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    High-Level Workflow

### Challenges
----------------
1.	Chatbot’s knowledge base is limited to the articles scraped within the project’s timeframe.
2.	The project is constrained by a short deadline, so any incomplete functionalities will be documented as areas for future improvement.
3.	Due to context window limitation, can retrieve only few chunks leaving the other chunks with useful and relevant information.
4.	Inefficient is summarizing the large article due to context window.
5.	Extracted data from website of the dynamic articles from a single page only.
6.	Need to improve the models in order to generate more accurate results.
   
### Future improvements
------------------------
1.	Real-Time Knowledge Base: Dynamic collection and processing of information in order to provide real-time updates and information. 
2.	Better Storage: Improve efficiency by using storage engine having out of the box support to hybrid search.
3.	Support Aggregate queries: By extracting the relevant entities from the articles and store it in advanced storage like graphDB to enhance the chatbot Assistant by providing accurate response of the queries requires calculations.
4.	Text-to-Speech feature: Include Text-to-Speech feature for better user experience and ease.
5.	Visualizer: It will give user the insights about the trends in more creative form.
6.	Multilinguistic: Include support to languages other than English.



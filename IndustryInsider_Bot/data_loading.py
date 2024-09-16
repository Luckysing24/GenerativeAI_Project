import os 
import logging
import traceback
import glob
from pathlib import Path
from datetime import datetime

import tiktoken
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv 
load_dotenv(override=True)

class Data_loading():
    '''Class to Perform Data loading based in the given document in Vector DB'''
    def __init__(self):
        '''Constructor for initialization'''
        self.logger=self._log_file_creation()
        token_encodingname=os.environ["TIKTOKEN_MODEL"]
        self.max_tokens=int(os.environ["MAX_CHUNK_TOKENS"])
        self.chunks_list=[]
        self.data_folder=os.environ["Data_dir"]
        self.file_extension=os.environ["FILE_EXTENSION"]
        self.EMBEDDINGS=HuggingFaceInferenceAPIEmbeddings(
            api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
            model_name=os.environ["EMBEDDING_MODEL"]
        )
        self.encoding=tiktoken.get_encoding(token_encodingname)
        self.text_splitter=SemanticChunker(self.EMBEDDINGS, breakpoint_threshold_type="percentile")

    def _log_file_creation(self):
        '''Function to create log file and logger object'''
        log_dir=os.path.join(os.environ["LOG_DIR"],"Vector")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        list_of_log_files= glob.glob(f"Vector/{log_dir}/*.log")
        if list_of_log_files:
            latest_log_file=max([f for f in list_of_log_files if f.startswith('Vector_store_')],key=os.path.getctime)
            if os.stat(latest_log_file).st_size >= int(os.environ["LOG_FILE_SIZE"]):
                logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Vector_store_%Y%m%d%S.log')))
            else:
                logfilepath=latest_log_file
        else:
            logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Vector_store_%Y%m%d%S.log')))
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

    def store_vectordb(self, documents) :
        '''Function: To store the generated embeddings into vector db'''
        self.logger.info("Creating vector store...")
        vectorstore=Chroma.from_documents(documents, self.EMBEDDINGS,persist_directory=os.environ["VECTOR_PATH"]) 
        self.logger.info("Successfully stored the data into VectorDB!")

    def split_chunks(self, chunk):
        """Function: To recursively create sub chunks from parent chunk""" 
        text=chunk.page_content
        token_count=len(self.encoding.encode(text))
        # print (token_count)
        if token_count <= self.max_tokens:
            self.chunks_list.append(chunk)
        else:
            all_subsplits=self.text_splitter.create_documents([text]) 
            
            for subsplit in all_subsplits: 
                self.split_chunks(subsplit)

    def validatetokenlength(self,data):
        '''Funtion: To split the chunk further based on number of chunks if the chunk is falling under above criteria'''
        for i in range(len(data)):
            self.split_chunks(data[i])
        return self.chunks_list
    
    def data_chunking(self):
        '''Function: perfroms the chunking of document using semantic splitter'''
        merged_splits=[]
        for filename in os.listdir(self.data_folder): 
            if filename.endswith(self.file_extension):
                with open(os.path.join(self.data_folder,filename),'r',encoding="utf-8") as file:
                    md_content =file.read()
                all_splits=self.text_splitter.create_documents([md_content])
                merged_splits.extend(all_splits)
        chunks=self.validatetokenlength(merged_splits)
        self.logger.info(f"total Number of chunks: {str(len(chunks))}")
        return chunks

    def main(self):
        '''Function: Does the data loading from creating chunks to embedding then storing in the vector'''
        try:
            chunks=self.data_chunking()
            # self.store_vectordb(chunks)
        except Exception as e:
            stack_trc=traceback.format_exc()
            self.logger.error(f"An error occurred in extracting articles: {str(stack_trc)}")

obj=Data_loading() 
chunks=obj.main()
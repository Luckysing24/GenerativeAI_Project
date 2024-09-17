import os 
import time
import traceback
import logging
import glob
from datetime import datetime
from urllib.parse import urljoin, urlparse 
from requests_html import HTML
from bs4 import BeautifulSoup 
from selenium import webdriver 
from langchain_community.document_loaders import AsyncHtmlLoader
from dotenv import load_dotenv
load_dotenv(override=True)

class WebScrap():
    """Class to extract articles using urls"""
    def __init__(self,output_dirname, extract_class, exclude_classes, url_prefix):
        '''Default Initialiation'''
        #Log file creation
        self.logger=self._log_file_creation()
        #Variable initialization
        self.extract_class=extract_class 
        self.exclude_classes=exclude_classes 
        self.url_prefix=url_prefix
        self.output_dir=output_dirname
        #Directory creation for storing articles
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _log_file_creation(self):
        '''Function to create log file and logger object'''
        log_dir=os.path.join(os.environ["LOG_DIR"],"DataExtraction")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        list_of_log_files= glob.glob(f"{log_dir}/*.log")
        if list_of_log_files:
            latest_log_file=max(list_of_log_files,key=os.path.getctime)
            if os.stat(latest_log_file).st_size >= int(os.environ["LOG_FILE_SIZE"]):
                logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Data_extraction_%Y%m%d%S.log')))
            else:
                logfilepath=latest_log_file

        else:
            logfilepath=os.path.join(log_dir,str(datetime.now().strftime('Data_extraction_%Y%m%d%S.log')))
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

    def html_loader(self,url):
        '''Function to load the raw html content of webpage'''
        loader = AsyncHtmlLoader(url)
        docs = loader.load()
        self.logger.info("Successfully loaded the html content!")
        return docs

    def remove_element(self,html_data):
        '''Function to remove unwanted elements from html data '''
        for class_name in self.exclude_classes:
            ele=html_data.find('div',class_=class_name)
            if ele:
                ele.extract()

    def extract_text(self,html_data): 
        '''Function to extract and save the relevant data from raw html'''
        for raw_html in html_data:
            soup=BeautifulSoup(raw_html.page_content, "html.parser")
            #Extract only relevant Html data
            relevant_html=soup.find('div',class_=self.extract_class)
            #Remove unnecessary elements from the relevant html data 
            self.remove_element(relevant_html)
            #Concatenate the title with it's content 
            title=str(raw_html.metadata['title']).removesuffix(' - The Economic Times') 
            articlecontent="\n\n".join([title,relevant_html.text])
            #Store the article
            self.save_webcontent(title, articlecontent)

    def articlelink_extractor(self,url):
        '''Function to extract all the article links from base url'''
        driver=webdriver.Chrome()
        driver.maximize_window()
        driver.get(url)
        #Sleep cause need time to redirect to the main page and load 
        time.sleep(10)
        screen_height=driver.execute_script("return window.screen.height;")
        scroll_pause_time=2
        last_height=0
        #loop over to scroll the page till the end by the driver 
        while True:
            driver.execute_script(f"window.scrollBy(0,3000)")#(screen_height*1});")
            #pause for specified time before scrolling down 
            time.sleep(scroll_pause_time) 
            scroll_height=driver.execute_script("return document.body.scrollHeight")
            # print(str(scroll_height)+"-"+str(last_height))
            #when reached the end stop scrolling 
            if scroll_height==last_height:
                break
            last_height=scroll_height
        #After loading the page entirely, we can fetch raw data 
        page_source=driver.page_source
        #converting raw data in to HTML 
        html_data=HTML(html=page_source)
        #Extrating only links from html 
        all_links=html_data.links
        #convert all the links into absolute links
        abolsute_links=[urljoin(self.url_prefix,link) for link in all_links]
        #Filter only the valid links
        valid_sublinks=[link for link in abolsute_links if link.startswith((url)) and (urlparse(link).path.split('/')[-2] == "articleshow")] 
        self.logger.info(f"Successfully extracted {str(len(valid_sublinks))} valid links!")
        return valid_sublinks
    
    def save_webcontent(self, filename, text):
        '''Function to save article content'''
        article_filename=filename.replace('/','_').replace('\\','_').replace(':','_').replace(' ','_')
        content_file=os.path.join(self.output_dir,article_filename+'.md')
        #Do not store duplicate articles
        if not os.path.exists(content_file):
            with open(content_file, 'w' ,encoding='utf-8') as f:
                f.write(text)
        self.logger.info(f"Successfully saved the file: {article_filename}")
    
    def webcontentextractor(self, url,depth=0):
        '''Function to extract web content of base and children urls'''
        # Get list of all the article's link 
        article_links=self.articlelink_extractor(url)
        # print('Total -number of article links:', len(article_links))
        article_html=self.html_loader(article_links)
        # print('Total number of article in html format:', len(article_html))
        self.extract_text(article_html)

    def main(self,base_urls):
        '''Main function'''
        try:
            for base_url in base_urls:
                self.webcontentextractor(base_url,depth=0)
        except Exception as e:
            stack_trc=traceback.format_exc()
            self.logger.error(f"An error occurred in extracting articles: {str(stack_trc)}")
    
'''Initializing the inputs'''
#class element to extract article links
extract_class="artText"
#class elements need to be removed
exclude_classes=["growfast_widget custom_ad", "inSideInd"] 
url_prefix="https://economictimes.indiatimes.com/"
#Main url to fetch articles
base_urls=["https://economictimes.indiatimes.com/industry/indl-goods/svs/engineering"] 
#directory to save extracted articles
output_dirname='./data/Articles'
#creating class object 
obj=WebScrap(output_dirname, extract_class,exclude_classes, url_prefix)
#calling class function 
obj.main(base_urls)

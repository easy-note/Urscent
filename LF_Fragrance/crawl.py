from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
import time
import urllib.request
import os
import pandas as pd
from urllib.parse import quote_plus          
from bs4 import BeautifulSoup as bs 
from xvfbwrapper import Xvfb
import time
from multiprocessing.pool import ThreadPool
import threading
import gc
from urllib.request import (urlopen, urlparse, urlunparse, urlretrieve)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
import re
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import pdb
import os
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import json
import asyncio
import multiprocessing
import numpy as np
import psutil
import concurrent.futures
from joblib import Parallel, delayed
import ray


def accord_element(url, xpath_data):
    text = []
    ratio = []
    driver = get_driver()
    p = re.compile('(?<=width: ).*')
    try:
        driver.get(url)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH,xpath_data['accord_grid'])))
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, xpath_data['accord_grid'])))
        
        grid = driver.find_element(by = By.XPATH, value = xpath_data['accord_grid'])
        num = len(grid.find_elements(by = By.CLASS_NAME, value = 'accord-bar'))

        for i in range(1,num+1):
            try:
                xpath_f = xpath_data['accord_bar_f']
                xpath_b = xpath_data['accord_bar_b']
                xpath = xpath_f + str(i) + xpath_b
                
                accord = driver.find_element(by = By.XPATH, value = xpath)
                accord_text = accord.get_attribute("textContent")
                accord_score = accord.get_attribute("style")
                accord_score = p.findall(accord_score)[0].strip(';').strip('%')
                
                text.append(accord_text)
                ratio.append(accord_score)
    
            except NoSuchElementException:
                continue
                
        driver.close()
        print(text)
        return text, ratio
    except TimeoutException:
        driver.close()
        text, ratio = accord_element(url,xpath_data)
        return text, ratio 
    

def kill_process(name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == name:
                proc.kill()
    except Exception:
        return

def get_driver():
    count = 0
    driver = None
    while (driver == None) and (count < 10):
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            except Exception:
                count = count + 1
                continue
    return driver


def information_crawler(data):
    url_data = data[0]
    index = data[1]
    chrome_options = data[2]
    xpath_data = data[3]

    failed_fragrance1 = []
    failed_fragrance2 = []

    for i in (list(url_data.index.values)):
        
        brand = url_data.loc[i,'Brand']
        fr_name = url_data.loc[i,'Fragrance']
        url = url_data.loc[i,'Url']

        try:

            accord_text, accord_ratio = accord_element(url, xpath_data)
            
  

        except Exception:
            accord_text, accord_ratio = None, None


    
    return [fr_name, accord_text, accord_ratio]

def crawl(data, *, loop):
    loop.run_in_executor(executor, information_crawler, data)

if __name__ =="__main__":

    vdisplay = Xvfb(width=1920, height=1080)
    vdisplay.start()
    
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument("--remote-debugging-port=9222")
    mobile_emulation = { "deviceName" : "iPhone X" }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument('--disable-dev-shm-usage') 
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument("--disable-extensions")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
    #user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOG'] = "false"


    with open('/home/dhkim/Fragrance/xpath.json', 'r') as f:
        
        
        xpath_data = json.load(f)
        data = pd.read_csv('/home/dhkim/Fragrance/data/data_final.csv',encoding='latin_1')
        data = data.loc[:5,:]

        url_chunks = np.array_split(data,6)

     

        datas = []
        for index in range(6):
            tmp = [
                pd.DataFrame(url_chunks[index]),
                index,
                chrome_options,
                xpath_data]
            datas.append(tmp)
            del tmp
        #pdb.set_trace()
        #with futures.ThreadPoolExecutor(6) as executor: # default/optimized number of threads
        ##    result = list(executor.map(information_crawler, datas))
         #   for r in result:
         #       if r[-1]: r[-1].quit()
         ##       print(r[1])

        Parallel(n_jobs=6, prefer="threads")(delayed(information_crawler)(data) for data in (datas))

    

        kill_process('chrome')
        kill_process('chromedriver')
        kill_process('Xvfb')
     


      
    
     
        
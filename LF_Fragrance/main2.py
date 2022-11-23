from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
import time
import urllib.request
import os
import pandas as pd
from urllib.parse import quote_plus          
from xvfbwrapper import Xvfb
import time
from urllib.request import (urlopen, urlparse, urlunparse, urlretrieve)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
import re
from selenium.webdriver.chrome.service import Service
import os 
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import pdb
import os
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import json
import random
from selenium_stealth import stealth
import undetected_chromedriver as uc
import copy
from selenium.webdriver.common.proxy import Proxy, ProxyType
import requests
import cfscrape
import cloudscraper
import csv

def img_finder(driver,xpath_data):
    try:
        url = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, xpath_data['img_url'])))
        url = url.get_attribute('src')
        return url  
    except Exception:
        return None



def accord_element(driver, xpath_data):
    text = []
    ratio = []
   
    p = re.compile('(?<=width: ).*')
    try:
        grid = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,xpath_data['accord_grid'])))
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
    
            except Exception:
                continue
      
        return text, ratio
    except Exception:
        return None, None

def season_element(driver, xpath_data):

    ratio = []
    season = ['winter','spring','summer','fall','day','night']
    p = re.compile('(?<=width: ).*')

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,xpath_data['season_grid'])))
        for i in range(1,7):
            try:
                #pdb.set_trace()
                xpath_f = xpath_data['season_score_f']
                xpath_b = xpath_data['season_score_b']
                xpath = xpath_f+ str(i) + xpath_b
                
                season_score = driver.find_element(by = By.XPATH, value = xpath)
                bar = season_score.get_attribute("style")
                bar = p.findall(bar)[0].strip(';').strip(' ')
                bar = list(bar)
                cut = bar.index('%')
                bar = bar[:cut]
                bar = "".join(bar)
            
                ratio.append(bar)

            except NoSuchElementException:
                continue

        return ratio
        
    except Exception as e:
        return None

def note_element(driver, xpath_data):

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,xpath_data['notes_grid'])))
        pdb.set_trace()
        try: ## top
            top_notes = driver.find_element(by = By.XPATH, value = xpath_data['top_notes_num'])
            t_num = len(top_notes.find_elements(by = By.TAG_NAME, value = 'div'))
            top_note = notes_finder(driver, xpath_data, t_num, 'top')
            

        except NoSuchElementException:
            top_note = [None]

        try: ## middle
            middle_notes = driver.find_element(by = By.XPATH, value = xpath_data['middle_notes_num'])
            m_num = len(top_notes.find_elements(by = By.TAG_NAME, value = 'div'))
            mid_note = notes_finder(driver, xpath_data, m_num, 'middle')

        except NoSuchElementException:
            mid_note = [None]

        try: ## base
            base_notes = driver.find_element(by = By.XPATH, value = xpath_data['base_notes_num'])
            b_num = len(top_notes.find_elements(by = By.TAG_NAME, value = 'div'))
            base_note = notes_finder(driver, xpath_data, b_num, 'base')
        except NoSuchElementException:
            base_note = [None]
            
        return top_note, mid_note, base_note

    except TimeoutException:
        return None, None, None

def notes_finder(driver, xpath_data, num, type):
    notes = []

    for i in range(1, num+1): ##top note
        xpath_f = xpath_data[type+'_note_f']
        xpath_b = xpath_data[type+'_note_b']
        xpath = xpath_f+ str(i) + xpath_b
        try:
            note = driver.find_element(by = By.XPATH, value = xpath)
            note = note.get_attribute("textContent")
            notes.append(note)
        except NoSuchElementException:
            continue

    return notes


def property_element(driver, xpath_data, property):
    for i in [7,8,9]:
        try:
            
            xpath_f = xpath_data['property_grid_f']
            xpath_b = xpath_data['property_grid_b']
            grid_xpath = xpath_f + str(i) + xpath_b
        
            grid = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH,grid_xpath))).get_attribute("class")

            if grid == 'grid-x grid-padding-x grid-padding-y':
                count = property_finder(driver,xpath_data, property, grid_xpath)
        
        except Exception:
            return None

def property_finder(driver,xpath_data, property, grid_path):

    for i in range(1,15):
        try:
        
            text_path = grid_path + xpath_data['property_mid'] + str(i) + xpath_data['property_text']
            found_property = driver.find_element(by = By.XPATH, value = text_path).get_attribute("textContent")

            if property == found_property:
                if property == "LONGEVITY": 
                    count = property_score(driver,xpath_data, grid_path, i, 5)
                    return count
                elif property == 'SILLAGE': ## -2 -1 1 2
                    count = property_score(driver,xpath_data, grid_path, i, 4)
                    return count
                elif property == 'GENDER': ##-1 -2 0 2 1 ---- negative female positive male
                    count = property_score(driver,xpath_data, grid_path, i, 5)
                    return count
                else:   ## -2 -1 0 1 2
                    count = property_score(driver,xpath_data, grid_path, i, 5)
                    return count
            else:
                continue
        except Exception:
            continue
   

def property_score(driver,xpath_data, grid_path, property_index, num):
    count = []
    for i in range(1, num+1):
        try:
        
            score_path = grid_path + '/div['+ str(property_index) + xpath_data['score_f'] + str(i) + xpath_data['score_b']
            score = driver.find_element(by = By.XPATH, value = score_path).get_attribute("textContent")
            count.append(score)
        except Exception:
            continue
    return count
    

def perfumer_finder(driver,xpath_data):
    pdb.set_trace()
    try:
        
        grid = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'perfumer-avatar')))
        num = len(grid.find_elements(by = By.CLASS_NAME, value = 'cell'))
        if num == 0:
            return None
        elif num == 1:
            try: perfumer = driver.find_element(by = By.XPATH, value = xpath_data['perfumer_one']).get_attribute("textContent")
            except Exception:
                return None
        else:
            perfumers = []
            for i in range(num):
                try:
                    xpath_f = xpath_data['perfumer_f']
                    xpath_b = xpath_data['perfumer_b']
                    xpath = xpath_f + str(i) + xpath_b
                    perfumer = driver.find_element(by = By.XPATH, value = xpath).get_attribute("textContent")
                    perfumers.append(perfumer)
                except Exception:
                    continue
            return perfumers

    except Exception:
        return None
def screenshot(driver):
    driver.save_screenshot('/home/dhkim/Fragrance/'+str(random.randrange(1,20)) + '.png')

def rating_element(driver, xpath_data):
    
    try:
       
        pdb.set_trace()
        selenium_scroll_option(driver)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#main-content > div.grid-x.grid-margin-x > div.small-12.medium-12.large-9.cell > div > div:nth-child(2) > div:nth-child(5) > div.small-12.medium-6.text-center > div')))
        
        try:
            rating_score = driver.find_element(by = By.XPATH, value = xpath_data['rating_score'])
            rating_num = driver.find_element(by = By.XPATH, value = xpath_data['rating_num'])
            rating_score = rating_score.get_attribute("textContent")
            rating_num = rating_num.get_attribute("textContent")

            return rating_score, rating_num

        except Exception:
            return None, None

        
    except Exception:
        return None, None










def selenium_scroll_option(driver):
    SCROLL_PAUSE_SEC = 3
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_SEC)
        new_height = driver.execute_script("return document.body.scrollHeight")
  
        if new_height == last_height:
            return
        last_height = new_height



def get_driver(chrome_options, url, cookies):
    driver = None
    count = 0
    while (driver == None) and (count < 10):
            try:
                
                
                prox = Proxy()
                prox.proxy_type = ProxyType.MANUAL
                prox.ssl_proxy = "ip_addr:port"
                prox.https_proxy = "ip_addr:port"
                prox.socks_version = 5
            
                capabilities = webdriver.DesiredCapabilities.CHROME
                prox.add_to_capabilities(capabilities)
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, capabilities = capabilities)
                
                #driver = uc.Chrome(use_subprocess=True, options=chrome_options) 
                
                driver.find_element(By.XPATH, '//*[@id="notice"]/div[3]/button')
            except Exception:
                count = count + 1
                if driver: driver.quit()
                continue
    pdb.set_trace()

    connect = False
    while connect == False:
        try:
            driver.get(url)
            driver.implicitly_wait(10)
            driver.delete_all_cookies()
            for cookie in cookies: 
                driver.add_cookie(cookie)
            connect = True
        except Exception:
            driver.quit()
            del driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            continue
    
    return driver
def kill_process(name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == name:
                proc.kill()
    except Exception:
        return

def information_crawler(DB, xpath_data,chrome_options,cookies):

    
    for i in tqdm(list(DB.index.values)):
        
        brand = DB.loc[i,'Brand']
        fr_name = DB.loc[i,'Fragrance']
        url = DB.loc[i,'Url']
        count = 0
        data = []
        
        driver = get_driver(chrome_options, url, cookies)
        
        try:
            screenshot(driver)
            pdb.set_trace()

            img_url = img_finder(driver,xpath_data) 
            data.append(img_url) #0
            pdb.set_trace()

            accord_text, accord_ratio = accord_element(driver, xpath_data)  
         
            data.append(accord_text) #1
            data.append(accord_ratio) #2
            pdb.set_trace()

            season_count = season_element(driver, xpath_data)   #4  ##['winter','spring','summer','fall','day','night'] 
            data.append(season_count) #3
        

            pdb.set_trace()
            top_note, mid_note, base_note = note_element(driver, xpath_data)
            data.append(top_note) #4
            data.append(mid_note) #5
            data.append(base_note) #6

            longevity = property_element(driver, xpath_data, "LONGEVITY")       #7
            sillage = property_element(driver, xpath_data, "SILLAGE")           #8
            gender = property_element(driver, xpath_data, "GENDER")             #9
            price_value = property_element(driver, xpath_data, "PRICE VALUE")   #10
            data.append(longevity)
            data.append(sillage)
            data.append(gender)
            data.append(price_value)

            
            pdb.set_trace()

            #rating, rating_count = rating_element(driver, xpath_data)   

        except Exception:
            1

        
        write_data.iloc[i,2] = img_url
        
        if i%200 == 0:
            write_data.to_csv('/home/dhkim/Fragrance/data/DB_img_url1.csv')
            failed = pd.DataFrame(failed_fragrance)
            failed.to_csv('/home/dhkim/Fragrance/failed_img_url1.csv')

        if driver:    
            driver.quit()

        kill_process('chrome')
        kill_process('chromedriver')
        kill_process('chromium-browse')
        kill_process('Xvfb')



    return write_data, failed_fragrance_list

if __name__ =="__main__":

    vdisplay = Xvfb(width=1920, height=1080)
    vdisplay.start()
    
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--incognito')
    #chrome_options.add_argument("--remote-debugging-port=9222")

    #mobile_emulation = { "deviceName" : "iPhone X" }
    #chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument("--single-process")

    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument('--disable-dev-shm-usage') 
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument("--disable-extensions")
    #user_agent = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    chrome_options.add_argument('--no-first-run --no-service-autorun --password-store=basic')

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOG'] = "false"

    with open('/home/dhkim/Fragrance/cookies.csv', 'r', encoding='utf-8-sig') as f:
        cookies = csv.DictReader(f)
        cookies = list(cookies)

    with open('/home/dhkim/Fragrance/xpath.json', 'r') as f:

        
        xpath_data = json.load(f)
        DB = pd.read_csv('/home/dhkim/Fragrance/data/DB.csv',encoding='latin_1')
   
        write_data = information_crawler(DB, xpath_data, chrome_options, cookies)

        
        


        
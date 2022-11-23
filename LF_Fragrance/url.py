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
import traceback         
from selenium.webdriver.common.proxy import Proxy, ProxyType
import csv
import json
import random
def selenium_scroll_down(driver):
    SCROLL_PAUSE_SEC = 3
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_SEC)
        new_height = driver.execute_script("return document.body.scrollHeight")
  
        if new_height == last_height:
            return 1
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
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, desired_capabilities = capabilities)
                
                #driver = uc.Chrome(use_subprocess=True, options=chrome_options) 
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
            driver.refresh()
            connect = True
        except Exception:
            driver.quit()
            del driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            continue
    return driver
def screenshot(driver):
    driver.save_screenshot('/home/dhkim/Fragrance/'+str(random.randrange(1,20)) + '.png')
def reset_driver(driver, chrome_options, url, cookies):
    driver.quit()
    kill_process('chrome')
    kill_process('chromedriver') 
    driver = get_driver(chrome_options, url, cookies)
    return driver

def kill_process(name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == name:
                proc.kill()
    except Exception:
        return

def Fragrance_crawler(url_data,chrome_options,xpath_data, cookies):
    
    base_url = 'https://www.parfumo.net/Release_Years'
    driver = get_driver(chrome_options, 'https://www.parfumo.net/Release_Years/1901', cookies)
    pdb.set_trace()
    years = list(range(1900, 2030))
    years.append(1370)
    failed_year = []

    for year in years:
        year_num = find_years_num(driver, year, xpath_data)
        if year_num == None: failed_year.append(year)
        else:
            year_grid = xpath['year_grid_f'] + str(year) + xpath['year_grid_b']
            for i in range(1, year_num + 1):
                year_f = xpath['to_specific_year_f']
                year_b = xpath['to_specific_year_b']
                xpath = year_f + str(i) + year_b
                specific_year =  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                specific_year_url = specific_year.get_attribute('href')
                url_crawler(driver, specific_year_url, xpath_data, year, write_file)

def kill_process(name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == name:
                proc.kill()
    except Exception:
        return
                
def find_years_num(driver, year, xpath_data):
    year_grid_f = xpath_data['year_grid_f']
    year_grid_b = xpath_data['year_grid_b']
    xpath = year_grid_f + str(year) + year_grid_b
    try:
        years =  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        y_num = len(years.find_elements(by = By.TAG_NAME, value = 'li'))
        return y_num
    except Exception:
        return None


def url_crawler(driver, url, xpath_data, year, write_file):
    try:
        driver.get(url)
        
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
        driver.get(url)
    page_exist = True
    while page_exist:
        fragrance_grid = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'pgrid')))
        fragrances = fragrance_grid.find_elements(by = By.CLASS_NAME, value = 'name')


        
    
        

if __name__ == '__main__':

    vdisplay = Xvfb(width=1920, height=1080)
    vdisplay.start()
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    #chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-dev-shm-usage')

    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--incognito')
    #mobile_emulation = { "deviceName" : "iPhone X" }
    #chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("disable-infobars")

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOG'] = "false"
  
    with open('/home/dhkim/Fragrance/cookies.csv', 'r', encoding='utf-8-sig') as f:
        cookies = csv.DictReader(f)
        cookies = list(cookies)
    url_data= None
    with open('/home/dhkim/Fragrance/xpath.json', 'r') as f:

        
        xpath_data = json.load(f)
        data, failed_fragrance_list= Fragrance_crawler(url_data,chrome_options,xpath_data, cookies)
        failed_country_list = pd.DataFrame(failed_country_list)
        failed_country_list.to_csv('/home/dhkim/Fragrance/failed_country.csv')
        failed_fragrance_list = pd.DataFrame(failed_fragrance_list)
        failed_fragrance_list.to_csv('/home/dhkim/Fragrance/failed_fragrance.csv')
        data.to_csv('/home/dhkim/Fragrance/data/data.csv')


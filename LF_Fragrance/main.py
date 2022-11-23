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
from fake_headers import Headers
import requests
import ray
import json
import random
import psutil
import pickle

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

            except Exception:
                count = count + 1
                clean_up()
                if driver: driver.quit()
                continue

    connect = False
    while connect == False: 
        try:
            driver.get(url)

            driver.implicitly_wait(10)
            driver.delete_all_cookies()
            for cookie in cookies: 
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    continue
                
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

    if driver: driver.quit()
    clean_up()
    driver = get_driver(chrome_options, url, cookies)
    return driver

def kill_process(name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == name:
                proc.kill()
    except Exception:
        return

def clean_up():
    kill_process('chrome')
    kill_process('chromedriver') 

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

def Fragrance_crawler(url_data,chrome_options,xpath_data, cookies, write_file, failed):
    
    base_url = 'https://www.parfumo.net/Release_Years'
    years = list(range(2020 ,1890, -10))
    years.append(1370)

    failed_year = []
    failed_grid = []
    driver = get_driver(chrome_options, base_url, cookies)
    
    for year in years:
    
        try:
            driver.get(base_url)
        except:
            driver = reset_driver(driver, chrome_options, base_url, cookies)

        year_num = find_years_num(driver, year, xpath_data)
        if year_num == None: failed_year.append(year)
        else:
            try:
                year_grid = xpath_data['year_grid_f'] + str(year) + xpath_data['year_grid_b']
                grid = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, year_grid)))
                urls = grid.find_elements(By.TAG_NAME, 'a')
                specific_year_urls = []

                for url in urls:
                    specific_year_urls.append(url.get_attribute('href'))
    
                for i,specific_year_url in (enumerate(specific_year_urls)):
                    try:
                        specific_year = year + i
                        
                        write_file, failed = url_crawler(driver, specific_year_url, xpath_data, specific_year, write_file, failed)
               
                    except Exception:
                        failed_year.append(year + i - 1)
            except Exception as e:
                failed_grid.append(year)
        
        time.sleep(random.randrange(20, 40))
    driver.quit()
    failed_year_DB = pd.DataFrame(failed_year)
    failed_year_DB.to_csv('/home/dhkim/Fragrance/failed/f_year.csv')
    failed_grid_DB = pd.DataFrame(failed_grid)
    failed_grid_DB.to_csv('/home/dhkim/Fragrance/failed/f_grid.csv')


def Fragrance_crawler2(url_data,chrome_options,xpath_data, cookies, write_file, failed):
    
    base_url = 'https://www.parfumo.net/Release_Years'
 
    years = [2015]
    failed_year = []
    failed_grid = []
    driver = get_driver(chrome_options, base_url, cookies)

    for year in years:
        try:
            specific_year_url = base_url + '/' + str(year)
            specific_year = year
            write_file, failed = url_crawler(driver, specific_year_url, xpath_data, specific_year, write_file, failed)
    
        except Exception:
            failed_year.append(year + i - 1)
     
        
        time.sleep(random.randrange(20, 40))
    driver.quit()
    failed_year_DB = pd.DataFrame(failed_year)
    failed_year_DB.to_csv('/home/dhkim/Fragrance/failed/f_year.csv')
    failed_grid_DB = pd.DataFrame(failed_grid)
    failed_grid_DB.to_csv('/home/dhkim/Fragrance/failed/f_grid.csv')

def find_pages(driver):
    try:
  
        numbers = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'numbers')))
        numbers = numbers.find_elements(By.TAG_NAME, 'div')

        num = numbers[-1].text
        return int(num)
    except Exception:
        return 1

def url_crawler(driver, url, xpath_data, specific_year, write_file, failed_pages):
    try:
        driver.get(url)
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
        driver.get(url)

    failed_data = []
    urls = []
    brands = []
    names = []
    datas = []

    num = find_pages(driver)

    for current_page in tqdm(range(1, num + 1)):
        try:
            goto = url +'?current_page=' + str(current_page)
            driver.get(goto)
            time.sleep(random.randrange(3))
            
            try:
                fragrance_grid = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'pgrid')))
                fragrances = fragrance_grid.find_elements(by = By.CLASS_NAME, value = 'col.col-normal')
                fragrance = fragrances[0]
                for fragrance in fragrances:
     
                    fragrance_data = fragrance.find_elements(By.TAG_NAME ,'a')
                    fr_url = fragrance_data[1].get_attribute('href')
                    name = fragrance_data[1].get_attribute('text')
                    brand = fragrance_data[2].get_attribute('text')

                    data = {'brand':brand, "name":name, 'year':specific_year,'url':fr_url}
                    datas.append(data)
            except Exception:
                continue

        except Exception:
            failed = {'url':goto}
            failed_data.append(failed)
        current_page += 1
        
    print('')
    print(str(specific_year) + ':' +str(len(datas)))

    write_file = write_data(write_file, datas)
    write_file.to_csv('/home/dhkim/Fragrance/data/fragrance_data.csv', encoding ='utf-8-sig',  index=False)
    
    failed_pages = write_data(failed_pages,failed_data)
    failed_pages.to_csv('/home/dhkim/Fragrance/failed/failed_pages_url.csv',  index=False)
    return write_file, failed_pages

def write_data(write_file, datas):
    
    for data in datas:
        
        write_file = write_file.append(data, ignore_index = True)
    
    return write_file

    
        

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
    chrome_options.add_argument("--start-maximized")

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOG'] = "false"
  
    with open('/home/dhkim/Fragrance/cookies.csv', 'r', encoding='utf-8-sig') as f:
        cookies = csv.DictReader(f)
        cookies = list(cookies)
    url_data= None
    with open('/home/dhkim/Fragrance/xpath2.json', 'r') as f:

        xpath_data = json.load(f)
        DB = pd.read_csv('/home/dhkim/Fragrance/data/fragrance_data.csv', encoding ='utf-8-sig')
        DB.astype('object')
   
        failed_pages =  pd.read_csv('/home/dhkim/Fragrance/failed/failed_url.csv')
        

        Fragrance_crawler2(url_data,chrome_options,xpath_data, cookies,DB ,failed_pages)

  


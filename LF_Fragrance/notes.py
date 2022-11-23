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

def listToString(str_list):
    result = ""
    for s in str_list:
        result += s + " "
    return result.strip()

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


def notes_crawler(url_data,chrome_options,xpath_data, cookies, write_file, write_file2):
    
    base_url = 'https://www.parfumo.net/Fragrance_Notes'
    driver = get_driver(chrome_options, base_url, cookies)
    try:
        main = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[1]')))
        parent_notes = main.find_elements(By.CLASS_NAME, 'bold.pt-2')

        url_list = []
        failed1 = []
        failed2 = []

        for i in range(len(parent_notes)):
            parent_note = parent_notes[i].find_element(By.TAG_NAME, 'a')
            name = parent_note.get_attribute('text')
            url = parent_note.get_attribute('href')
            url_list.append({'name':name, 'url':url})
        
        #for url in url_list:
        #    parent_note = url['name']
        #    note_url = url['url']
        #    write_file, failed_url = child_notecrawl(driver, note_url, parent_note, write_file)
        #    failed1.append(failed_url)


        grey_box = main.find_elements(By.CLASS_NAME, 'notes_list_holder')
        note_links = []
        for i in range(len(grey_box)):
            if i != 1:
                parent_note = parent_notes[i].find_element(By.TAG_NAME, 'a')
                parent_note = parent_note.get_attribute('text')

                mid_notes = grey_box[i].find_elements(By.TAG_NAME, 'a')
                for mid_note in mid_notes:
                    url = mid_note.get_attribute('href')
                    mid_note = mid_note.get_attribute('text')
                    note_links.append({'parent_note':parent_note,'mid_note':mid_note,'url':url})
            else:
                continue

        for link in note_links:        
            parent_note = link['parent_note']
            mid_note = link['mid_note']
            url = link['url']
     
            write_file2, failed_url2 = mid_notecrawl(driver, url, parent_note, mid_note, write_file2)
            failed2.append(failed_url2)
            driver.get(base_url)
    except Exception:
        1
 
    driver.quit()
    clean_up()

def child_notecrawl(driver, note_url, parent_note, write_file):

    try:
        driver.get(note_url)
    except Exception:
        driver = reset_driver(driver, chrome_options, note_url, cookies)
    notes_list = []
    try:
        note_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'grey-box.mb-2')))
        click_more(note_box)

        notes_holder = note_box.find_element(By.ID, 'notes_list_holder')
        notes = notes_holder.find_elements(By.TAG_NAME, 'a')
        for note in tqdm(notes):
            note = note.get_attribute('text').split()
            notes_list.append({'parent note':parent_note, 'child note':listToString(note[:-1]), 'count':note[-1]})
    
        write_file = write_data(write_file, notes_list)
        write_file.to_csv('/home/dhkim/Fragrance/data/notes_data.csv', encoding ='utf-8-sig')
    except:
        return write_file, note_url

    return write_file, None

def mid_notecrawl(driver, note_url, parent_note, mid_note, write_file):
    time.sleep(random.randrange(1,3))
    try:
        driver.get(note_url)
    except Exception:
        driver = reset_driver(driver, chrome_options, note_url, cookies)
    notes_list = []
    try:
        note_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'grey-box.mb-2')))
        click_more(note_box)
        notes_holder = note_box.find_element(By.ID, 'notes_list_holder')
        notes = notes_holder.find_elements(By.TAG_NAME, 'a')
        for note in tqdm(notes):
            note = note.get_attribute('text').split()
            notes_list.append({'parent note':parent_note, 'mid note': mid_note, 'child note':listToString(note[:-1]), 'count':note[-1]})
        write_file = write_data(write_file, notes_list)
        write_file.to_csv('/home/dhkim/Fragrance/data/parent_mid_child_data.csv', encoding ='utf-8-sig')
    except:
        return write_file, note_url

    return write_file, None


def click_more(note_box):
    try:
        button = note_box.find_element(By.XPATH, '//*[@id="rm-more_0"]/span')
        button.click()
    except Exception:
        return

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
        DB = pd.DataFrame(columns = ['parent note','child note','count'])

        DB2 = pd.DataFrame(columns = ['parent note','mid note','child note','count'])
  
        #DB = pd.read_csv('/home/dhkim/Fragrance/data/fragrance_data.csv', encoding ='utf-8-sig')
        DB.astype('object')
        DB2.astype('object')

        
        
        notes_crawler(url_data,chrome_options,xpath_data, cookies,DB ,DB2)

  


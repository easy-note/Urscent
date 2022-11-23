from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
import time
import urllib.request
import os
import numpy as np
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

         
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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
            del driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            continue
    return driver

def screenshot(driver):
    driver.save_screenshot('/home/dhkim/Fragrance/'+str(random.randrange(1,20)) + '.png')


def reset_driver(driver, chrome_options, url, cookies):

    try :
        driver.quit()
        driver = get_driver(chrome_options, url, cookies)
        click(driver)
    except Exception:
        driver = get_driver(chrome_options, url, cookies)
        click(driver)
    #clean_up()
    return driver

def find_chart(driver):
    try:
        cla = driver.find_element(By.ID, "pd_cla")
        actions = ActionChains(driver)
        actions.move_to_element(cla).perform()
        holder = WebDriverWait(cla, 3).until(EC.presence_of_element_located((By.ID, "classification_community")))
        return holder
    except Exception:
        return False
    
def click(driver):
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        content = driver.find_element(By.ID, "sp_message_iframe_626574")
        driver.switch_to.frame(content)
        driver.find_element(By.XPATH, '//*[@id="notice"]/div[3]/button').click()
        driver.switch_to.default_content()
        time.sleep(3)
        return True
    except Exception:
        return True

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


def info_crawler(url_data,chrome_options, cookies, write_file):
    url = 'https://www.parfumo.net/Perfumes/Lattafa/Opulent_Oud'
    driver = get_driver(chrome_options, url, cookies)
    click(driver)
 
    datas = []

    with open('/home/dhkim/Fragrance/data/notes_icon.pkl','rb') as f1:
        notes_icon = pickle.load(f1)
        notes_icon = set(notes_icon)
    with open('/home/dhkim/Fragrance/data/failed_url.pkl','rb') as f2:
        failed = pickle.load(f2)


    for i in tqdm(range(71100, len(url_data))):
        data = {}
        url = url_data.loc[i, 'url']

        if driver != None:
            try:
                driver.get(url)
            except Exception:
                driver = reset_driver(driver, chrome_options, url, cookies)
        else: 
            driver = get_driver(chrome_options, url, cookies)
            click(driver)
        

        try:
            data['brand'] = url_data.loc[i, 'brand']
            data['name'] = url_data.loc[i, 'name']
            data['year'] = url_data.loc[i, 'year']
            
            
            data['gender'] = get_gender(driver)
            data['img_url'] = get_img(driver)
            data['perfumer'] = get_perfumer(driver)
            top, heart, base, notes_icon = get_notes(driver, notes_icon)
            if top != None:
                data['top_notes'] = top['top_notes']
            if heart != None:
                data['heart_notes'] = heart['heart_notes']
            if base != None:
                data['base_notes'] = base['base_notes']

            data['text'] = get_text(driver)
            rating_datas, data['rating'], data['rating_count'] = get_ratings(driver)

            if rating_datas != None:
                for rating in rating_datas:
                    data[rating['criteria']] = rating['score']
                    data[rating['criteria'] + '_count'] = rating['count']


            if click_chart(driver) == True:

                pie_charts = get_pie_charts(driver)   
                for j, pie_chart in enumerate(pie_charts):
                    chart_dic = get_percentage(driver, j, True)

                    if pie_chart == 'Type':
                        data[pie_chart+'_count'] = chart_dic['Votes']
                        del chart_dic['Votes']
                        data[pie_chart] = chart_dic
                    else:
                        for keys in list(chart_dic.keys()):
                            if keys == 'Votes': data[pie_chart+'_count'] = chart_dic[keys]
                            else: data[keys] = chart_dic[keys]
            else:
                holder = find_chart(driver)
                if holder != False:
                    pie_charts = get_pie_charts(holder)   
                    for j, pie_chart in enumerate(pie_charts):
                        chart_dic = get_percentage(holder, j, False)

                        if pie_chart == 'Type':
                            data[pie_chart+'_count'] = chart_dic['Votes']
                            del chart_dic['Votes']
                            data[pie_chart] = chart_dic
                        else:
                            for keys in list(chart_dic.keys()):
                                if keys == 'Votes': data[pie_chart+'_count'] = chart_dic[keys]
                                else: data[keys] = chart_dic[keys]
        except Exception as e:
            print(e)
            failed.append(url)
                
        datas.append(data)
    

        if len(datas) % 100 == 0:
            with open('/home/dhkim/Fragrance/data/notes_icon.pkl','wb') as f:
                pickle.dump(notes_icon,f)
            with open('/home/dhkim/Fragrance/data/failed_url.pkl','wb') as f2:
                pickle.dump(failed,f2)
            write_file = write_data(write_file, datas)
            write_file.to_csv('/home/dhkim/Fragrance/data/DB.csv' ,encoding ='utf-8-sig',  index=False)
            datas.clear()

    write_file = write_data(write_file, datas)
    write_file.to_csv('/home/dhkim/Fragrance/data/DB.csv' ,encoding ='utf-8-sig',  index=False)

    icon = pd.DataFrame(list(note_icons), columns =['notes','icon_url'])
    icon.to_csv('/home/dhkim/Fragrance/data/icon.csv' ,encoding ='utf-8-sig',  index=False)

def get_img(driver):
    try:
        image_holder= WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'p_image_holder')))
        image_url = image_holder.find_element(By.CLASS_NAME, 'p-main-img')
        image_url = image_url.get_attribute('src')
        return image_url
    except Exception:
        try:
            image_holder= driver.find_element(By.ID, 'p_image_imagery_holder')
            image_url = image_holder.find_element(By.CLASS_NAME, 'p-main-img')
            image_url = image_url.get_attribute('src')
            return image_url
        except Exception: 
            return None


def get_gender(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'fa.fa-venus')
        return 'Female'
    except Exception:
        1
    try:
        driver.find_element(By.CLASS_NAME, 'fa.fa-mars')
        return 'Male'
    except Exception:
        1
    try:
        driver.find_element(By.CLASS_NAME, 'fa.fa-venus-mars')
        return 'Unisex'
    except Exception:
        1

    return None
def get_perfumer(driver):
    perfumer = []
    try:
        perfumers = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'perfumers')))
        perfumers = perfumers.find_elements(By.TAG_NAME, 'a')
        for p in perfumers:
            perfumer.append(p.get_attribute('text'))
        return perfumer
    except Exception:
        return None

def get_notes(driver, note_icons):
    top_notes, heart_notes, base_notes = None, None, None
    try:
        notes = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'notes3')))
        notes_types = notes.find_elements(By.CLASS_NAME, 'notetype')
        note_blocks = notes.find_elements(By.CLASS_NAME, 'notes_block')

        if len(notes_types) == 3:
            for i in range(len(notes_types)):
                if i == 0: top_notes, note_icons = notes_finder('top_notes', note_blocks[i], note_icons)
                elif i == 1: heart_notes, note_icons = notes_finder('heart_notes', note_blocks[i], note_icons)
                elif i == 2: base_notes, note_icons = notes_finder('base_notes', note_blocks[i], note_icons)

        elif len(notes_types) == 0:
            base_notes, note_icons = notes_finder('base_notes', note_blocks[0], note_icons)

        elif len(notes_types) == 2:
            
            for i, note in enumerate(notes_types):
                if note.text == 'Top Notes' : top_notes, note_icons = notes_finder('top_notes', note_blocks[i], note_icons)
                elif note.text == 'Heart Notes' : heart_notes, note_icons = notes_finder('heart_notes', note_blocks[i], note_icons)
                elif note.text == 'Base Notes' : base_notes, note_icons = notes_finder('base_notes', note_blocks[i], note_icons)

        return top_notes, heart_notes, base_notes, note_icons

    except Exception:
        return None, None, None, note_icons


def notes_finder(type, note_block, note_icons):

    note_list = note_block.find_elements(By.CLASS_NAME, 'nowrap.pointer')
    notes = []

    for note in note_list:
        icon = note.find_element(By.TAG_NAME, 'img').get_attribute('src')
        name = note.text
        note_icons.add((name, icon))
        notes.append(name)

    return {type:notes}, note_icons

def get_text(driver):
    try:
        text = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'perfum_details_desc.pt-1.pb-1')))
        text = text.text
        return text
    except Exception:
        return None

def click_chart(driver):
    try:
        chart = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'classi_li')))
        chart.click()
        return True
    except Exception:
        return False


def get_pie_charts(driver):
    try:
        pie_charts_titles = driver.find_elements(By.CLASS_NAME,'black.bold')
        pie_charts=[]

        for chart in pie_charts_titles: 
            pie_charts.append(chart.text)
        return pie_charts
    except Exception:
        return None

def get_percentage(driver, num, click):
    
    data_dic = {}
    if click:
        container = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME,'chart-container')))
        data_elements = container.find_elements(By.CLASS_NAME,'col.mb-2')
    else:
        data_elements = driver.find_elements(By.CLASS_NAME,'col.mb-2')
    
    data = data_elements[num].text
    data = str(data)
    data = data.replace("\n", " ").replace('Votes', "").replace('(', "").replace(')', "").replace('%', "").replace('Vote', "")
    data = data.split()
    data = data[1:]

    i = 0
    while i < len(data):
        if i == 0:
            data_dic['Votes'] = data[i]
            i += 1
        else:
            if data[i] == "Night": 
                data_dic["Night Out"] = int(data[i+2])
                i += 3
            else: 
                data_dic[data[i]] = int(data[i+1])
                i += 2
    
    return data_dic



def get_ratings(driver):
    rating_datas = []
    score_sum = 0
    total = 0

    try:
        rating_info = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'perfum_ratings_holder')))
        ratings = rating_info.find_elements(By.CLASS_NAME, 'barfiller_element.rating-details.pointer')
        num = 0
        for rating in ratings:
            rating_data = rating.text
            rating_data = rating_data.split("\n")
            criteria = rating_data[0]
        
            if '.' in rating_data[1][:3]:
                score = float(rating_data[1][:3])
                count = int(rating_data[1][3:].replace(' Ratings',""))
            else:
                score = float(rating_data[1][:2])
                count = int(rating_data[1][2:].replace(' Ratings',""))

            if criteria != 'Bottle':
                rating_datas.append({'criteria':criteria, 'score':score, 'count':count})
                score_sum += score * count
                total += count
                num += 1
        return rating_datas, round(score_sum / total, 1), round(total / num)
    except Exception:
        return None, None, None

def find_rating(rating, rating_type):

    if rating_type == "Scent": color = 'blue'
    elif rating_type == "Longevity": color = 'pink'
    elif rating_type == "Sillage": color = 'purple'
    elif rating_type == "Value for money": color = 'grey'

    rating_info = rating.find_element(By.CLASS_NAME,'width-100.nowrap')
    score = rating_info.find_element(By.CLASS_NAME, 'pr-1.bold.larger.'+color).text
    count = rating_info.find_element(By.CLASS_NAME, 'lightgrey.small')
    return score, count

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




    #float_16 = ['rating','Scent','Longevity','Sillage','Value for money']
    #for column in float_16:
    #    DB[column] = DB[column].astype(np.float16)
        
    #int_16 = ['year','rating_count', 'Scent_count','Longevity_count','Sillage_count',
    #'Value for money_count','Type_count','Season_count', 'Spring','Summer','Fall','Winter',
    #'Audience_count','Old','Young','Men','Women',
    #'Occasion_count','Leisure','Daily','Night Out','Business','Sport','Evening']
    #for column in int_16:
    #    DB[column] = DB[column].astype(np.int8)

    #string = ['brand','name','perfumer','gender', 'img_url','text']
    #for column in string :
    #    DB[column] = DB[column].astype('string')

    



    
    
    DB = pd.read_csv('/home/dhkim/Fragrance/data/DB.csv',encoding='utf-8-sig')
    url_data = pd.read_csv('/home/dhkim/Fragrance/data/fragrance_data2.csv', encoding ='utf-8-sig')
    

    info_crawler(url_data,chrome_options, cookies,DB)

  


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
import warnings
import re
import pickle


def find_pages(driver):
    try:
  
        numbers = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'numbers')))
        numbers = numbers.find_elements(By.TAG_NAME, 'div')

        num = numbers[-1].text
        return int(num)
    except Exception:
        return 1


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
            popup = False
            while popup != True:
                popup = click(driver)
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
        driver = get_driver(chrome_options, url, cookies)
        click(driver)
    except Exception:
        driver = get_driver(chrome_options, url, cookies)
        click(driver)
    #clean_up()
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

def get_url(driver, DB, chrome_options,xpath_data, cookies):
 
    url_list = set()
    urls_have = set(DB.loc[:,'url'])

    for i in tqdm(range(1, 2855)):
        time.sleep(random.randrange(1,3))
        try:
            driver.get('https://www.parfumo.net/Reviews?current_page=' +str(i))
        except Exception:
            driver = reset_driver(driver, chrome_options, 'https://www.parfumo.net', cookies)
            driver.get('https://www.parfumo.net/Reviews?current_page=' +str(i))

        try:
            main = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'main')))
            p_boxes = main.find_element(By.CLASS_NAME, 'p-boxes-2')
            p_boxes = p_boxes.find_elements(By.CLASS_NAME, 'p-box')

            for p_box in p_boxes:

                review = p_box.find_element(By.CLASS_NAME, 'grey-box.review-box')
                title = review.find_element(By.CLASS_NAME, 'title')
                url_data = title.find_element(By.TAG_NAME,'a')
                url = url_data.get_attribute('href')
                name = url_data.get_attribute('text')
                
                if url not in urls_have:
                    brand  = review.find_element(By.CLASS_NAME, 'lightblue').get_attribute('text')
                    brand = brand.replace("- ", "")
                    data = {'brand':brand, 'name':name,'year':None,'url':url}
                    DB = DB.append(data, ignore_index = True)
                    DB.to_csv('/home/dhkim/Fragrance/data/fragrance_data2.csv', encoding ='utf-8-sig',  index=False)
                
                url_list.add((name, url))
                
        except Exception:
            continue
    url_list = list(url_list)
    df = pd.DataFrame(url_list)
    df.to_csv('/home/dhkim/Fragrance/data/rating_url.csv', encoding ='utf-8-sig',  index=False)

    return url_list
                        
def rating_crawler(url_data,chrome_options,cookies, write_file):

    driver = get_driver(chrome_options, 'https://www.parfumo.net/Perfumes/Serge_Lutens/ambre-sultan-eau-de-parfum', cookies)
    click(driver)
    rating_data = []
    
    user_list = set()
    user_index = {}

    with open('/home/dhkim/Fragrance/data/rating_data.pkl','rb') as f1:
        rating_data = pickle.load(f1)
    with open('/home/dhkim/Fragrance/data/user_list.pkl','rb') as f2:
        user_list = pickle.load(f2)
    with open('/home/dhkim/Fragrance/data/user_index.pkl','rb') as f3:
        user_index = pickle.load(f3)
    with open('/home/dhkim/Fragrance/data/failed.pkl','rb') as f4:
        failed = pickle.load(f4)


    for i in tqdm(range(4500, len(url_data))):
        data = url_data.iloc[i,:]
        fragrance_name = data[0]
        url = data[1]
        bf = len(rating_data)
        rating_data, failed, user_list, user_index, update = visit_page(driver, chrome_options, url, cookies, fragrance_name, rating_data, user_list, user_index, failed)

        print("Update:"+str(update))
        if update == 0: 
            failed.append(url)
            
        if i % 100 == 0:
            with open('/home/dhkim/Fragrance/data/rating_data.pkl','wb') as f1:
                pickle.dump(rating_data,f1)
            with open('/home/dhkim/Fragrance/data/user_list.pkl','wb') as f2:
                pickle.dump(user_list,f2)
            with open('/home/dhkim/Fragrance/data/user_index.pkl','wb') as f3:
                pickle.dump(user_index,f3)
            with open('/home/dhkim/Fragrance/data/failed.pkl','wb') as f4:
                pickle.dump(failed,f4)

    write_file = write_data(write_file, rating_data)
    write_file.to_csv('/home/dhkim/Fragrance/data/rating_data.csv', encoding ='utf-8-sig')
    write_file.iloc[:,2:] = write_file.iloc[:,2:].astype(np.float16)
    pdb.set_trace()


def rating_crawler2(chrome_options,cookies):
    
    driver = get_driver(chrome_options, 'https://www.parfumo.net/Perfumes/Serge_Lutens/ambre-sultan-eau-de-parfum', cookies)
    click(driver)

    user_list = set()
    failed = []

    #result = pd.DataFrame(columns = ['user_id','gender','nation','brand','fragrance','user_rating'])
    
    #result = result.drop_duplicates()
    result = pd.read_csv('/home/dhkim/Fragrance/data/rating_table.csv',encoding='utf-8-sig')
    #result['user_rating'] = result['user_rating'].astype(np.float16)

    visited = set(list(result['user_id']))

    with open('/home/dhkim/Fragrance/data/user_list.pkl','rb') as f2:
        user_list = list(pickle.load(f2))

    user_list = list(set(user_list))



    for user in tqdm(user_list):
        if (user not in visited) & (isinstance(user, str)):
            update = []
            
            user_url = 'https://www.parfumo.net/Users/' + user
            nation, gender = get_user_info(driver, user_url)
            review_url = 'https://www.parfumo.net/Users/' + user +'/Reviews'
            statement_url = 'https://www.parfumo.net/Users/' + user + '/Statements'
            
            update1 = review_page(driver, review_url, user, nation, gender)
            update.extend(update1)
            update2 = statement_page(driver, statement_url, user, nation, gender)
            update.extend(update2)

            print(user + ':' + str(len(update)))
            visited.add(user)
            result = write_data(result, update)
            result.to_csv('/home/dhkim/Fragrance/data/rating_table.csv', encoding ='utf-8-sig',  index=False)

            with open('/home/dhkim/Fragrance/data/visited.pkl','wb') as f:
                pickle.dump(visited,f)

def get_user_info(driver, url):
    try:
        driver.get(url)
        driver.implicitly_wait(10)
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
    try:
        nation = driver.find_elements(By.CLASS_NAME,'user-badge.user-badge-online')
        nation = nation[0].text
    except Exception:
        nation = None
    
    try:
        main = driver.find_element(By.CLASS_NAME,'main')
        gender = main.find_elements(By.TAG_NAME,'i')[1]
        gender = gender.get_attribute('class')
        if gender == 'fa fa-mars blue gender_idcard' : gender = 'M'
        elif gender == 'fa fa-venus pink gender_idcard' : gender = 'W'
        else: gender = None
    except Exception:
        gender = None
    return nation, gender


def review_page(driver, url, user, nation, gender):

    try:
        driver.get(url)
        driver.implicitly_wait(10)
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
    
    page_num = find_pages(driver)

    result = []

    for current_page in (range(1, page_num + 1)):
        try:
            goto = url +'?current_page=' + str(current_page)
            driver.get(goto)
            time.sleep(random.randrange(1))
        except:
            driver = reset_driver(driver, chrome_options, goto, cookies)
        try:
            review_boxes = driver.find_elements(By.CLASS_NAME, 'review-box-user-reviews-page.grey-box.mb-2')
            if len(review_boxes) != 0:
                for review in review_boxes:
                    dic = {}
                    rating, fragrance, brand = review_find_avg(review)
                    if rating != None:
                        dic['user_rating'] = rating
                        dic['user_id'] = user
                        dic['gender'] = gender
                        dic['nation'] = nation
                        dic['fragrance'] = fragrance
                        dic['brand'] = brand
                        result.append(dic)
            else: return []

        except Exception:
            continue
            
    return result
    



def review_find_avg(review):
    p = re.compile(r'.*(?=\n)')
    try:
        votes = review.find_elements(By.CLASS_NAME, 'ml-1.voting-icon-nr.small')
        score = 0
        num = len(votes)
        for vote in votes:
            rating = p.findall(vote.text)[0]
            if vote.text.replace(rating,'').replace('\n','') == 'Bottle':
                num -= 1
                continue
            else: score += float(rating)

        if num != 0 : rating = round(score / num, 1)
        else : return None, None, None

    except Exception:
        return None, None, None

    try:
        fragrance = review.find_element(By.CLASS_NAME, 'mt-1')
        fragrance_info = fragrance.find_elements(By.TAG_NAME, 'a')[0]
        brand = fragrance.find_elements(By.TAG_NAME, 'a')[1].text
        brand = brand.replace('- ','')
        fragrance = fragrance_info.text
    except Exception:
        fragrance = None
    
    return rating, fragrance, brand


def statement_page(driver, url, user, nation, gender):

    try:
        driver.get(url)
        driver.implicitly_wait(10)
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
    
    page_num = find_pages(driver)

    result = []

    for current_page in (range(1, page_num + 1)):
        try:
            goto = url +'?current_page=' + str(current_page)
            driver.get(goto)
            time.sleep(random.randrange(1))
        except:
            driver = reset_driver(driver, chrome_options, goto, cookies)

        try:
            statement_boxes = driver.find_elements(By.CLASS_NAME, 'statement')
            if len(statement_boxes) != 0:
                for statement in statement_boxes:
                    dic = {}
                    rating, fragrance, brand  = statement_find_avg2(statement)
                    if rating != None:
                        dic['user_rating'] = rating
                        dic['user_id'] = user
                        dic['gender'] = gender
                        dic['nation'] = nation
                        dic['fragrance'] = fragrance
                        dic['brand'] = brand
                        result.append(dic)
            else: return []

        except Exception:
            continue
            
    return result


def statement_find_avg2(statement):
    p = re.compile(r'.*(?=\n)')
    try:
        votes = statement.find_elements(By.CLASS_NAME, 'ml-1.voting-icon-nr.small')
        score = 0
        num = len(votes)
        for vote in votes:
            rating = p.findall(vote.text)[0]
            if vote.text.replace(rating,'').replace('\n','') == 'Bottle':
                num -= 1
                continue
            else: score += float(rating)

        if num != 0 : rating = round(score / num, 1)
        else : return None, None, None

    except Exception:
        return None, None, None

    try:
        fragrance_info = statement.find_element(By.CLASS_NAME, 'right.right_first')
        fragrance_brand= fragrance_info.find_element(By.CLASS_NAME, 'bold').text
        fragrance = fragrance_brand.split('-')[0].strip()
        brand = fragrance_brand.split('-')[1].strip()
    except Exception:
        fragrance = None
    
    return rating, fragrance, brand 


def visit_page(driver, chrome_options, url, cookies, fragrance_name, rating_data, user_list, user_index, failed):

    try:
        driver.get(url)
        driver.implicitly_wait(10)
    except Exception:
        driver = reset_driver(driver, chrome_options, url, cookies)
    

    update = 0
    try:
        review_holder = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'reviews_holder')))
        more = click_more(review_holder)
        articles = review_holder.find_elements(By.TAG_NAME, 'article')

        if more: 
            more_articles = WebDriverWait(review_holder, 5).until(EC.presence_of_element_located((By.ID, 'more-reviews')))
            more_articles = more_articles.find_elements(By.TAG_NAME, 'article')
            articles.extend(more_articles)

        update += len(articles)

        for article in articles:
            header = article.find_element(By.CLASS_NAME, 'review_header')
            ##find rating
            rating = None
            user_id, gender = None, None

            if header != None : rating = article_find_avg(header)
            if rating != None: user_id, gender = article_find_user(article)

            if user_id != None: 
                if user_id not in user_list:
                    user_list.add(user_id)
                    user_index[user_id] = len(user_list) - 1 
                    rating_data.append({'gender':gender, 'user_id':user_id, fragrance_name:rating})

                elif user_id in user_list:
                    index = user_index[user_id]
                    rating_data[i][fragrance_name] = rating

    except Exception:
        failed.append(url)

    try:
        statement_holder = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'statements_holder')))
        statements = statement_holder.find_elements(By.CLASS_NAME, 'statement')
        more = click_more(statement_holder)
        if more: 
            more_statements = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'more-statements')))
            more_statements = more_statements.find_elements(By.CLASS_NAME, 'statement')
            statements.extend(more_statements)
        update += len(statements)
        for statement in statements:
            rating = None
            user_id, gender = None, None

            rating = statement_find_avg(statement)
            if rating != None: user_id, gender = statement_find_user(statement)

            if user_id not in user_list:
                user_list.add(user_id)
                user_index[user_id] = len(user_list) - 1 
                rating_data.append({'gender':gender, 'user_id':user_id,fragrance_name:rating})

            elif user_id in user_list:
                index = user_index[user_id]
                rating_data[index][fragrance_name] = rating

    except Exception:
        failed.append(url)

    return rating_data, failed, user_list, user_index, update



def statement_find_avg(statement):
    p = re.compile(r'.*(?=\n)')
    try:
        votes = statement.find_element(By.CLASS_NAME, 'statement_text.statement-bubble')
        votes = statement.find_element(By.CLASS_NAME, 'statement_text_text.pt-2.pl-2.pr-2')
        votes = statement.find_element(By.CLASS_NAME, 'voting-nrs-statements')
        votes = votes.find_elements(By.CLASS_NAME, 'mr-1.voting-icon-nr.small')
        score = 0
        for vote in votes:
            vote = p.findall(vote.text)[0]
            score += float(vote)
        return round(score / len(votes), 1) 
    except Exception:
        return None


def statement_find_user(statement):
    
    try:
        user = statement.find_element(By.CLASS_NAME, 'statement-top.flex')
        user = user.find_element(By.CLASS_NAME, 'left.nowrap')
        name = user.find_element(By.TAG_NAME, 'a').text
        gender = user.find_element(By.TAG_NAME, 'i').get_attribute('class')

        if gender == 'fa fa-venus.pink': gender = 'W'
        elif gender == 'fa fa-mars.blue': gender = 'M'
        else: gender = None

        return name, gender
    except Exception:
        return None, None

def article_find_user(article):
    try:

        user = article.find_element(By.CLASS_NAME, 'review_user_photo')
        name = user.find_element(By.TAG_NAME, 'span').text
        gender = user.find_element(By.TAG_NAME, 'i').get_attribute('class')
        if gender == 'fa fa-venus pink': gender = 'W'
        elif gender == 'fa fa-mars blue': gender = 'M'
        else: gender = None

        return name, gender
    except Exception:
        return None, None


def article_find_avg(header):
    p = re.compile(r'.*(?=\n)')
    try:
        votes = header.find_elements(By.CLASS_NAME, 'mr-1.voting-icon-nr.small')
        score = 0
        for vote in votes:
            vote = p.findall(vote.text)[0]
            score += float(vote)
        
        return round(score / len(votes), 1) 

    except Exception:
        return None

def click_more(driver):
    try:
        button = driver.find_element(By.CLASS_NAME, 'btn-more-reviews.pbtn-small.ptbn-transparent.width-100.pointer')
        button.click()
        return True
    except Exception:
        return False

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
    warnings.filterwarnings("ignore", category=DeprecationWarning) 
    rating_crawler2(chrome_options, cookies)

  


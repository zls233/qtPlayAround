import time
import random
import pandas as pd
import lxml
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

product_dict = {
    'title': [],
    'price': [],
    'shop_name': [],
    'sales': [],
    'url': [],
    'location': []
}

def sleep_count(t):
    for remaining in range(t, 0, -1):
        print(f'剩余时间: {remaining} 秒', end='\r')  # \r 用于回到行首，不换行
        time.sleep(1)
    print('时间到！')

def First_login(driver):

    driver.get("https://www.taobao.com/")
    input("等待登录完成，按任意键继续...")
    cookies = driver.get_cookies()
    print("cookies获取成功！")

    with open('taobao_cookies.json', 'w') as f:
        json.dump(cookies, f)

    print(cookies)

def driver_init(driver, cookies_path):
    driver.get("https://www.taobao.com/")

    driver.delete_all_cookies()

    with open(cookies_path, 'r') as f:
        cookies = json.load(f)
        
    # driver.add_cookie(cookies)
    for cookie in cookies:
        driver.add_cookie(cookie)
    # s_time = time.time()
    # action = ActionChains(driver)
    # 等待登录成功

    driver.get("https://www.taobao.com/")
    driver.maximize_window()
    # sleep_count(1)
    print('登录成功！')

def Normal_login(cookies_path, driver, input_str, page_num) :
    driver.find_element(By.XPATH, '//*[@id="q"]').send_keys(input_str)
    sleep_count(2)

    driver.find_element(By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button').click()
    sleep_count(2)

    products = driver.find_elements(By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O')

    print('共找到{}个商品'.format(len(products)))

    product_count = 1
    page_count = 1

    for page_count in range(page_num):
        print('第{}页'.format(page_count))
        # 等待产品列表加载
        products = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O'))
        )
        
        
        product_count = 0  # 重置商品计数器
        for product in products:
            try:
                title = product.find_element(By.CLASS_NAME, 'title--F6pvp_RZ').text
            except NoSuchElementException:
                title = '无'
            product_dict['title'].append(title)
            try:
                price = product.find_element(By.CLASS_NAME, 'priceInt--j47mhkXk').text
                price = price.replace('?', '9')
            except NoSuchElementException:
                price = '无'
            product_dict['price'].append(price)
            try:
                shop_name = product.find_element(By.CLASS_NAME, 'shopNameText--APRH8pWb').text
            except NoSuchElementException:
                shop_name = '无'
            product_dict['shop_name'].append(shop_name)
            try:
                sales = product.find_element(By.CLASS_NAME, 'realSales--nOat6VGM').text
                sales = sales.replace('万', '0000')
                sales = sales.replace('+', '')
                sales = sales.replace('人付款', '')
                if(sales.find('人看过') != -1):
                    sales = 0
            except NoSuchElementException:
                sales = '无'
            product_dict['sales'].append(sales)
            try:
                url = product.get_attribute('href')
            except:
                url = '无'
            product_dict['url'].append(url)
            try: 
                location = product.find_element(By.CLASS_NAME, 'procity--QyzqB59i').text
            except:
                location = '无'
            product_dict['location'].append(location)

            product_count += 1
            # time.sleep(0.25)  
            print('商品{}：标题：{}，价格： {}，店铺：{}，销量：{}，地址：{}，链接：{}'.format(product_count, title, price, shop_name, sales, location, url))
            
        # 检查是否有下一页
        try:
            driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
            sleep_count(5)  # 等待下一页加载
        except Exception as error_msg:
            print("error_msg: {}".format(error_msg))
            err = input('再次尝试？(y/n)')
            if err == 'y':
                driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
            else:
                print('退出循环。。。')
                break  

    #保存数据到csv文件
    df = pd.DataFrame(product_dict)
    df.to_csv('mock_taobao_products.csv', index=False, encoding='utf-8')
    print('数据保存成功！')

    # driver.quit()


def crawl_review(driver):
    # 读取数据
    df = pd.read_csv('taobao_products.csv')
    product_dict['title'] = df['title'].tolist()
    product_dict['url'] = df['url'].tolist()
    print('开始爬取评论。。。')
    new_dict = {}
    new_dict['review'] = []
    new_dict['user_name'] = []
    new_dict['title'] = []
    # 爬取评论
    #每爬取20个url，休息10秒
    for i in range(0, len(product_dict['url']), 20):
        urls = product_dict['url'][i:i+20]
        for url in urls:
            new_dict['title'].append(product_dict['title'][i])
            driver.get(url)
            sleep_count(random.randint(1, 3))
            try:
                review = driver.find_element(By.CLASS_NAME, 'content--FpIOzHeP').text
            except:
                review = '无'

            new_dict['review'].append(review)
            try:
                user_name = driver.find_element(By.CLASS_NAME, 'userName--mmxkxkd0').text
            except:
                user_name = '无'
            new_dict['user_name'].append(user_name)
            print('用户名: {}, 评论：{}, 商品：{}'.format(user_name, review, product_dict['title'][i]))
        sleep_count(10)
        stop_loop = input('是否停止？(y/n)')
        if stop_loop == 'y':
            break
    #保存数据到csv文件
    pd.DataFrame(new_dict).to_csv('taobao_reviews.csv', index=False, encoding='utf-8')
    print('数据保存成功！')

if __name__ == '__main__':
    options = webdriver.EdgeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Edge(options=options)
    cookies_path = 'taobao_cookies.json'
    i = input('是否首次登录？(y/n)')
    if i == 'y':
        First_login(driver)
        driver_init(driver, 'taobao_cookies.json')
        input_str = input('请输入搜索关键词：')
        page_num = int(input('请输入搜索页数：'))
        Normal_login(cookies_path, driver, input_str, page_num)
        i = input('是否需要爬取评论？(y/n)')
        if i == 'y':
            crawl_review(driver)
        else:
            print('退出程序。。。')
            driver.quit()
    else:
        driver_init(driver, 'taobao_cookies.json')
        i = input('是否只爬取评论？(y/n)')
        if i == 'y':
            crawl_review(driver)
        else:
            input_str = input('请输入搜索关键词：')
            page_num = int(input('请输入搜索页数：'))
            Normal_login(cookies_path, driver, input_str, page_num)
            i = input('是否需要爬取评论？(y/n)')
            if i == 'y':
                crawl_review(driver)
            else:
                print('退出程序。。。')
                driver.quit()
 
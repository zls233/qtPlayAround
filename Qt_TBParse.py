import sys
import json
import time
import random
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QSpinBox, QTextEdit, QSplitter)
from PySide6.QtCore import Qt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class TaobaoCrawlerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Taobao Crawler')
        self.setGeometry(300, 300, 1000, 800)
        
        self.initUI()
        
        self.driver = None
        self.product_dict = {
            'title': [],
            'price': [],
            'shop_name': [],
            'sales': [],
            'url': [],
            'location': []
        }

    def initUI(self):
        # 设置布局和控件
        layout = QVBoxLayout()

        # 标签和输入框：搜索关键词
        self.keyword_label = QLabel("请输入搜索关键词：", self)
        self.keyword_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.keyword_label)

        self.keyword_input = QLineEdit(self)
        self.keyword_input.setFixedHeight(40)
        self.keyword_input.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.keyword_input)

        # 标签和输入框：页数
        self.page_num_label = QLabel("请输入搜索页数：", self)
        self.page_num_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.page_num_label)

        self.page_num_input = QSpinBox(self)
        self.page_num_input.setFixedHeight(40)
        self.page_num_input.setStyleSheet("font-size: 16px;")
        self.page_num_input.setRange(1, 100)  # 设置页数范围
        layout.addWidget(self.page_num_input)

        # 按钮：首次登录和加载cookie登录
        self.first_login_button = QPushButton('首次登录', self)
        self.first_login_button.setFixedHeight(50)
        self.first_login_button.setStyleSheet("font-size: 16px;")
        self.first_login_button.clicked.connect(self.first_login)
        layout.addWidget(self.first_login_button)

        self.load_cookie_button = QPushButton('加载Cookie登录', self)
        self.load_cookie_button.setFixedHeight(50)
        self.load_cookie_button.setStyleSheet("font-size: 16px;")
        self.load_cookie_button.clicked.connect(self.load_cookie)
        layout.addWidget(self.load_cookie_button)

        # 按钮：启动爬虫
        self.start_crawl_button = QPushButton('开始爬取', self)
        self.start_crawl_button.setFixedHeight(50)
        self.start_crawl_button.setStyleSheet("font-size: 16px;")
        self.start_crawl_button.clicked.connect(self.start_crawl)
        layout.addWidget(self.start_crawl_button)

        # 日志输出窗口
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setFixedHeight(200)
        self.log_text_edit.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.log_text_edit)

        # 商品信息展示表格
        self.product_table = QTableWidget(self)
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(['Title', 'Price', 'Shop', 'Sales', 'URL', 'Location'])
        self.product_table.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.product_table)

        # 中间窗口
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def log_message(self, message):
        """ 在日志窗口中输出信息 """
        self.log_text_edit.append(message)
        self.log_text_edit.ensureCursorVisible()

    def first_login(self):
        # Selenium 操作
        options = webdriver.EdgeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Edge(options=options)

        self.driver.get("https://login.taobao.com/member/login.jhtml?spm=a21bo.jianhua/")
        self.log_message("请手动登录淘宝...")
        self.log_message("登录后请点击按钮继续。")
        self.log_message("请手动登录淘宝，登陆完成后点击确定按钮。")
        self.driver.get("https://www.taobao.com/")
        cookies = self.driver.get_cookies()

        # 保存 cookies
        with open('taobao_cookies.json', 'w') as f:
            json.dump(cookies, f)
        self.log_message("Cookies 已保存成功！")

    def load_cookie(self):
        options = webdriver.EdgeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Edge(options=options)

        self.driver.get("https://www.taobao.com/")
        self.driver.delete_all_cookies()

        # 从文件加载 cookies
        try:
            with open('taobao_cookies.json', 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.get("https://www.taobao.com/")
            self.log_message("登录成功！点击‘开始爬取’开始运行程序。")
        except Exception as e:
            self.log_message(f"加载 Cookies 失败: {str(e)}")

    def start_crawl(self):
        # 获取用户输入的关键词和页数
        keyword = self.keyword_input.text()
        page_num = self.page_num_input.value()

        if not self.driver:
            self.log_message("请先登录淘宝！")
            return

        if keyword == "":
            self.log_message("请输入搜索关键词！")
            return

        try:
            self.normal_login(keyword, page_num)
            self.log_message("商品爬取完成！")
        except Exception as e:
            self.log_message(f"爬取过程中出错: {str(e)}")

    def normal_login(self, input_str, page_num):
        self.driver.find_element(By.XPATH, '//*[@id="q"]').send_keys(input_str)
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button').click()
        time.sleep(2)

        for page_count in range(page_num):
            self.log_message(f'正在爬取第 {page_count + 1} 页...')
            products = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O'))
            )

            for product in products:
                title = product.find_element(By.CLASS_NAME, 'title--F6pvp_RZ').text if product else '无'
                price = product.find_element(By.CLASS_NAME, 'priceInt--j47mhkXk').text.replace('?', '9') if product else '无'
                shop_name = product.find_element(By.CLASS_NAME, 'shopNameText--APRH8pWb').text if product else '无'
                sales = product.find_element(By.CLASS_NAME, 'realSales--nOat6VGM').text.replace('万', '0000') if product else '无'
                url = product.get_attribute('href') if product else '无'
                location = product.find_element(By.CLASS_NAME, 'procity--QyzqB59i').text if product else '无'

                # 保存数据到字典
                self.product_dict['title'].append(title)
                self.product_dict['price'].append(price)
                self.product_dict['shop_name'].append(shop_name)
                self.product_dict['sales'].append(sales)
                self.product_dict['url'].append(url)
                self.product_dict['location'].append(location)

                # 在日志中输出当前爬取商品的信息
                self.log_message(f"商品：{title}, 价格：{price}, 店铺：{shop_name}, 销量：{sales}, 地址：{location}")

            # 下一页
            try:
                next_button = self.driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]')
                next_button.click()
                time.sleep(3)
            except:
                break  # 没有下一页

        # 显示商品信息到表格中
        self.show_product_table()

    def show_product_table(self):
        # 显示爬取的商品信息到 QTableWidget
        self.product_table.setRowCount(len(self.product_dict['title']))
        for row in range(len(self.product_dict['title'])):
            self.product_table.setItem(row, 0, QTableWidgetItem(self.product_dict['title'][row]))
            self.product_table.setItem(row, 1, QTableWidgetItem(self.product_dict['price'][row]))
            self.product_table.setItem(row, 2, QTableWidgetItem(self.product_dict['shop_name'][row]))
            self.product_table.setItem(row, 3, QTableWidgetItem(self.product_dict['sales'][row]))
            self.product_table.setItem(row, 4, QTableWidgetItem(self.product_dict['url'][row]))
            self.product_table.setItem(row, 5, QTableWidgetItem(self.product_dict['location'][row]))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaobaoCrawlerApp()
    window.show()
    sys.exit(app.exec())

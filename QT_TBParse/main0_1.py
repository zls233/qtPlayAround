import sys
import json
import time
import random
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QSpinBox, QTextEdit, QSplitter, QHBoxLayout, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class TaobaoCrawlerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Taobao Crawler')
        self.setGeometry(300, 300, 1000, 400)
        
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
        
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()
        Hlayout = QHBoxLayout()
        Vlayout = QVBoxLayout()

        font = QFont('微软雅黑')

        self.title = QLabel("淘宝商品爬取器 要你命3000", self)
        self.title.setStyleSheet("font-size: 30px; font-weight: bold;")
        self.title.setFont(font)
        Vlayout.addWidget(self.title, alignment=Qt.AlignCenter)

        # 文本：说明
        self.explain_text = QLabel("咋用？\n1.输入搜索关键词和页数\n2.如首次使用请点击'获取cookie' \n3.点击开爬！\n ", self)
        self.explain_text.setStyleSheet("font-size: 16px")
        self.explain_text.setFont(font)
        layout1.addWidget(self.explain_text, alignment=Qt.AlignCenter)

        # 标签和输入框：搜索关键词
        self.keyword_label = QLabel("请输入搜索关键词：", self)
        self.keyword_label.setStyleSheet("font-size: 16px;")
        self.keyword_label.setFont(font)
        layout1.addWidget(self.keyword_label)

        self.keyword_input = QLineEdit(self)
        self.keyword_input.setFixedHeight(40)
        self.keyword_input.setStyleSheet("font-size: 16px;")
        self.keyword_input.setPlaceholderText("请输入搜索关键词")
        self.keyword_input.setFont(font)
        layout1.addWidget(self.keyword_input)

        # 标签和输入框：页数
        self.page_num_label = QLabel("请输入搜索页数：", self)
        self.page_num_label.setStyleSheet("font-size: 16px;")
        self.page_num_label.setFont(font)
        layout1.addWidget(self.page_num_label)

        self.page_num_input = QSpinBox(self)
        self.page_num_input.setFixedHeight(40)
        self.page_num_input.setStyleSheet("font-size: 16px;")
        self.page_num_input.setRange(1, 100)  # 设置页数范围
        self.page_num_input.setFont(font)
        layout1.addWidget(self.page_num_input)

        # 按钮：首次登录和加载cookie登录
        self.first_login_button = QPushButton('获取Cookie', self)
        self.first_login_button.setFixedHeight(50)
        self.first_login_button.setStyleSheet("font-size: 16px;")
        self.first_login_button.clicked.connect(self.first_login)
        self.first_login_button.setFont(font)
        layout1.addWidget(self.first_login_button)

        # self.load_cookie_button = QPushButton('非首次使用：加载Cookie登录', self)
        # self.load_cookie_button.setFixedHeight(50)
        # self.load_cookie_button.setStyleSheet("font-size: 16px;")
        # self.load_cookie_button.clicked.connect(self.load_cookie)
        # self.load_cookie_button.setFont(font)
        # layout1.addWidget(self.load_cookie_button)

        # 按钮：启动爬虫
        self.start_crawl_button = QPushButton('开始爬取', self)
        self.start_crawl_button.setFixedHeight(50)
        self.start_crawl_button.setStyleSheet("font-size: 16px;")
        self.start_crawl_button.clicked.connect(self.start_crawl)
        self.start_crawl_button.setFont(font)
        layout1.addWidget(self.start_crawl_button)

        # 日志输出窗口
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setFixedHeight(200)
        self.log_text_edit.setStyleSheet("font-size: 14px;")
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFont(font)
        layout2.addWidget(self.log_text_edit)

        # 商品信息展示表格
        self.product_table = QTableWidget(self)
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(['Title', 'Price', 'Shop', 'Sales', 'URL', 'Location'])
        self.product_table.setStyleSheet("font-size: 14px;")
        self.product_table.setFont(font)
        layout2.addWidget(self.product_table)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("font-size: 16px;")
        self.progress_bar.setFont(font)
        layout1.addWidget(self.progress_bar)

        Hlayout.addLayout(layout1)
        Hlayout.addLayout(layout2)
        Hlayout.setStretch(0, 1)
        Hlayout.setStretch(1, 2)
        Vlayout.addLayout(Hlayout)


        # 中间窗口
        central_widget = QWidget(self)
        central_widget.setLayout(Vlayout)
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
        QMessageBox.information(self, "登录提示", "请手动登录淘宝，登录后点击确定。")
        self.driver.get("https://www.taobao.com/")
        cookies = self.driver.get_cookies()

        # 保存 cookies
        with open('taobao_cookies.json', 'w') as f:
            json.dump(cookies, f)
        self.log_message("Cookies 已保存成功！")
        QMessageBox.information(self, "登录提示", "Cookies 已保存成功！点击'加载cookies'登录。")
        self.driver.quit()

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
            self.log_message("登录成功！")
            # QMessageBox.information(self, "登录提示", "登录成功！cookies 已加载。点击“开始爬取”来开始爬取数据。")
        except Exception as e:
            self.log_message(f"加载 Cookies 失败: {str(e)}")
            QMessageBox.warning(self, "登录提示", f"加载 Cookies 失败: {str(e)}")
    def start_crawl(self):
        # 获取用户输入的关键词和页数
        self.load_cookie()
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
            self.log_message(f"爬取过程中出错: \n{str(e)}")
        
        self.driver.quit()

    def normal_login(self, input_str, page_num):
        self.driver.maximize_window()
        self.driver.find_element(By.XPATH, '//*[@id="q"]').send_keys(input_str)
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button').click()
        time.sleep(2)

        products = WebDriverWait(self.driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O')))
        total_products_cnt = page_num * len(products)
        current_products_cnt = 0

        for page_count in range(page_num):
            print('第{}页'.format(page_count))
            self.log_message('第{}页'.format(page_count))
            # 等待产品列表加载
            products = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O')))
            
            product_count = 0  # 重置商品计数器
            for product in products:
                try:
                    title = product.find_element(By.CLASS_NAME, 'title--F6pvp_RZ').text
                except NoSuchElementException:
                    title = '无'
                self.product_dict['title'].append(title)
                try:
                    price = product.find_element(By.CLASS_NAME, 'priceInt--j47mhkXk').text
                    price = price.replace('?', '9')
                except NoSuchElementException:
                    price = '无'
                self.product_dict['price'].append(price)
                try:
                    shop_name = product.find_element(By.CLASS_NAME, 'shopNameText--APRH8pWb').text
                except NoSuchElementException:
                    shop_name = '无'
                self.product_dict['shop_name'].append(shop_name)
                try:
                    sales = product.find_element(By.CLASS_NAME, 'realSales--nOat6VGM').text
                    sales = sales.replace('万', '0000')
                    sales = sales.replace('+', '')
                    sales = sales.replace('人付款', '')
                    if(sales.find('人看过') != -1):
                        sales = 0
                except NoSuchElementException:
                    sales = '无'
                self.product_dict['sales'].append(sales)
                try:
                    url = product.get_attribute('href')
                except:
                    url = '无'
                self.product_dict['url'].append(url)
                try: 
                    location = product.find_element(By.CLASS_NAME, 'procity--QyzqB59i').text
                except:
                    location = '无'
                self.product_dict['location'].append(location)

                product_count += 1
                current_products_cnt += 1
                progress = current_products_cnt / total_products_cnt * 100
                self.progress_bar.setValue(progress)
                # time.sleep(0.25)  
                print('商品{}：标题：{}，价格： {}，店铺：{}，销量：{}，地址：{}，链接：{}'.format(product_count, title, price, shop_name, sales, location, url))
                self.log_message('商品{}：标题：{}，价格： {}，店铺：{}，销量：{}，地址：{}，链接：{}'.format(product_count, title, price, shop_name, sales, location, url))
                # 下一页
          # 检查是否有下一页
            try:
                self.driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
                time.sleep(5)  # 等待下一页加载
            except Exception as error_msg:
                print("error_msg: {}".format(error_msg))
                # err = input('再次尝试？(y/n)') 转换成pyside6的QMessageBox
                err = QMessageBox.question(self, "爬取提示", "是否再次尝试？\n错误信息：\n{}".format(error_msg), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if err == QMessageBox.Yes:
                    self.driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
                else:
                    self.log_message("爬取完成！")
                    print('退出循环。。。')
                    break  


        QMessageBox.information(self, "爬取提示", "所有数据爬取完成！")
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

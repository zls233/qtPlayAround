import sys
import json
import time
import random
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QSpinBox, QTextEdit, QSplitter, QHBoxLayout, QMessageBox, QProgressBar, QComboBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QEvent
from PySide6.QtGui import QFont, QIcon, QPixmap
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

global_product_dict = {
    'title': [],
    'price': [],
    'shop_name': [],
    'sales': [],
    'url': [],
    'location': []
}

class LoadCookieThread(QThread):
    update_log = Signal(str)
    finished_load = Signal()

    def __init__(self, driver, cookie_file):
        super().__init__()
        self.driver = driver
        self.cookie_file = cookie_file


    def run(self):
        self.update_log.emit("正在加载Cookie...")
        self.driver.get('https://www.taobao.com')
        self.driver.delete_all_cookies()
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.update_log.emit("Cookie加载成功！")
        except Exception as e:
            self.update_log.emit(f"Cookie加载失败: \n{str(e)}")
            self.finished_load.emit()


class CrawlerThread(QThread):
    update_log = Signal(str)
    update_progress = Signal(int)
    update_table = Signal()
    finished_crawl = Signal()

    def __init__(self, keyword, driver, page_num, product_dict, csv_file):
        super().__init__()
        self.driver = driver
        self.keyword = keyword
        self.page_num = page_num
        self.product_dict = product_dict
        self.csv_file = csv_file

    def run(self):
        self.update_log.emit("正在获取商品信息...")
        self.update_progress.emit(0)
        
        try:
            self.normal_login(self.keyword, self.page_num)
            self.update_log.emit('爬取成功！')
        except Exception as e:
            self.update_log.emit(f"爬取过程中出错: \n{str(e)}")

    def normal_login(self, input_str, page_num):
        self.driver.find_element(By.XPATH, '//*[@id="q"]').send_keys(input_str)
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button').click()
        time.sleep(2)
        products = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O')))
        total_products_cnt = page_num * len(products)
        current_products_cnt = 0
        for page_count in range(page_num):
            self.update_log.emit(f'第{page_count}页')
            products = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'doubleCardWrapper--BpyYIb1O')))
            product_count = 0
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
                    price = '0'
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
                    sales = '0'
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
                self.update_progress.emit(int(current_products_cnt / total_products_cnt * 100))
                self.update_log.emit(f"已获取{current_products_cnt}个商品信息")
                self.update_log.emit(f"当前商品：{title}，价格：{price}，店铺：{shop_name}，销量：{sales}，地区：{location}")
                self.update_table.emit()
        # 检查是否有下一页
            if page_num != page_count + 1:
                try:
                    ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()  
                    ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()  
                    ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()  
                    ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()  
                    ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()  
                    ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()  
                    self.driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
                    time.sleep(5)  # 等待下一页加载
                except Exception as error_msg:
                    print("error_msg: {}".format(error_msg))
                    # err = input('再次尝试？(y/n)') 转换成pyside6的QMessageBox
                    for tries in range(5): 
                        try:
                            print("trying to click next page button...")
                            self.update_log.emit("翻页错误，重新尝试点击下一页按钮...")
                            ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()  
                            ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()  
                            self.driver.find_element(By.XPATH, '//*[@id="sortBarWrap"]/div[1]/div[2]/div[2]/div[8]/div/button[2]').click()
                            break
                        except:
                            continue
        pd.DataFrame(self.product_dict).to_csv(self.csv_file, index=False, encoding='utf-8')
        print('数据保存成功！')
        self.update_log.emit("爬取完成！")
        self.update_log.emit('数据已保存到{}'.format(self.csv_file))
        self.finished_crawl.emit()
        # self.driver.quit()
            
class TaobaoCrawlerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Taobao Crawler')
        self.setGeometry(300, 300, 1000, 800)
        
        self.initUI()
        
        options = webdriver.EdgeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Edge(options=options)
        self.driver.maximize_window()
        # self.driver.minimize_window()
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
        
        Vlayout1 = QVBoxLayout()
        Vlayout2 = QVBoxLayout()
        Hlayout = QHBoxLayout()
        Hlayout2 = QHBoxLayout()
        Vlayout3 = QVBoxLayout()
        zls233 = QVBoxLayout()

        font = QFont('微软雅黑')

        self.title = QLabel("要你命3000淘宝商品爬取器V0.2.2", self)
        self.title.setStyleSheet("font-size: 30px; font-weight: bold;")
        self.title.setFont(font)
        Vlayout3.addWidget(self.title, alignment=Qt.AlignCenter)

        self.image = QLabel(self)
        self.image.setPixmap(QPixmap("bean.jpg"))
        self.image.setFixedSize(80, 80)
        self.image.setScaledContents(True)
        self.image.setStyleSheet("border: 1px solid black;")
        zls233.addWidget(self.image, alignment=Qt.AlignCenter)

        self.name = QLabel("@zls233", self)
        self.name.setStyleSheet("font-size: 16px;")
        zls233.addWidget(self.name, alignment=Qt.AlignCenter)

        Hlayout2.addLayout(zls233)

        # 文本：说明
        self.explain_text = QLabel("咋用？\n1.输入搜索关键词和页数\n2.如首次使用请点击'获取cookie' \n3.点击开爬！\n ", self)
        self.explain_text.setStyleSheet("font-size: 16px")
        self.explain_text.setFont(font)
        Hlayout2.addWidget(self.explain_text, alignment=Qt.AlignCenter)

        Vlayout1.addLayout(Hlayout2)

        self.cookie_file_label = QLabel("Cookie文件路径：", self)
        self.cookie_file_label.setStyleSheet("font-size: 16px;")
        self.cookie_file_label.setFont(font)
        Vlayout1.addWidget(self.cookie_file_label)

        self.cookie_file_input = QLineEdit(self)
        self.cookie_file_input.setFixedHeight(40)
        self.cookie_file_input.setStyleSheet("font-size: 16px;")
        #设置默认路径
        self.cookie_file_input.setText("taobao_cookies.json")
        self.cookie_file_input.setFont(font)
        Vlayout1.addWidget(self.cookie_file_input)

        self.csv_file_label = QLabel("CSV文件路径：", self)
        self.csv_file_label.setStyleSheet("font-size: 16px;")
        self.csv_file_label.setFont(font)
        Vlayout1.addWidget(self.csv_file_label)

        self.csv_file_input = QLineEdit(self)
        self.csv_file_input.setFixedHeight(40)
        self.csv_file_input.setStyleSheet("font-size: 16px;")
        #设置默认路径
        self.csv_file_input.setText("taobao_products.csv")
        self.csv_file_input.setFont(font)
        Vlayout1.addWidget(self.csv_file_input)

        # 标签和输入框：搜索关键词
        self.keyword_label = QLabel("请输入搜索关键词：", self)
        self.keyword_label.setStyleSheet("font-size: 16px;")
        self.keyword_label.setFont(font)
        Vlayout1.addWidget(self.keyword_label)

        self.keyword_input = QLineEdit(self)
        self.keyword_input.setFixedHeight(40)
        self.keyword_input.setStyleSheet("font-size: 16px;")
        self.keyword_input.setPlaceholderText("请输入搜索关键词")
        self.keyword_input.setFont(font)
        Vlayout1.addWidget(self.keyword_input)

        # 标签和输入框：页数
        self.page_num_label = QLabel("请输入搜索页数：", self)
        self.page_num_label.setStyleSheet("font-size: 16px;")
        self.page_num_label.setFont(font)
        Vlayout1.addWidget(self.page_num_label)

        self.page_num_input = QSpinBox(self)
        self.page_num_input.setFixedHeight(40)
        self.page_num_input.setStyleSheet("font-size: 16px;")
        self.page_num_input.setRange(1, 100)  # 设置页数范围
        self.page_num_input.setFont(font)
        Vlayout1.addWidget(self.page_num_input)

        # 按钮：加载cookies

        # 按钮：首次登录和加载cookie登录
        self.first_login_button = QPushButton('获取Cookie', self)
        self.first_login_button.setFixedHeight(50)
        self.first_login_button.setStyleSheet("font-size: 16px;")
        self.first_login_button.clicked.connect(self.first_login)
        self.first_login_button.setFont(font)
        Vlayout1.addWidget(self.first_login_button)

        # 按钮：启动爬虫
        self.start_crawl_button = QPushButton('开始爬取', self)
        self.start_crawl_button.setFixedHeight(50)
        self.start_crawl_button.setStyleSheet("font-size: 16px;")
        self.start_crawl_button.clicked.connect(self.start_crawl)
        self.start_crawl_button.setFont(font)
        Vlayout1.addWidget(self.start_crawl_button)

        # 日志输出窗口
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setFixedHeight(200)
        self.log_text_edit.setStyleSheet("font-size: 14px;")
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFont(font)
        Vlayout2.addWidget(self.log_text_edit)

        # 商品信息展示表格3
        self.product_table = QTableWidget(self)
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(['Title', 'Price', 'Shop', 'Sales', 'URL', 'Location'])
        self.product_table.setStyleSheet("font-size: 14px;")
        self.product_table.setFont(font)
        Vlayout2.addWidget(self.product_table)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("font-size: 16px;")
        self.progress_bar.setFont(font)
        Vlayout1.addWidget(self.progress_bar)

        Hlayout.addLayout(Vlayout1)
        Hlayout.addLayout(Vlayout2)
        Hlayout.setStretch(0, 1)
        Hlayout.setStretch(1, 2)
        Vlayout3.addLayout(Hlayout)


        # 中间窗口
        central_widget = QWidget(self)
        central_widget.setLayout(Vlayout3)
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

    def start_crawl(self):
        # 获取用户输入的关键词和页数
        keyword = self.keyword_input.text()
        page_num = self.page_num_input.value()
        cookie_file = self.cookie_file_input.text()
        csv_file = self.csv_file_input.text()

        self.load_cookie_thread = LoadCookieThread(self.driver, cookie_file)
        self.load_cookie_thread.update_log.connect(self.log_message)
        self.load_cookie_thread.finished_load.connect(self.start_crawl_button.clicked)
        self.load_cookie_thread.start()

        if not self.driver:
            self.log_message("请先登录淘宝！")
            QMessageBox.warning(self, "登录提示", "请先登录淘宝！")
            return

        if keyword == "":
            self.log_message("请输入搜索关键词！")
            QMessageBox.warning(self, "搜索提示", "请输入搜索关键词！")
            return
        
        self.crawl_thread = CrawlerThread(keyword, self.driver, page_num, self.product_dict, csv_file)
        self.crawl_thread.update_log.connect(self.log_message)
        self.crawl_thread.update_progress.connect(self.progress_bar.setValue)
        self.crawl_thread.update_table.connect(self.show_product_table)
        self.crawl_thread.start()

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
        # 滑动到最后一行
        self.product_table.scrollToBottom()

    def closeEvent(self, event: QEvent):
        if self.driver:
            self.driver.quit()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaobaoCrawlerApp()
    window.show()
    sys.exit(app.exec())

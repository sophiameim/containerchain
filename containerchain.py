import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from utils import google_sheet_utils
from utils.google_sheet_utils import get_worksheet, str_to_datetime
import copy
from config import containerchain_config
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
# 设置登录网页
URL = containerchain_config.CONTAINERCHAINURL
EMPTYDEPOTCHECKURL = containerchain_config.EMPTYDEPOTINQUIRY

def __init__(self,  wait_time=10):
    self.config = containerchain_config
    self.browser = webdriver.Chrome()
    self.wait_time = wait_time
    self.wait = WebDriverWait(self.browser, self.wait_time)

def initialize_communication_and_data():
    # 建立通信 & 打开源文档
    WORKSHEET = get_worksheet(containerchain_config.SHEET_URL, containerchain_config.WORKSHEET_NAME)

    # 一次性获得整个工作表数据
    all_data = google_sheet_utils.get_all_data(WORKSHEET)

    # 备份工作表数据 以比较需要更新的部分
    old_data = copy.deepcopy(all_data)

    # 获取表头
    headers = all_data[0]

    return WORKSHEET, all_data, old_data, headers


def filter_data(all_data, headers):

    # 获取 "id"
    id_numbers_col_index = headers.index("ID")
    all_id_numbers = [row[id_numbers_col_index] for row in all_data[1:]]

    # 获取 "BOOKING REF"
    booking_refs_col_index = headers.index("BOOKING REF")
    booking_refs = [row[booking_refs_col_index] for row in all_data[1:]]

    # 获取 "Logitics Status"
    logitics_status_col_index = headers.index("Logitics Status")
    logitics_status = [row[logitics_status_col_index] for row in all_data[1:]]

    # 获取 "First Free"
    first_free_col_index = headers.index("First Free")
    first_free = [row[first_free_col_index] for row in all_data[1:]]

    # 获取 "Export Check"
    export_check_col_index = headers.index("Export Check")
    export_check = [row[export_check_col_index] for row in all_data[1:]]
    # 创建 booking_ref 到 ID 的映射，确保一个 booking_ref 可以对应多个 ID
    booking_ref_to_id = {booking_refs[i]: [all_id_numbers[i]] for i in range(len(all_id_numbers))}
    

    # 当前日期时间
    now = datetime.datetime.now()
    two_day_later = now + datetime.timedelta(days=2)

    # 根据条件筛选id NUMBER
    filtered_id_numbers = []
    filtered_booking_refs = []  # 新增的列表来存储筛选后的booking ref
    for i in range(len(all_id_numbers)):


        formatted_date = str_to_datetime(first_free[i])  # 直接使用 first_free[i]
        if formatted_date is None:
            print(f"Row {i + 2}: Skipped due to invalid first_free format: {first_free[i]}")
            continue

        if formatted_date > two_day_later:
            print(f"Row {i + 2}: Skipped due to first_free > now + 2 day: {formatted_date}")
            continue


        if logitics_status[i] in ["Yard(F)","Client","Yard(E)","Empty Park"]:
            print(f"Row {i + 2}: Skipped due to logitics status: {logitics_status[i]}")
            continue

        if export_check[i] in ["Completed"]:
            print(f"Row {i + 2}: Skipped due to export_check: {export_check[i]}")
            continue

        filtered_id_numbers.append(all_id_numbers[i])
        filtered_booking_refs.append(booking_refs[i])  # 同时添加对应的BOOKING REFS到新列表

    print("Filtered ID NUMBERs:", filtered_id_numbers)
    print("Filtered BOOKING REFS:", filtered_booking_refs)  # 打印筛选后的BOOKING REFS

    return all_id_numbers, filtered_id_numbers, filtered_booking_refs, booking_ref_to_id # 返回三个列表

class ContainerchainScraper:

    def __init__(self, booking_refs, wait_time=10):
        self.config = containerchain_config
        chrome_options = Options()
        #chrome_options.add_argument("--headless")   无头模式
        #chrome_options.add_argument("--window-size=1920,1080")  # 设置默认窗口大小
        chrome_options.add_argument("--start-maximized")  # 开始最大化（对于非无头模式）
        #chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速（在某些系统中可能是必要的）
        #chrome_options.add_argument("--remote-debugging-port=9222")
        self.browser = webdriver.Chrome(options=chrome_options)
        self.wait_time = wait_time
        self.wait = WebDriverWait(self.browser, self.wait_time)
        self.booking_refs = booking_refs


    def login(self):
        username = containerchain_config.USERNAME
        password = containerchain_config.PASSWORD
        url = containerchain_config.CONTAINERCHAINURL
        self.browser.get(url)

        homepage_link_text = 'Containerchain Home Page'
        login_xpath = '//a[text()="Login"]'
        
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, homepage_link_text))).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, login_xpath))).click()
        
        self.browser.find_element(By.ID, 'username').send_keys(username)
        self.browser.find_element(By.ID, 'password').send_keys(password)
        self.browser.find_element(By.ID, 'login').click()
        try:
            close_button_selector = ".modal-header .close"
            WebDriverWait(self.browser, self.wait_time).until(EC.element_to_be_clickable((By.CSS_SELECTOR, close_button_selector))).click()
            print("关闭按钮被点击")
        except NoSuchElementException:
            print("没有找到关闭按钮，继续执行后续操作")



    
    def navigate_to_inquiry(self):
        inquiry_link_text = 'Inquiry'
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, inquiry_link_text))).click()

        empty_depot_inquiry_text = 'Empty Depot Inquiry'
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, empty_depot_inquiry_text))).click()

    def navigate_and_filter(self, booking_ref):
        select_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "select[ng-model='searchType']")))
        select = Select(select_element)
        select.select_by_value("ReleaseInformation")
        input_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[ng-model='searchValue']")))
        input_element.clear()
        input_element.send_keys(booking_ref)
        search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[ng-click='doSearch()']")))
        search_button.click()

        loading_mask = "div.loading-outer-container"  # 这是阻挡点击的元素的CSS选择器
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_mask)))

        

        # 检查是否存在错误消息
        error_message_elements = self.browser.find_elements(By.CSS_SELECTOR, ".alert.alert-danger")
        for element in error_message_elements:
            if "Release not found or you may not have access to the Port of Operation" in element.text:
                print(f"跳过 booking_ref {booking_ref}.")
                return None
            
        # 获取页面上显示的 Release Number
        container_release_selector = ".container-release"
        release_number_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, container_release_selector)))
        page_release_number = release_number_element.text.strip() if release_number_element else "Not Found"
        # 检查页面上的 Release Number 是否与输入的 Release Number 匹配
        if page_release_number != booking_ref:
            print(f"页面上的 Release Number {page_release_number} 与输入的 {booking_ref} 不匹配。")
            return None
            
    
        empty_park_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h4.recent-title.p-none.m-none")))
        empty_park = empty_park_element.text if empty_park_element else "Not Found"
        print(f"Empty Park : {empty_park}")
        qty_on_release_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".col-xs-12.col-sm-1.text-right strong")))
        qty_on_release = qty_on_release_element.text if qty_on_release_element else "Not Found"
        print(f"Qty On Release: {qty_on_release}")
        expiry_date_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".col-xs-12.col-sm-2.text-center strong")))
        expiry_date = expiry_date_element.text if expiry_date_element else "Not Found"
        print(f"Expiry Date: {expiry_date}")
        ready_date_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "table tbody tr td:nth-of-type(6)")))
        ready_date = ready_date_element.text if ready_date_element else "Not Found"
        print(f"Ready Date: {ready_date}")
        time.sleep(1)

        # 现在获取页面上的 Release Details 下的 release number
        release_number_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".container-release")))
        release_number = release_number_element.text.strip()  # 删除可能的前后空白字符
        # 检查 release number 是否与提供的 booking_ref 匹配
        if release_number != booking_ref:
            print(f"Release number {release_number} does not match booking_ref {booking_ref}. Skipping fill.")
            return None  # 不匹配则返回 None，这样就不会继续填充数据
        
        return {
            'booking_ref': booking_ref,
            "Empty Park": empty_park,
            "Qty On Release": qty_on_release,
            "Ready Date": ready_date,
            "Expiry Date": expiry_date
         }
    
    def run(self):
        self.login()
        self.navigate_to_inquiry()
        fetched_data = []
        for booking_ref in self.booking_refs:
            data = self.navigate_and_filter(booking_ref)
            if data:  # 确保 data 不是 None
                fetched_data.append(data)
            else:
                print(f"booking_ref {booking_ref} 被跳过，没有添加到 fetched_data。")
            
        return fetched_data
        

def write_data_to_google_sheet(WORKSHEET, all_data, old_data, headers, fetched_data, all_id_numbers, booking_ref_to_id):
    for data in fetched_data:
        if data is None:  # 检查是否为 None
            continue  # 如果是 None，就跳过当前迭代
        booking_ref = data['booking_ref']
        ids = booking_ref_to_id.get(booking_ref, [])
        for id in ids:
            row_number = all_id_numbers.index(id) + 1
            # 在这里根据 row_number 更新 all_data 中的对应行
            all_data[row_number][headers.index("Empty Park")] = data["Empty Park"]
            all_data[row_number][headers.index("Qty On Release")] = data["Qty On Release"]
            all_data[row_number][headers.index("Ready Date")] = data["Ready Date"]
            all_data[row_number][headers.index("Expiry Date")] = data["Expiry Date"]
        else:
            print(f"找不到 booking_ref 对应的 ID: {booking_ref}")

    # 更新工作表数据
    google_sheet_utils.update_changed_data(WORKSHEET, old_data, all_data)


def main():
    WORKSHEET, all_data, old_data, headers = initialize_communication_and_data()
    all_id_numbers, filtered_id_numbers, filtered_booking_refs, booking_ref_to_id = filter_data(all_data, headers)
    scraper = ContainerchainScraper(filtered_booking_refs)
    fetched_data = scraper.run()
    # 传递 all_id_numbers 给 write_data_to_google_sheet 函数
    write_data_to_google_sheet(WORKSHEET, all_data, old_data, headers, fetched_data, all_id_numbers, booking_ref_to_id)
if __name__ == '__main__':
    main()

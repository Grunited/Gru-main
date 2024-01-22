from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-data-dir=/Users/arvindh/Library/Application Support/Google/Chrome/")
driver = webdriver.Chrome(options=options)
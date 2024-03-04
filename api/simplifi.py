import logging
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from seleniumrequests import Chrome

logging.basicConfig()
log = logging.getLogger('simplifi')
log.setLevel(logging.DEBUG)


class IncorrectPasswordException(Exception):
  pass


class Simplify:
  def __init__(self, username, password, session_path=None, headless=False):
    chrome_options = ChromeOptions()
    if headless:
      chrome_options.add_argument("headless")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-dev-shm-usage")
    chrome_options.add_argument("disable-gpu")
    if session_path is not None:
      chrome_options.add_argument("user-data-dir=%s" % session_path)
    self.driver = Chrome(options=chrome_options)
    self.username = username
    self.password = password

  def enter_username(self, username):
    WebDriverWait(self.driver, 20).until(
        ec.presence_of_element_located((By.ID, 'username'))
    )
    email_input = self.driver.find_element(By.ID, 'username')
    email_input.clear()
    time.sleep(1)
    email_input.click()
    time.sleep(1)
    email_input.send_keys(username)
    time.sleep(1)
    continue_button = self.driver.find_element(By.ID, 'submit-continue')
    continue_button.click()

  def enter_password(self, password):
    WebDriverWait(self.driver, 20).until(
        ec.presence_of_element_located((By.ID, 'current-password'))
    )
    password_input = self.driver.find_element(By.ID, 'current-password')
    password_input.click()
    time.sleep(1)
    password_input.send_keys(password)
    time.sleep(1)
    self.driver.find_element(By.ID, 'rememberMe').click()
    time.sleep(1)
    self.driver.find_element(By.ID, 'submit-sign-in').click()

  def login(self):
    self.driver.get('https://app.simplifimoney.com/')

    # Check if already logged in.
    if self.is_logged_in():
      log.info('Already logged in')
      self.wait_to_load()
      return
    log.info('Logging in')

    log.debug('Waiting for login frame to be available')
    WebDriverWait(self.driver, 20).until(
        ec.frame_to_be_available_and_switch_to_it('login_frame'))

    log.debug('Entering username and password')
    self.enter_username(self.username)
    self.enter_password(self.password)

    # Check if password was incorrect.
    if self.incorrect_password():
      raise IncorrectPasswordException('Incorrect password')

    # Check if MFA was requested.
    self.mfa()

    # Wait for the page to load.
    log.info('Waiting for data to load')
    self.wait_to_load()

    log.info('Logged in')

  def mfa(self):
    time.sleep(2)
    try:
      self.driver.find_element(By.ID, 'mfa-for-signup-signin')
    except NoSuchElementException:
      return
    print('Enter MFA')
    mfa = input()
    self.driver.find_element(By.ID, 'mfa-for-signup-signin').send_keys(mfa)
    time.sleep(1)
    self.driver.find_element(By.ID, 'submit-mfa-for-signup-and-signin').click()

  def incorrect_password(self):
    time.sleep(2)
    incorrect_password_banner = None
    try:
      incorrect_password_banner = self.driver.find_element(By.XPATH,
                                                           '/html/body/div/div[3]/div/div/div[1]/div[2]/div[1]/div[2]')
    except NoSuchElementException:
      return False
    return 'Invalid Quicken ID or password' in incorrect_password_banner.text

  def wait_to_load(self, timeout=600):
    self.driver.switch_to.parent_frame()
    WebDriverWait(self.driver, timeout).until(
        ec.presence_of_element_located(
            (By.CSS_SELECTOR, '[aria-label="Refresh All"]'))
    )

  def is_logged_in(self, timeout=10):
    try:
      WebDriverWait(self.driver, timeout).until(
          ec.presence_of_element_located(
              (By.ID, 'logo-nav'))
      )
    except TimeoutException:
      return False
    return True

  def get_account_data(self):
    response = self.driver.request(
        method='GET',
        url='https://services.quicken.com/accounts',
        headers=self.headers()
    )
    response.raise_for_status()
    accounts = response.json()['resources']
    return accounts

  def headers(self):
    bearer_token = self.driver.execute_script(
        'return JSON.parse(window.localStorage.getItem("authSession")).accessToken')
    dataset_id = self.driver.execute_script(
        'return JSON.parse(window.localStorage.getItem("authSession")).datasetId')
    headers = {
        "accept": "application/json",
        "authorization": f'Bearer {bearer_token}',
        "qcs-dataset-id": dataset_id,
    }
    return headers

  def close(self):
    self.driver.quit()

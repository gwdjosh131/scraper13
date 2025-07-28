import os
from google import genai
import re
from google.genai import types


from constants import *
import random
import requests
from colorama import Fore, Style
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import json
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from selenium.common import TimeoutException, ElementClickInterceptedException, NoSuchElementException, \
    StaleElementReferenceException, JavascriptException, WebDriverException # Added JS/WD Exceptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # Keep for potential standard waits elsewhere
from selenium.webdriver.common.by import By # Keep for potential standard waits elsewhere
from selenium.webdriver.common.action_chains import ActionChains
from typing import Optional, Tuple, List # Use Tuple, List directly
import time


def driver_init(window_size:tuple=(), headless=False) -> WebDriver:
    """
    This function initializes the webdriver instance, in order to be undetectable by facebook.
    Returns:
        WebDriver
    """
    # Configure Chrome options to be less detectable
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2
            # with 2 should disable notifications
        },
    )
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    if headless:
        chrome_options.add_argument('headless')
    else:
        chrome_options.add_argument("start-maximized")


    # Set a realistic user agent
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=chrome_options)
    if headless:
        driver.set_window_size(1440, 797)

    if window_size:
        driver.set_window_size(window_size[0], window_size[1])
    else:
        pass

    # Execute CDP commands to avoid detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    })

    return driver


def login(driver: WebDriver, group_link: str, use_cookies: bool = False):
    driver.get("https://facebook.com")
    load_dotenv()
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    # Use variable wait times for different elements
    driver.implicitly_wait(random.uniform(2, 4))


    if use_cookies and group_link:
        driver.get(group_link)
        with open("storage/cookies.json", "r") as f:
            cookie_list = json.load(f)

        for cookie in cookie_list:
            driver.add_cookie(cookie)

        driver.refresh()
    else:
        # Find login elements
        email_input = driver.find_element(by=By.ID, value="email")
        time.sleep(1.2)
        password_input = driver.find_element(by=By.NAME, value="pass")
        time.sleep(1.1)
        submit_button = driver.find_element(by=By.NAME, value="login")

        # Type like a human with varied speed
        def human_type(element, text):
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(.2, .4))

        # Login with credentials
        human_type(email_input, email)
        time.sleep(1)
        human_type(password_input, password)
        time.sleep(random.uniform(1, 2))
        submit_button.click()
        time.sleep(random.uniform(1, 2))


def check_facebook_captcha_links(html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks for Facebook CAPTCHA presence based *only* on image/audio links.

    Args:
        html_content: The HTML content of the page as a string.

    Returns:
        A tuple: (is_captcha: bool, image_link: Optional[str], audio_link: Optional[str])
        - is_captcha is True if a CAPTCHA image or audio link is found.
        - image_link is the src of the CAPTCHA image if found, else None.
        - audio_link is the href of the CAPTCHA audio link if found, else None.
    """
    if not html_content:
        return False, None, None

    image_link = None
    audio_link = None

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Check for the CAPTCHA image source pattern
        captcha_image_tag = soup.find('img', src=re.compile(r'/captcha/tfbimage/', re.IGNORECASE))
        if captcha_image_tag and captcha_image_tag.get('src'):
            image_link = captcha_image_tag['src']

        # 2. Check for the CAPTCHA audio link pattern
        captcha_audio_tag = soup.find('a', href=re.compile(r'/captcha/tfbaudio/', re.IGNORECASE))
        if captcha_audio_tag and captcha_audio_tag.get('href'):
            audio_link = captcha_audio_tag['href']

        # 3. Determine presence based on finding either link
        is_captcha = image_link is not None or audio_link is not None

        if is_captcha:
            return True, image_link, audio_link
        else:
            return False, None, None

    except Exception as e:
        print(f"Something went wrong during the captcha check: {e}")
        return False, None, None # Be conservative on error


def solve_captch(audio_link) -> str:
    # get GEMINI_API and GEMINI_MODEL from .env
    load_dotenv()
    api_key = os.getenv("GEMINI_API")
    model = os.getenv("GEMINI_MODEL")
    prompt = """You are solving a CAPTCHA. Based on the attached information what is the captcha phrase (there can be numbers)?

    Use this JSON schema:

    captcha_string = {"captcha_phrase": str}
    Return: captch_string"""
    client = genai.Client(api_key=api_key)

    # open the audio link, then find the link within that page and use that link to download the audio
    r = requests.get(audio_link)
    soup = BeautifulSoup(r.content, 'html.parser')
    audio_download_url = soup.find('audio')["src"]
    audio_content = requests.get(audio_download_url).content

    response = client.models.generate_content(
        model=model, contents=[prompt,
                               types.Part.from_bytes(data=audio_content, mime_type="audio/mp3")]
    )

    return response.text


def captcha_interact(driver: WebDriver, debug: bool=False) -> bool:
    try:
        time.sleep(1)
        status, image, audio = check_facebook_captcha_links(driver.page_source)
        if status:  # if there is a captcha
            captcha_phrase = solve_captch(audio).replace("```", "").replace('json',
                                                                                   '')  # Gemini inputs captcha audio and outputs JSON of the answer
            captcha_phrase = json.loads(captcha_phrase)["captcha_phrase"]  # captcha phrase recorded and saved
            # phrase input
            input_field = find_element_bs4(driver, driver.find_element(By.TAG_NAME, value="body"),
                                           [captcha_input_class])
            captcha_login_button = find_element_bs4(driver, driver.find_element(By.TAG_NAME, value="body"),
                                                    [captcha_login_class])

            if input_field and captcha_login_button:
                # phrase submitted
                input_field.send_keys(captcha_phrase)
                captcha_login_button.click()
            else:
                print(f"{Fore.BLUE}No captcha found{Style.RESET_ALL}")

            current_url = driver.current_url
            try:
                WebDriverWait(driver, 10).until(EC.url_changes(current_url))
            except Exception as e:
                print(f"Timed out waiting for URL to change. {e}")

            # check that the bot has successfully logged in and is ready to scrape.
            current_cookies = str(driver.get_cookies())
            if current_cookies.find("'c_user'") != -1 or current_cookies.find("'xs'") != -1:
                if debug: print(f"{Fore.GREEN}Current Cookies, containing xs and c_user: {current_cookies}{Style.RESET_ALL}")
                if debug: print(f"{Fore.GREEN}Solved Captcha - Successfully Logged In{Style.RESET_ALL}")
                return True
            else:
                return False
        else:
            return True

    except Exception as e:
        print(f"Something went wrong during the captcha check: {e}")

    return False

# ------------------------------------------------
# NON CAPTCHA / SETUP RELATED FUNCTIONS
# ------------------------------------------------

# Finished
def scroll_and_wait_for_new_posts(driver: WebDriver, known_post_count: int, timeout: int = 25) -> bool:
    """
    Actively scrolls and waits for new post-elements to appear in the DOM after a scroll.

    Args:
        driver: The Selenium WebDriver instance.
        known_post_count: The number of posts detected *before* the scroll action
                          that triggered this wait.
        timeout: Maximum time in seconds to wait for new posts to appear.

    Returns:
        True if the number of posts increased within the timeout period,
        False if the timeout was reached without detecting new posts.
    """
    if not post_class:
        print(f"{Fore.RED}Error: post_class constant is empty. Cannot wait for posts.{Style.RESET_ALL}")
        return False # Cannot proceed without a valid selector

    # Construct the CSS selector: ".class1.class2" if post_class is "class1 class2"
    post_class_selector = "." + ".".join(post_class.split())
    if post_class_selector == ".": # Avoid overly broad selector if split results in an empty list
         print(f"{Fore.RED}Error: post_class resulted in an invalid selector '{post_class_selector}'.{Style.RESET_ALL}")
         return False

    try:
        wait = WebDriverWait(driver, timeout)

        def scroll_check(d: WebDriver):
            # scroll to bottom of page
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            return len(d.find_elements(By.CSS_SELECTOR, post_class_selector)) > known_post_count

        # Continue to scroll and wait until scroll_check returns True
        wait.until(scroll_check)

        # If wait.until() succeeds without TimeoutException, it means new posts were loaded.
        return True

    except TimeoutException:
        # The timeout was reached before the condition (more posts appearing) was met.
        # This usually indicates the end of the feed or very slow loading.
        print(f"{Fore.YELLOW}Timeout: No new posts found after {timeout} seconds. Likely end of feed.{Style.RESET_ALL}")
        return False
    except Exception as e:
        # Catch any other unexpected WebDriver or element finding errors during the wait.
        print(f"{Fore.RED}An unexpected error occurred while waiting for new posts: {e}{Style.RESET_ALL}")
        return False

# Finished
def get_rendered_posts(driver: WebDriver) -> list[WebElement]:
    try:
        feed_element = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

        # --- Dynamically build the XPath selector ---

        # 1. Split the post_class string from constants.py into individual classes
        individual_classes = post_class.split()  # Handles space separation

        if not individual_classes:
            raise ValueError("Error: post_class constant seems to be empty or invalid.")
        else:
            # 2. Create the "contains(...)" condition string for each class
            #    We use f-strings for easy insertion of the class name 'cls'.
            #    Note the crucial spaces inside the single quotes: '{cls}'
            conditions = [f"contains(concat(' ', normalize-space(@class), ' '), ' {cls} ')" for cls in
                          individual_classes]

            # 3. Join these conditions with "and"
            joined_conditions = " and ".join(conditions)

            # 4. Construct the final relative XPath selector
            #    Selects direct children (*) of the current node (.)
            #    that satisfy all the joined conditions [...]
            dynamic_xpath_selector = f"./*[{joined_conditions}]"

            # --- End of dynamic XPath building ---

        try:
            post_elements = feed_element.find_elements(By.XPATH, dynamic_xpath_selector)
            return post_elements
        except NoSuchElementException as e:
            raise NoSuchElementException(f"Unable to locate posts: {e}")
    except NoSuchElementException as e:
        print(f"{Fore.RED}Unable to locate the feed_element:\n{e}{Style.RESET_ALL}")
        return []

# Finished
def open_post(post: WebElement, driver: WebDriver, actions: ActionChains, wait_time: int = 10) -> Optional[WebElement]:
    """
    Attempts to open the post by clicking a date or comments element,
    using robust methods and waits for the popup.

    Args:
        post: The WebElement representing the post-container.
        driver: The WebDriver instance.
        actions: The ActionChains instance.
        wait_time: Max seconds to wait for the popup.

    Returns:
        webElement: The WebElement representing the post-container.
    """
    clicked_element_successfully = False
    wait = WebDriverWait(driver, wait_time)

    # --- Try clicking the date element ---
    try:
        # find the entire info section of a post's author

        try:
            driver.implicitly_wait(2)
            post_date_element = post.find_element(By.XPATH, date_enclosing_span_obj["xpath"])

        except TimeoutException as e:
            print(f"{Fore.RED}TimeoutException occurred during open_post:\n{e}{Style.RESET_ALL}")
            return None
        except NoSuchElementException as e:
            print(f"{Fore.RED}NoSuchElementException occurred during open_post:\n{e}{Style.RESET_ALL}")
            try:
                css_selector_info_section = "." + ".".join(poster_info_class.split())
                css_selector_date = "." + ".".join(date_enclosing_span.split())

                info_section = post.find_element(By.CSS_SELECTOR, css_selector_info_section) # find the whole info section
                post_date_element = info_section.find_element(By.CSS_SELECTOR, css_selector_date) # find the date element to click on
            except Exception as e:
                print(f"{Fore.RED}Exception occurred during open_post (attempt two):\n{e}{Style.RESET_ALL}")
                return None
        except Exception as e:
            print(f"{Fore.RED}Exception occurred during open_post:\n{e}{Style.RESET_ALL}")
            return None


        # Using your custom finder for the date element
        if post_date_element:
            try:
                # Basic scroll and click - consider replacing with more robust click logic
                actions.scroll_to_element(post_date_element).perform()
                # Wait for the element to be potentially clickable (basic visibility check)
                wait.until(EC.visibility_of(post_date_element)) # Basic check
                # Hover and scrape the date
                # click on the element
                post_date_element.click()
                clicked_element_successfully = True
            except ElementClickInterceptedException as e:
                 print(f"{Fore.YELLOW}Click on date element intercepted: {e}{Style.RESET_ALL}")
                 # Maybe try JS click as fallback here if needed
                 try:
                     driver.execute_script("arguments[0].click();", post_date_element)
                     clicked_element_successfully = True
                     print("Clicked date element using JavaScript fallback.")
                 except Exception as js_e:
                     print(f"{Fore.RED}JS click fallback also failed: {js_e}{Style.RESET_ALL}")
            except StaleElementReferenceException:
                 print(f"{Fore.RED}Date element became stale before click.{Style.RESET_ALL}")
            except Exception as e:
                 print(f"{Fore.RED}Error clicking date element: {e}{Style.RESET_ALL}")

        else: # IN FUTURE this should try to click the view-more-comments-button - to open the pop-up
            pass


        # --- If a click was attempted/successful, wait for the popup ---
        if clicked_element_successfully:

            def find_popup_window(d: WebDriver) -> Optional[WebElement]:

                try:
                    dialog_window = d.find_element(By.XPATH, pop_up_whole_window_class_obj["xpath"])
                    return dialog_window
                except NoSuchElementException as e:
                    print(f"{Fore.RED}An error occurred in 'find_popup_window'\n{e}{Style.RESET_ALL}")
                except Exception as e2:
                    print(f"{Fore.RED}An error occurred in 'find_popup_window'\n{e2}{Style.RESET_ALL}")
                    print("Resorting to alternative locating approach")


                # --- Dynamically build the CSS selector ---

                # 1. Get the class string from the constant
                class_string = pop_up_whole_window_class

                # 2. Split the class string into individual classes
                individual_classes = class_string.split()

                if not individual_classes:
                    print(
                        f"{Fore.RED}Error: pop_up_whole_window_class constant seems to be empty or invalid.{Style.RESET_ALL}")
                    # Handle the error appropriately, maybe skip finding the element
                    return None
                else:
                    # 3. Create the chained class selector part by prepending '.' to each class
                    #    and joining them without spaces.
                    chained_classes = "".join([f".{cls}" for cls in individual_classes])

                    # 4. Combine the tag, attribute selector, and the chained classes
                    #    Using single quotes for the role value makes defining the f-string easier.
                    dynamic_css_selector = f"div[role='dialog']{chained_classes}"

                    # --- End of dynamic CSS building ---

                try:
                    dialog_window = d.find_element(By.CSS_SELECTOR, dynamic_css_selector)
                    if dialog_window:
                        return dialog_window
                    else:
                        return None
                except NoSuchElementException:
                    return None
                except Exception as e2:
                    print(f"{Fore.RED}An error occurred in 'find_popup_window'\n{e2}{Style.RESET_ALL}")
                    return None

            try:
                # wait.until will call find_popup_window repeatedly until it returns
                # a WebElement or the timeout (wait_time) occurs.
                pop_up_window = wait.until(find_popup_window)
                return pop_up_window
            except TimeoutException:
                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                except Exception:
                    pass # Ignore errors sending escape
                return None
            except Exception:
                 return None

        else:
            # Neither date nor comments button could be clicked successfully
            print(f"{Fore.RED}Failed to click any interactable element to open post details.{Style.RESET_ALL}")
            return None

    except Exception as e:
        print(f"{Fore.RED}Outer error in open_post before click attempt: {e}{Style.RESET_ALL}")
        return None


def find_element_bs4(driver: WebDriver, element: WebElement, exact_class_strings: list[str]) -> Optional[WebElement]:
    """
    Find a nested element by sequentially matching the *exact* string value
    of the 'class' attribute at each level.

    *** WARNING: ***
    This function performs a LITERAL string match on the entire 'class' attribute.
    It treats "class1 class2" as a single entity, NOT as two separate classes.
    This deviates significantly from standard HTML/CSS behavior where spaces
    delimit multiple classes. Use this only if you are certain the target
    elements have a 'class' attribute matching these strings EXACTLY, including
    spaces and order, and potentially no other classes present. This is
    highly unusual for most web development practices, especially frameworks
    that dynamically add classes.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        element (WebElement): The parent WebElement to start searching within.
        exact_class_strings (List[str]): List of strings, where each string is
                                         the exact value expected in the 'class'
                                         attribute of the sequentially nested element.

    Returns:
        Optional[WebElement]: The final WebElement found, or None if the sequence
                              of exact class attribute matches is not found.
    """
    if not driver or not element or not isinstance(exact_class_strings, list):
        print("Error: Invalid parameters for find_element_exact_class_string")
        return None
    if not exact_class_strings:
        print("Error: exact_class_strings list cannot be empty.")
        return None

    try:
        # This JavaScript function iterates through the provided exact_class_strings.
        # For each string, it searches for a *direct descendant* of the current element
        # whose 'class' attribute EXACTLY matches the string.
        js_find_element_exact_match = """
        function findElementByExactClassAttribute(startElement, exactStrings) {
            let currentElement = startElement;

            for (let i = 0; i < exactStrings.length; i++) {
                if (!currentElement) {
                    // If the chain broke in a previous iteration, stop.
                    // console.log(`Chain broke at step ${i}, currentElement is null.`);
                    return null;
                }

                const targetClassString = exactStrings[i];
                // console.log(`Step ${i+1}: Looking for descendant of current element with exact class="${targetClassString}"`);

                // Construct the CSS attribute selector for an EXACT match.
                // Need to escape double quotes within the target string if they were ever present.
                const escapedTargetClassString = targetClassString.replace(/"/g, '\\"');
                const selector = `[class="${escapedTargetClassString}"]`;
                // console.log(`Constructed selector: ${selector}`);

                let foundElement = null;
                try {
                    // Use querySelector to find the first descendant matching the exact attribute value.
                    // Note: querySelector searches *down* the tree from currentElement.
                    foundElement = currentElement.querySelector(selector);
                } catch (e) {
                    // Handle potential errors if the selector is invalid (unlikely here)
                    // console.error(`Error using querySelector with selector "${selector}": ${e}`);
                    return null;
                }


                if (!foundElement) {
                    // console.log(`No descendant found with exact class="${targetClassString}"`);
                    return null; // If no element is found with that exact class attribute, stop.
                }

                // console.log('Found matching element, moving to next step.', foundElement);
                currentElement = foundElement; // Set the found element as the context for the next iteration.
            }

            // If the loop completes, currentElement is the final element in the chain.
            // console.log('Successfully found element chain.');
            return currentElement;
        }

        // arguments[0] is the starting WebElement (element)
        // arguments[1] is the list of exact class strings (exact_class_strings)
        return findElementByExactClassAttribute(arguments[0], arguments[1]);
        """

        # Execute the script
        found_element = driver.execute_script(js_find_element_exact_match, element, exact_class_strings)

        # Check if the script returned a WebElement or null
        if not found_element:
            # print(f"Element sequence not found for: {exact_class_strings}") # Optional debug print
            return None

        # The script returns a DOM element, Selenium wraps it as a WebElement
        return found_element

    except JavascriptException as e:
        print(f"JavaScript error in find_element_exact_class_string: {e}")
        return None
    except WebDriverException as e:
        print(f"WebDriver error in find_element_exact_class_string: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error in find_element_exact_class_string: {e}")
        return None


def scrape_for_post_info(popup_window: WebElement, driver: WebDriver, actions: ActionChains) -> tuple[str, str, str]:
    """

    Args:
        popup_window:
        driver:
        actions:

    Returns:
        username
        post_text
        date

    """
    try:
        # Get username information, if it gets AttributeError it falls back on another place
        try:
            username = popup_window.find_element(By.XPATH, username_popup_obj['xpath']).text.replace("'s post", "")
        except Exception as e:
            username=""
            print(f"{Fore.RED}Error scraping Username {e}{Style.RESET_ALL}")

        # Get post text information
        try:
            post_text = popup_window.find_element(By.XPATH, post_text_obj["xpath"]).text
        except Exception as e:
            post_text = ""
            print(f"{Fore.RED}An Error occurred while scraping text information: {e}{Style.RESET_ALL}")

        date=""
        try: # Get date information
            date_hover_section = popup_window.find_element(By.XPATH, date_popup_obj['xpath'])
            actions.move_to_element(date_hover_section).perform()
            # wait until the date_hover element is ready

            wait = WebDriverWait(driver, 3)

            def get_date(d: WebDriver) -> str:
                try:
                    found_date = ""

                    date_list = d.execute_script(
                        f"return document.getElementsByClassName(\"{js_date_class}\");")  # find the readable date
                    if date_list:
                        # First, try to find an element containing the Unicode character
                        for i, item in enumerate(date_list):
                            if hasattr(item, 'text') and item.text and '\u202f' in item.text:
                                found_date = str(item.text)
                                break

                    return found_date
                except Exception as e2:
                    print(f"{Fore.RED}Error during get_date():\n{e2}{Style.RESET_ALL}")
                    return ""

            date = wait.until(get_date)

        except TimeoutException as e:
            print(f"{Fore.RED}Error while getting date:\n{e}{Style.RESET_ALL}")
        except NoSuchElementException as e:
            print(f"{Fore.RED}Error while getting date:\n{e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error while getting date:\n{e}{Style.RESET_ALL}")

        return username, post_text, date

    except NoSuchElementException as e:
        print(f"{Fore.RED}An Error occurred during scrape_for_post_info\n{e}{Style.RESET_ALL}")
        return "", "", ""
    except Exception as e:
        print(f"{Fore.RED}An Error occurred during scrape_for_post_info\n{e}{Style.RESET_ALL}")
        return "", "", ""


def pop_up_scrape(popup_window: WebElement, driver: WebDriver, actions: ActionChains) -> dict:
    """
    This function scrapes the username, date, and post-text content of any given post.  Next it scrolls to the bottom
    of the comment section. Finally, it scrapes the comments, then it returns a dict.
    Args:
        popup_window:
        driver:
        actions:

    Returns:

    """
    username, post_text, date = "", "", ""
    comment_list = []
    try:

        try: # Scrape the Username, Post Text, and Date
            username, post_text, date = scrape_for_post_info(popup_window, driver, actions)
        except Exception as e:
            print(f"{Fore.RED}An Error occurred while retrieving from scrape_for_post_info\n{e}{Style.RESET_ALL}")

        # --------------------- SCRAPE FOR COMMENTS -------------------------------------------------------------

        comment_container = popup_window.find_element(By.XPATH, comment_pop_up_class_obj["xpath"]) # find the comment container in the popup dialog

        try:
            bottom_loader = popup_window.find_element(By.XPATH, comment_loader_class_obj["xpath"])
        except NoSuchElementException:
            bottom_loader = None

        if bottom_loader:
            def check_loading() -> bool:
                try:
                    if bottom_loader.size['height'] != 0 and bottom_loader.size['width'] != 0:
                        try:
                            children = bottom_loader.find_elements(By.CSS_SELECTOR, "div")
                            if children:
                                return True
                            else:
                                return False
                        except NoSuchElementException as e2:
                            print(f"{Fore.RED}NoSuchElementException in pop_up_scrape:\n{e2}{Style.RESET_ALL}")
                            return False
                        except StaleElementReferenceException:
                            return False
                        except Exception as e2:
                            print(f"{Fore.RED}Error in pop_up_scrape:\n{e2}{Style.RESET_ALL}")
                            return False
                    else:
                        return False
                except StaleElementReferenceException:
                    return False
                except Exception as e2:
                    print(f"{Fore.RED}Error in pop_up_scrape (check loading outer):\n{e2}{Style.RESET_ALL}")

            while check_loading(): # keep forcing the bottom of the comment section until all comments have been loaded
                try:
                    actions.scroll_to_element(bottom_loader).perform()
                except StaleElementReferenceException:
                    break
                except Exception as e:
                    print(f"{Fore.RED}Error in pop_up_scrape (check loading):\n{e}{Style.RESET_ALL}")

        # Find all individual comment elements using the predefined class
        comments = comment_container.find_elements(By.XPATH, individual_comment_class_obj["xpath"])
        if comments:
            for comment in comments:
                try:
                    # Extract the commenter's username
                    poster = comment.find_element(By.XPATH, individual_comment_name_obj["xpath"]).text
                except AttributeError:
                    poster = ""
                except Exception as e:
                    print(f"{Fore.RED}Error while scrapping a comment:\n{e}{Style.RESET_ALL}")
                    poster = ""
                try:
                    # Extract the comment's text content
                    text = comment.find_element(By.XPATH, individual_comment_text_obj["xpath"]).text
                except AttributeError:
                    text = ""
                except Exception as e:
                    print(e)
                    text = ""
                # Store the comment data in our list
                comment_list.append({"username": poster, "comment_text": text})
        else:
            comment_list = []

        actions.send_keys(Keys.ESCAPE).perform()
        return {"username": username, "post_text": post_text, "date": date, "comments": comment_list}

    except NoSuchElementException:
        return {"username": username, "post_text": post_text, "date": date, "comments": comment_list}
    except Exception as e:
        print(f"{Fore.RED}An Error occurred in pop_up_scrape (comment scrape): {e}{Style.RESET_ALL}")
        return {"username": username, "post_text": post_text, "date": date, "comments": comment_list}


def store_post_data(file_path:str, post_data: dict) -> None:
    try:
        # Load existing data if the file exists
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        # Append new post-data
        existing_data.append(post_data)

        # Write back to the file
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=4)
    except Exception as e:
        print(f"Error saving post data to JSON: {e}")


def close_new_tabs_and_keep_original(driver) -> bool:
    """
    Closes any new tabs that might have opened, keeping only the original tab.

    Args:
        driver: The Selenium WebDriver instance.
    """
    original_window_handle = driver.current_window_handle  # Get the handle of the original tab

    # Get all window handles (tabs/windows) currently open
    window_handles = driver.window_handles
    status = False
    # Iterate through all handles
    for handle in window_handles:
        if handle != original_window_handle:  # If it's not the original tab
            driver.switch_to.window(handle)  # Switch to the new tab
            driver.close()                   # Close the new tab
            status = True

    # Switch back to the original tab (important!)
    driver.switch_to.window(original_window_handle)
    return status

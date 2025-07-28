"""
Facebook Group Scraper Main Module

This script orchestrates the Facebook scraping process by initializing the browser,
logging into Facebook, and collecting posts from a specified Facebook group.

The script handles:
1. Driver initialization with anti-detection measures
2. Login to Facebook (using stored cookies or credentials)
3. Scrolling through the group feed to load posts incrementally
4. Extracting data from each post (text, username, date, comments)
5. Storing the collected data in JSON format

The scraper continues running until no new posts are loaded on scroll,
suggesting that it has reached the end of available content.
"""
import sys
from scraper_functions import *
from colorama import Fore, Style
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.ie.webdriver import WebDriver
from constants import *
from selenium.webdriver import ActionChains
import json


with open('settings.json', 'r') as settings_file:
    try:
        settings = json.load(settings_file)[0]
        auto_captcha: bool = settings['auto_captcha']
        cookie_based_login_check: bool = settings['cookie_based_login_check']
        window_size: tuple = tuple(settings['window_size'])
        headless_bool: bool = settings['headless_bool']
        file_path: str = settings['output_file']
        cookie_bool: bool = settings['cookie_login']
        group_link: str = settings['group_scrape_link']
        debug: bool = settings['debug']
    except Exception as e:
        print(f"{Fore.RED}There was an error with the settings file.{Style.RESET_ALL}")
        print(f"{Fore.RED}{e}{Style.RESET_ALL}")
        print(f"\n---------------------------------------------------------------------\n")
        auto_captcha = False
        cookie_based_login_check = False
        window_size = ()
        headless_bool = False
        file_path = "scrape_data.json"
        cookie_login = False
        group_link: str = input("Please enter the URL of the Facebook Group you would like to scrape: ")
        debug = False

if cookie_bool:
    # check that cookies.json contains cookies (is not empty)
    try:
        with(open("storage/cookies.json", "r")) as f:
            cookies = json.load(f)
        if cookies:
            pass
        else:
            cookie_bool = False
    except Exception as e:
        print(e)
        print("Cookies file not found. Using login information instead...")
        cookie_bool = False


driver: WebDriver = driver_init(headless=headless_bool, window_size=window_size)
actions = ActionChains(driver)

try:
    # Log in to Facebook using stored cookies if available
    login(driver, group_link, use_cookies=cookie_bool)
    if debug: print(f"Post-Login Cookies - {driver.get_cookies()}")

    if not cookie_bool:
        time.sleep(1)
        status, image, audio = check_facebook_captcha_links(driver.page_source)
        if status: # if there is a captcha
            if not auto_captcha:
                input("Please solve the captcha manually (Enter to continue)")
            else:
                solved = captcha_interact(driver, debug=debug) # solve and return status of captcha\
                if not solved:
                    print(f"{Fore.RED}CAPTCHA solve failed. Logging in again.{Style.RESET_ALL}")
                    status, image, audio = check_facebook_captcha_links(driver.page_source)
                    if status:
                        solved = captcha_interact(driver, debug=debug)
                        if not solved:
                            print(f"{Fore.RED}Failed to log in.  Try again later.{Style.RESET_ALL}")
                            driver.quit()
                            sys.exit()
                    else:
                        print(f"{Fore.RED}The system was unable to login. Trying again.{Style.RESET_ALL}")
                        login(driver, group_link, use_cookies=False)

                    print(f"{Fore.GREEN}The system will now begin scrapping, however, there may be an error.  If you detect an error stop the system and re-run.{Style.RESET_ALL}")



        driver.get(group_link)
        cookies = driver.get_cookies()
        if debug: print(f"Post-Captcha-Login Cookies - {cookies}")
        with open("storage/cookies.json", "w") as f:
            json.dump(cookies, f)

    # Wait for manual intervention if needed (e.g., to handle unexpected prompts or CAPTCHA)
    scrape_command = input(
        "Press Enter to begin data scraping. Or type 'x' and press Enter to end this process (then you can redo this and try a different approach)."
    )

    if scrape_command == 'x' or scrape_command == 'X':
        print("This process is now ending, try again with a different approach (ex. no cookies login).")
        driver.quit()
        sys.exit()

    # Store the original window handle to ensure we stay on the main window
    original_window_handle = driver.current_window_handle
    time.sleep(1)

# ----------------------------------------------------------------------------------------------------------------------

    # Check for new content and scroll to the page-bottom
    loaded = scroll_and_wait_for_new_posts(driver, 0)

    # set num_posts
    num_posts = 0

    # Main scraping loop: continue scrolling and scraping until no new posts load
    while loaded:
        # Allow time for new posts to render
        time.sleep(2)

        # Get all posts currently in the DOM
        post_class_selector = "." + ".".join(post_class.split())

        # rendered_posts: list[WebElement] = driver.execute_script(
        #     f"return document.querySelectorAll('[class=\"{post_class}\"]')"
        # )
        rendered_posts = get_rendered_posts(driver)

        # Process only newly loaded posts (those beyond our previously processed count)
        wait = WebDriverWait(driver, 10)  # Default wait time (seconds) for conditions

        # Process only newly loaded posts (those beyond our previously processed count)
        if debug: print(f"{Fore.BLUE}Processing posts len: {len(rendered_posts)}{Style.RESET_ALL}")
        for rendered_post in rendered_posts:
            # post_info = scrape_post(driver, rendered_post, actions) # Scrape the posts

            # click for the pop-up
            pop_up_window = open_post(rendered_post, driver, actions)  # Use the specific element

            if pop_up_window:
                try:
                    try: # scrape data from post
                        post_info = pop_up_scrape(pop_up_window, driver, actions)
                        store_post_data(file_path, post_info)
                        print(f"{Fore.BLUE}{post_info}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}{e}{Style.RESET_ALL}")
                    if debug: print(
                        f"Popup window element found: {pop_up_window.tag_name if pop_up_window else 'None'}. Attempting to close with ESCAPE.")
                    # Send ESCAPE key - targeting body is often effective
                    body_element = driver.find_element(By.TAG_NAME, 'body')
                    body_element.send_keys(Keys.ESCAPE)
                    if debug: print("Sent ESCAPE key.")

                    # Wait until the popup window element is no longer attached to the DOM (stale)
                    if debug: print("Waiting for popup to become stale (max 10s)...")
                    wait.until(EC.staleness_of(pop_up_window))
                    if debug: print(f"{Fore.GREEN}Popup element is stale (closed/removed).{Style.RESET_ALL}")

                except TimeoutException:
                    # The popup didn't become stale within the wait time after sending ESCAPE
                    print(
                        f"{Fore.YELLOW}Popup element did not become stale after sending ESCAPE.{Style.RESET_ALL}")
                    # You might want additional fallback logic here if the popup is stuck
                except StaleElementReferenceException:
                    # This is actually GOOD - means the element was already gone before the wait even checked properly.
                    print(f"{Fore.GREEN}Popup element was already stale before explicit wait.{Style.RESET_ALL}")
                except NoSuchElementException:
                    print(f"{Fore.RED}Could not find body element to send ESCAPE key.{Style.RESET_ALL}")
                except Exception as e:
                    # Catch other potential errors during the close attempt
                    print(f"{Fore.RED}Error occurred during popup close/wait: {e}{Style.RESET_ALL}")

            try: # for memory efficieny and cleanness, remove the post after processing
                driver.execute_script("arguments[0].remove();", rendered_post)
            except StaleElementReferenceException:
                if debug: print(
                    f"{Fore.YELLOW}Post was already stale before explicit removal.{Style.RESET_ALL}")
                pass  # Already gone, no action needed
            except Exception as e_remove:
                print(f"{Fore.RED}Error removing post index from DOM: {e_remove}{Style.RESET_ALL}")

        # Check if new content was loaded
        loaded = scroll_and_wait_for_new_posts(driver, 0)

    # Clean up resources
    driver.quit()
    sys.exit()
except KeyboardInterrupt:
    driver.quit()
    sys.exit()

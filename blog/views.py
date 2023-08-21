from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from PIL import Image
import pickle
from selenium import webdriver
import time
from instagrapi import Client
import datetime
from datetime import datetime as dt
import pytz
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from django.contrib.sessions.middleware import SessionMiddleware
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import os
from django.conf import settings
from .models import InstagramPost, InstagramLogin


def homepage(request):
    if 'input_username' in request.session:
        user_name = request.session['input_username']
        recent_posts = InstagramPost.objects.filter(user_name=user_name).order_by('-scheduled_time')[:5]
        other_posts = InstagramPost.objects.all().order_by('-scheduled_time')[:5]
        messages.success(request, 'Stay in our website in order to work automations, it will not work if you close website.')
        return render(request, "index.html", {"recent_posts": recent_posts, "other_posts": other_posts})
    else:
        messages.error(request, "Please Login to Start automations")
        other_posts = InstagramPost.objects.all().order_by('-scheduled_time')[:5]
        return render(request, "index.html", {"recent_posts": [], "other_posts": other_posts})

def schedule_posts(request):
    if 'input_username' in request.session:
        if request.method == "POST":
            username = request.POST.get('username')
            image = request.FILES.get('image')
            caption = request.POST.get('caption')
            scheduled_datetime = request.POST.get('scheduled_datetime')

            # Convert the scheduled_datetime string to a datetime object
            from datetime import datetime
            # scheduled_datetime = datetime.strptime(scheduled_datetime, '%Y-%m-%dT%H:%M')

            # Convert the scheduled_datetime string to a datetime object in UTC
            scheduled_datetime_utc = datetime.strptime(scheduled_datetime, '%Y-%m-%dT%H:%M').replace(tzinfo=pytz.UTC)

            # Fetch the timezone offset from the session
            timezone_offset = request.session.get('timezone_offset')

            # Convert the scheduled_datetime from UTC to the user's local timezone
            local_tz = pytz.timezone(timezone_offset)
            scheduled_datetime_local = scheduled_datetime_utc.astimezone(local_tz)

            # Save the post to the database with the local timezone datetime
            instagram_post = InstagramPost(user_name=username, caption=caption, image=image, scheduled_time=scheduled_datetime_local)
            instagram_post.save()


            messages.success(request, f"Your Post has been submitted. Please Click on Schedule Now below and stay on website.")
            return redirect('schedule_posts')
        else:
            return render(request, "submit-recipe.html")
    else:
        messages.error(request, "Please log in first.")
        return redirect('user_login')


def user_code(request):
    if request.method == 'POST':
        verifi_Code = request.POST.get('verification_code')
        request.session['verification_Code'] = verifi_Code
        return render(request, 'login.html')

def user_login(request):
    if request.method == 'POST':
        input_username = request.POST.get('username')
        input_password = request.POST.get('password')
        timezone = request.POST.get('timezone')
        print("Received login request for user:", input_username)
      
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

        chromedriver_path = str(settings.BASE_DIR/"chromedriver.exe")
        driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        username_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[1]/div/label/input""")
        username_field.send_keys(input_username)

        password_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[2]/div/label/input""")
        password_field.send_keys(input_password)
        password_field.send_keys(Keys.ENTER)
        time.sleep(6)

        print(f"Logged In Successfully as {input_username}")

     
        try:
            two_factor_code_field = driver.find_element_by_name("verificationCode")
            just_code = '123456'
            request.session['verification_Code'] = just_code
            time.sleep(5)

            two_factor_code = request.session['verification_Code']
            two_factor_code_field.send_keys(two_factor_code)
            time.sleep(1)  # Add a short delay for the value to be set
            
            # Submit the 2FA code
            two_factor_code_field.send_keys(Keys.ENTER)
            time.sleep(3)  # Adjust sleep duration as needed
            # Remove the verification_Code session variable
            del request.session['verification_Code']
            print("2FA code entered successfully.")
        except Exception as e:
            print(f"Error Handled is : {str(e)}")
        

        # Save Login to Django session
        request.session['input_username'] = input_username
        request.session['input_password'] = input_password
        request.session['timezone_offset'] = timezone
        print(f"User saved to Session Successfully {input_username}, {input_password}, {timezone}")

        # Save Login to Database
        save_user_db(input_username, input_password)
        print("User saved to Database Successfully")

        #Click Dont Save Now Option (if present)
        try:
            not_element = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/div/div/div/div")
            if not_element:
                not_element.click()
        except Exception as e:
            print("Do not save element not found. Continuing automation.")

        # Turn off Notification (if present)
        try:
            notification_bar = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div")
            if notification_bar:
                not_now = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]").click()
                time.sleep(1)
        except Exception as e:
            print("No notification bar found. Continuing automation.")
        
        
        # Save Login to Django session
        request.session['input_username'] = input_username
        request.session['input_password'] = input_password
        request.session['timezone_offset'] = timezone
        print(f"User saved to Session Successfully {input_username}, {input_password}, {timezone}")
        driver.quit()
        messages.success(request, "Logged In Successfully, Now you can start Automation!")
        return redirect('home')
    else:
        return render(request, "login.html")


def save_session_cookies(driver, filename):
    with open(filename, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)

def load_session_cookies(driver, filename):
    with open(filename, 'rb') as file:
        cookies = pickle.load(file)

        # Fix SameSite attribute for cookies
        for cookie in cookies:
            if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                cookie['sameSite'] = 'Lax'

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except AssertionError as e:
                print("Ignoring cookie with invalid SameSite attribute:", cookie)

def save_user_db(username, password):
    user_creden = InstagramLogin(user_name=username, pass_word=password)
    user_creden.save()


def delete_cookies(request):
    response = HttpResponse("Cookies Deleted")
    response.delete_cookie('jannah_serenity__')  # Replace 'cookie_name' with the name of the cookie you want to delete
    return response

def insta_login(driver, username, password, cookies_filename):

    # Check if the cookie file exists for the given username
    if os.path.exists(cookies_filename):
        try:
            # Try to load session cookies
            load_session_cookies(driver, cookies_filename)
            driver.refresh()
            print("Session loaded successfully. Continuing automation.")
            time.sleep(3)
            return
        except FileNotFoundError:
            print("Session cookies not found. Logging in with credentials.")
            username = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[1]/div/label/input""")
            username.send_keys(username)

            password = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[2]/div/label/input""")
            password.send_keys(password)
            password.send_keys(Keys.ENTER)
            time.sleep(6)

            print(f"Logged In Successfully as {username}")

            # Save Login to Database
            save_user_db(username, password)
            print("User saved to Database Sucessfully")

    
    # Turn off Notification (if present)
    try:
        notification_bar = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div")
        if notification_bar:
            not_now = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]").click()
            time.sleep(1)
    except Exception as e:
        print("No notification bar found. Continuing automation.")

    # After successful login, save the session cookies for future use
    save_session_cookies(driver, cookies_filename)
    print(f"Cookies Saved Successfully!..")

# Keep track of the last processed post time
last_processed = None

def post_insta(request):
    global last_processed  # Declare last_processed as a global variable

    # Fetch the input_username and input_password from the session
    input_username = request.session.get('input_username')
    input_password = request.session.get('input_password')

    # Fetch the timezone offset from the session
    timezone_offset = request.session.get('timezone_offset')
    print("Timezone Offset:", timezone_offset)

    local_tz = pytz.timezone(timezone_offset)

    while True:
        # Get the current time in your timezone
        now = datetime.datetime.now(local_tz)
        current_time = now.strftime('%Y-%m-%d %H:%M:00')
        print("Current time:", current_time)

        # Fetch all posts for the given user
        posts = InstagramPost.objects.filter(user_name=input_username)

        # Loop through each post and check if its scheduled_time has passed
        for i, post in enumerate(posts):
            db_scheduled_time = post.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"The post {post.caption} scheduled time is {db_scheduled_time}")
            if db_scheduled_time == current_time and (last_processed is None or db_scheduled_time > last_processed):
                # Execute the automation for this post
                execute_instagram_automation(i, post, input_username, input_password)
                # Update the last_processed variable to the current post's scheduled time
                last_processed = db_scheduled_time
                break  # Break the loop for the current iteration, we don't need to check other posts right now

        # Sleep for a while before checking again (e.g., every 1 minute)
        time.sleep(60)


    # Redirect the user to the home page (or any other desired page)
    return redirect('home')


def execute_instagram_automation(i, post, input_username, input_password):

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    chromedriver_path = str(settings.BASE_DIR/"chromedriver.exe")
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    
    try:
        driver.get("https://www.instagram.com/")
        time.sleep(3)

        username_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[1]/div/label/input""")
        username_field.send_keys(input_username)

        password_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[2]/div/label/input""")
        password_field.send_keys(input_password)
        password_field.send_keys(Keys.ENTER)
        time.sleep(6)

        print(f"Logged In Successfully as {input_username}")

        #Click Dont Save Now Option
        not_element = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/div/div/div/div")
        not_element.click()

        # Turn off Notification (if present)
        try:
            notification_bar = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div")
            if notification_bar:
                not_now = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]").click()
                time.sleep(1)
        except Exception as e:
            print("No notification bar found. Continuing automation.")
        
        #Create Post
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div/div/div[2]/div[7]/div""").click()
        time.sleep(1)

        #Select Media (Add from Computer)
        select_path = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div/button""").click()
        time.sleep(2)

        # Use pyautogui to interact with the file manager dialog and enter the file path
        image_path = post.image.path  # Use the 'path' attribute of the ImageFieldFile object
        print("Image Path:", image_path)
        pyautogui.write(image_path)
        pyautogui.press("enter")
        time.sleep(1)
        print(f"The Image path is {image_path}")

        #Click Image Original Size
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div[1]/div/div[2]/div/button""").click()
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]""").click()
        time.sleep(1)

        #Click Next
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div[3]/div/div""").click()
        time.sleep(1)
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div[3]/div/div""").click()
        time.sleep(1)

        #Write Caption for Post
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div[1]/p""").click()
        caption = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div[1]/p""")
        time.sleep(1)
        caption.send_keys(post.caption)

        # caption_text = emoji.demojize(post_captions[i])
        # caption.send_keys(caption_text)
        print(f"The Caption is {post.caption}")

        #Dropdown Advance Settings
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[2]/div/div/div/div[5]""").click()
        time.sleep(1)

        #Hide Like Counts:
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[2]/div/div/div/div[5]/div[2]/div/div[1]/div/div[1]/label/span""").click()
        time.sleep(1)

        #Share Post
        driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div[3]/div/div""").click()
        print(f"Post {i + 1} shared successfully..!")
        time.sleep(3)

        # Find the success message and wait for it
        success_message_xpath = "/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/span"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, success_message_xpath))
        )

        # Get the success message element
        success_message_element = driver.find_element(By.XPATH, success_message_xpath)

        # Print the success message
        print("Success message:", success_message_element.text)
    finally:
        # Quit the driver
        driver.quit()


def explore_scheduled(request):
    limitNumber = 20
    limitPosts = InstagramPost.objects.filter().order_by('-scheduled_time')[:limitNumber]
    context = {'title': 'Instagram Automation - Posts Scheduled', 'limitPosts': limitPosts}
    return render(request, 'explore-posts.html', context)

def explore_scheduled_users(request):
    if 'input_username' in request.session:
        user_name = request.session['input_username']
        user_posts = InstagramPost.objects.filter(user_name=user_name).order_by('-scheduled_time')
        context = {'title': 'Instagram Automation - Your Scheduled Posts', 'user_posts': user_posts}
        return render(request, 'explore-user-posts.html', context)
    else:
        return render(request, 'explore-user-posts.html', {'title': 'Instagram Automation - Your Scheduled Posts', 'user_posts': []})
 
def multiple_likes(request):
    if 'input_username' in request.session:
        if request.method == 'POST':
            account_name = request.POST.get('account_name')
            post_number = int(request.POST.get('post_number'))
            print(account_name)

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")

            chromedriver_path = str(settings.BASE_DIR/"chromedriver.exe")
            driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
            driver.get("https://www.instagram.com/")
            time.sleep(3)
            # Rest of your automation code ...
            input_username = request.session.get('input_username')
            input_password = request.session.get('input_password')

            username_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[1]/div/label/input""")
            username_field.send_keys(input_username)

            password_field = driver.find_element_by_xpath("""/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[2]/div/label/input""")
            password_field.send_keys(input_password)
            password_field.send_keys(Keys.ENTER)
            time.sleep(6)

            print(f"Logged In Successfully as {input_username}")

            #Click Dont Save Now Option
            not_element = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/div/div/div/div")
            not_element.click()

            # Turn off Notification (if present)
            try:
                notification_bar = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div")
                if notification_bar:
                    not_now = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]").click()
                    time.sleep(1)
            except Exception as e:
                print("No notification bar found. Continuing automation.")

            try:
                search_btn = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div/div/div[2]/div[2]/span/div/a/div/div[1]/div/div").click()
                print('Search button clicked..')
                time.sleep(1)
            except Exception as e:
                print('Search Button Not Clicked')


            #searched account
            # search_input = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div/div/div[1]/div/div/input")
            search_input = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div[1]/div/input")
            search_input.send_keys(account_name)
            time.sleep(2)
            search_input.send_keys(Keys.RETURN)  # Press the Enter key
            print('Search Input Found')

            #Click on 1st searched Single or List account
            account_paths = ["/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div[2]/div/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div/div/div[2]/div/a[1]"
            ]
            account_path_found = False
            # Iterate through Xpath
            for path in account_paths:
                try:
                    account_path_type = driver.find_element_by_xpath(path)
                    account_path_type.click()
                    print(f"Account path found : {path}")
                    account_path_found = True
                    print(f" {account_name} Account found successfully. Liking the posts..")
                    time.sleep(5)
                    break
                except NoSuchElementException:
                    print(f"Cannot Find {account_name} Account on the Search bar..!")
        

            account_type_xpaths = [
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[3]/article/div/div/div/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[2]/article/div/div/div/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[3]/article/div/div/div[1]/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[2]/article/div/div/div[1]/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[2]/article/div[1]/div/div[1]/div[1]/a",
            "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/div[3]/article/div[1]/div/div[1]/div[1]/a",
            ]

            # Initialize the variable to track whether an account type is found
            account_type_found = False

            # Iterate through the xpaths
            for xpath in account_type_xpaths:
                try:
                    account_type_element = driver.find_element_by_xpath(xpath)
                    account_type_element.click()
                    time.sleep(2)
                    print(f"Account type clicked using xpath: {xpath}")
                    account_type_found = True
                    break  # Exit the loop after finding and clicking on the account type
                except NoSuchElementException:
                    print(f"No xpath found for {account_name} to click the post")

            # Check if an account type was found and clicked
            if account_type_found:
            # Like the post
                like_button = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/div")
                like_button.click()
                print("1st Post Liked")
                time.sleep(1)
            else:
                print(f"Error while finding post type for {account_name}")
                # Handle the error message or action here


            try:
                # Click next post
                next_post = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[1]/div/div/div/button").click()
                time.sleep(1)

                #like 2nd Post
                like = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/div").click()
                print("2nd Post Liked")
                time.sleep(1)
            except Exception as e:
                print(f"No More Posts Except One.")


            #Loop over Liking Multiple Posts
            if post_number >= 3:
                for i in range(post_number-2):
                    try:
                        next_multiple_post = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[1]/div/div/div[2]/button").click()
                        time.sleep(1)
                        like_multiple_posts = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/section[1]/span[1]/div").click()
                        time.sleep(1)
                        print(f"Post {i+3} got liked")
                    except Exception as e:
                        print(f"No more posts to like.")
                        messages.success(request, f"{i + 3} Posts from @{account_name} Got Liked Successfuly")
            else:
                messages.error(request, "You only have lesser than 3 posts.")
            return redirect('home')
        else:
            return render(request, "multiple_likes.html")
    else:
        messages.error(request, "Please log in first.")
        return redirect('user_login')


def contact_us(request):
    if request.method == "POST":
        pass
    else:
        return render(request, "contact.html")

def share_to_followers(request):
    if 'input_username' in request.session:
        user_name = request.session['input_username']
        followers_file_exists = os.path.exists(f"followers/{user_name}_followers.txt")
        context = {
        # ... your other context variables ...
        'followers_file_exists': followers_file_exists
    }
        if request.method == "POST":
            # Handle form submission here
            post_url = request.POST.get('post_url')
            custom_message = request.POST.get('custom_message')
            user_name = request.session['input_username']
            user_password = request.session['input_password']


            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")

            chromedriver_path = str(settings.BASE_DIR/"chromedriver.exe")
            driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

            try:
                driver.get("https://www.instagram.com/")
                time.sleep(3)
                
                username = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[1]/div/label/input")
                username.send_keys(user_name)

                password = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/section/main/article/div[2]/div[1]/div[2]/form/div/div[2]/div/label/input")
                password.send_keys(user_password)
                password.send_keys(Keys.ENTER)
                print("Logging in...")
                time.sleep(4)

                # Click "Not Now" Option
                not_element = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/div/div/div/div")
                not_element.click()
                print("Clicked 'Not Now'")
                time.sleep(3)

                # Turn off Notification (if present)
                try:
                    notification_bar = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div")
                    if notification_bar:
                        not_now = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div[3]/button[2]").click()
                        print("Turned off notifications")
                        time.sleep(2)
                except Exception as e:
                    print("No notification bar found. Continuing automation.")

                # Redirect to the specific post URL

                driver.get(post_url)
                time.sleep(3)

                print(f"Redirected to {post_url}")

                # Share button
                share_btn = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/section/main/div/div[1]/div/div[2]/div/div[3]/div[1]/div[1]/button/div[2]")
                share_btn.click()
                time.sleep(2)
                print("Clicked on share button")

                # Search Input
                search_input = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[1]/div/div[2]/input")
                followers_filename = f'followers/{user_name}_followers.txt'

                with open(followers_filename, 'r') as f:
                    follower_usernames = f.read().splitlines()

                for follower_username in follower_usernames[:15]:

                    # Enter the follower's username
                    search_input.send_keys(follower_username)
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(2)

                    # Check if the "No results found" message is displayed
                    try:
                        get_not_found = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/div/span")
                        # time.sleep(1)
                        for _ in follower_username:
                            search_input.send_keys(Keys.BACK_SPACE)
                            # time.sleep(0.2)
                        time.sleep(1)
                        print("No follower found. Space Cleared..!")
                    except NoSuchElementException:
                        # Look for the clickable elements if not found message
                        try:
                            get_fol_name1 = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/div")
                            get_fol_name2 = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/div[1]")
                            if get_fol_name1:
                                get_fol_name1.click()
                                time.sleep(1)
                            elif get_fol_name2:
                                get_fol_name2.click()
                                time.sleep(1)
                        except NoSuchElementException as e:
                            print(f"Error Handled: {str(e)}")
                    
                    print(f"Searching for {follower_username}")

                # caption input
                time.sleep(1)
                caption_input = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[2]/div/input")
                caption_input.send_keys(custom_message)
                time.sleep(2)
                
                # send_btn
                send_btn = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[2]/div[3]/div").click()
                print("Message Shared Successsfully..!")
                time.sleep(3)
                driver.quit()
            except Exception as e:
                print(f"An error occurred: {e}")
           

            messages.success(request, "Your post has been shared with your 15 followers successfully.")
            return redirect('home')  # Redirect to the desired page
        else:
            return render(request, "share_to_followers.html", context)
    else:
        messages.error(request, "Please log in first.")
        return redirect('user_login')


def download_followers(request):
    try:
        cl = Client()

        user_name = request.session['input_username']
        user_password = request.session['input_password']

        # Function for user login
        cl.login(user_name, user_password)

        followers = cl.user_followers(cl.user_id)

        # Extract usernames from the followers dictionary
        usernames = [follower.username for follower in followers.values()]


        # Save usernames in a text file
        filename = f"followers/{user_name}_followers.txt"
        with open(filename, "w") as file:
            for username in usernames:
                file.write(username + "\n")

        print(f"Usernames saved in {filename}")
        messages.success(request, f"Follower usernames saved in {user_name} Database, Now start sharing your posts")
    except Exception as e:
        print(f"Error Handled : {str(e)}")
        messages.error(request, f"Error Occured while downloading - Error Handled : {str(e)}")

    return redirect('share_to_followers')
    
def file_check(request):
    user_name = request.session['input_username']

    followers_file_exists = os.path.exists(f"followers/{user_name}_followers.txt")

    context = {
        # ... your other context variables ...
        'followers_file_exists': followers_file_exists,
    }

    return render(request, 'share_to_followers.html', context)

def remove_unfollowers(request):
    messages.error(request, "We are working on it and will come soon!")
    return redirect('home')

def follower_interactions(request):
    messages.error(request, "We are working on it and will come soon!")
    return redirect('home')

def story_viewer(request):
    messages.error(request, "We are working on it and will come soon!")
    return redirect('home')
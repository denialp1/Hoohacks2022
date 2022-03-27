# Daniel Park, HooHacks 2022, 3/26/2022
# This python script allows users to use chromedriver to join a zoom
# meeting through their chrome browser, and record meeting attendance incrementaly
# during the meeting (15 seconds) into a text file.

import jwt
import requests
import json
import os
from time import time
from time import sleep

from selenium import webdriver
import selenium=
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.auth import HTTPBasicAuth
from urllib.request import HTTPDigestAuthHandler
from datetime import datetime

API_KEY = "cTy9hSNxQHOYWJRo8OWgug"
API_SECRET = "IViFnWMSgjRrhewUFLFW9i2Sa7fEuTMMjN9V"
meeting = "4067260653"

#Method to generate JWT auth token for Zoom API access
def genToken():
    token = jwt.encode(
        {'iss': API_KEY, 'exp' : time() + 5000},
        API_SECRET,
        algorithm='HS256'
    )
    return token

#Method to get user data with Zoom API
def getUser():
    headers = {'authorization': 'Bearer %s' % genToken(),
               'content-type': 'application/json'}

    r = requests.get('https://api.zoom.us/v2/users/', headers=headers).json()
    return r

#Method to get meeting info with Zoom API
def getMeeting():
    headers = {'authorization': 'Bearer %s' % genToken(),
               'content-type': 'application/json'}

    r = requests.get('https://api.zoom.us/v2/meetings/{meeting}', headers=headers).json()
    return r

#Method to get attendance report with Zoom API, requires premium account
def getAttendance():
    headers = {'authorization': 'Bearer %s' % genToken(),
               'content-type': 'application/json'}
    r = requests.get(
        f'https://api.zoom.us/v2/metrics/meetings/{meeting}/participants', headers=headers)
    print(r.text)

# # Method to auto login, deprecated due to 401 http error
# # def manualLogin(driver):
#     email = getUser()['users'][0]['email']
#     password = "Hoohacks123"

#     try:
#         element = WebDriverWait(driver, 10).until(
#             EC.visibility_of_element_located((By.XPATH, '//*[@id="email"]'))
#         )
#     finally:
#         driver.find_element(by=By.XPATH, value='//*[@id="email"]').send_keys(email)
#         sleep(5)
#         driver.find_element(by=By.XPATH, value='//*[@id="password"]').send_keys(password)
#         sleep(10)
#         driver.find_element(by=By.XPATH, value='//*[@id="login-form"]/div[4]/div/div[1]/button').click()

# # def isLoggedIn(driver):
#     element = driver.find_element(by=By.XPATH, value='//*[@id="login-form"]/div[4]/div/div[1]/button')
#     driver.execute_script("var ele = arguments[0];ele.addEventListener('click', function() {ele.setAttribute('automationTrack','true');});",element)
#     if element.get_attribute("automationTrack"):
#         return True

#Method to find number of participants in Zoom meeting
def getNumParticipants(driver):
    try: #Try to find number on center bottom participants button
        num = driver.find_element(by=By.XPATH, value='//*[@id="foot-bar"]/div[2]/div[2]/button/div/span/span').text
        print("Number of participants" + str(num))
        returnValue = int(num)
    except (ValueError, selenium.common.exceptions.NoSuchElementException): #Case for where bottom bar is hidden
        backupNum = driver.find_element(by=By.XPATH, value='//*[@id="wc-container-right"]/div/div[1]/div[2]/span').text
        backupNum = backupNum.strip('Participants ()') #Strips extra chars from participants menu source
        print("Number of participants" + str(num))
        returnValue = int(backupNum)
    else:
        print("Failed to find participants, using old value")
        returnValue = participantNum
    finally: 
        print("Successfully found num participants")
        return returnValue

#Method to get participant names from list
def getNames(driver, num):
    print("Starting getNames")
    returnList = []

    while(num > 0): #While participants exist
        try: #Try to find participant xpath data with index
            print("Finding name in position" + str(num-1) + "with path" + '//*[@id="participants-list-' + str(num-1) + ']/div/div/span/span[1]')
            name = driver.find_element(by=By.XPATH, value='//*[@id="participants-list-' + str(num-1) + '"]/div/div/span/span[1]').text
            returnList.append(str(name)) #Append found name to returnList
            num -= 1 #Counter down index
        except selenium.common.exceptions.NoSuchElementException:
            print("No such element") #Error message for console
            num -= 1 #Counter down index

    return returnList #Returns returnList to global participants list to update
    
#Method to recursively check for status of in meeting
def inMeetingCheck(driver):
    try: #Presence of button in Zoom meeting detected
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="foot-bar"]/div[2]/div[2]/button/div/span/span'))
        )
    except selenium.common.exceptions.NoSuchElementException:
        print("Not in meeting")
        inMeetingCheck(driver) #Recursively check for element
    else: #Element found, return True
        return True

#Method to wait for user input to avoid http 401
def promptUser():
    prompt = input("Please press enter if entered Zoom meeting: ")
    if prompt == "": #Check for enter key
        return True;
    else: #If typed other, try again
        promptUser()

#Method to send user to given url
def login(driver, url):
    driver.get(url)
    driver.maximize_window()

#Method to record participants at time to txt file
def writeToFile(num, participants):
    f = open('attendanceLog.txt', "a")
    f.write(str(datetime.now()) + ':\n')
    for x in range(num):
        f.write(str(x+1) + '. ' + str(participants[x]) + '\n')
    f.write("\n")
    f.close()

#Method to loop and parse participants list in Zoom meeting
def loopParse(driver):

    #Fetch participant number from xpath
    participantNum = getNumParticipants(driver)

    #Check to see if participant menu open
    if EC.visibility_of_element_located((By.XPATH, '//*[@id="wc-container-right"]/div/div[1]')):
        participants = getNames(driver, participantNum) #Get participants array
        print("Menu open, got names")
    else: #Ff paricipant menu not open
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="foot-bar"]/div[2]/div[2]/button/div/span/span'))
            )
        finally: #Click open participants menu
            driver.find_element(by=By.XPATH, value='//*[@id="foot-bar"]/div[2]/div[2]/button').click()
            print("Clicked menu participants")
            participants = getNames(driver, participantNum) #Get participants array

    #Print scraped names to console
    print("Printing participants list:")
    for x in participants:
        print(x)

    #Record members at time to file    
    writeToFile(participantNum, participants)

    #Sleep for 15 seconds before re-looping for participants check
    sleep(15)
    print("\n")
    loopParse(driver)

def main():
    #Access chrome webdriver
    dirname = os.path.dirname('C:/Users/green/Desktop/py/hoohack/')
    path = os.path.join(dirname, 'chromedriver.exe')
    driver = webdriver.Chrome(path)

    #Enter login page
    url = 'https://zoom.us/signin'

    #Global participants array to update
    global participants
    global participantNum
   
    #If logged in, or in meeting, parse members
    login(driver, url)
    enteredMeeting = promptUser()
    if(enteredMeeting) :
        if inMeetingCheck(driver):
            #Write initial info/start time to file
            f = open('attendanceLog.txt', "w")
            f.write('Start time: ' + str(datetime.now()) + '\n')
            f.write("\n")
            f.close()
            loopParse(driver)

#Run main
main()
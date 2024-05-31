import pandas as pd
import re
from flask import Flask, request, redirect, session, jsonify, Response, g
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_jobs():

    df = pd.read_csv('jobs.csv')
    
    # Convert the DataFrame to a dictionary
    data = df.to_dict(orient='records')
    
    # Return the JSON response
    return jsonify(data)

@app.route('/scrape', methods=['GET'])
def scrape_and_store_jobs():
    try:
        # Initialize Chrome WebDriver
        driver = webdriver.Chrome()

        # Website URL
        url = "https://equitek.ca/connected-most-recent-jobs/"

        # Open URL in browser
        driver.get(url)

        # Wait for the list of jobs to load
        list_jobs = driver.find_elements(By.CLASS_NAME, "listJobs")

        # Initialize an empty list to store job details
        job_data = []

        # Extract jobs company-wise
        for job_list in list_jobs:
            # Get company name and link
            company_logo = job_list.find_element(By.CLASS_NAME, "company-logo").get_attribute("alt")
            company_link = job_list.find_element(By.CSS_SELECTOR, ".text-right a").get_attribute("href")

            # Skip the header rows
            jobs = job_list.find_elements(By.XPATH, ".//li[position()>1]")


            # Initialize a flag to check if it's the first job for the company
            first_job = True

            # Extract job details
            for job in jobs:

                if first_job:
                    # After adding the first job, set the flag to False
                    first_job = False
                else:
                    # Extract job details
                    job_title = job.find_element(By.XPATH, ".//div[contains(@class,'col-md-6')]").text.strip()
                    job_date = job.find_element(By.XPATH, ".//div[contains(@class,'col-md-2')]").text.strip()
                    job_location = job.find_element(By.XPATH, ".//div[contains(@class,'col-md-4')]").text.strip()
                    # Extract the job link
                    job_link = job.find_element(By.XPATH, ".//a").get_attribute("href")

                    # city_province = detect_city_province(job_location)
                    # if len(city_province) < 1:
                    #     city_province = []

                    # Append job details to the list
                    job_data.append({'Company': company_logo,
                                     'Job Title': job_title,
                                     'Job Date': job_date,
                                     'Job Location': job_location,
                                     'Jobs Page': company_link,
                                     'Job Link' : job_link,
                                    #  'city' : city_province[1],
                                    #  'province' : city_province[2]
                                     })

        # Close the browser
        driver.quit()

        # print("Data scraped successfully.")

        # Convert the list of dictionaries to DataFrame
        df = pd.DataFrame(job_data)

        # Save DataFrame to CSV file
        df.to_csv('jobs.csv', index=False)

        # print("Data saved to jobs.csv.")
        return Response(status=200)

    except NoSuchElementException as e:
        print("Failed to fetch data from the website:", e)
        return Response(status=500)

    except Exception as e:
        print("An error occurred:", e)
        return Response(status=500)

def detect_city_province(input_string):

    df = pd.read_csv('cities_provinces.csv')
    # Create a set of city names for quick lookup
    cities_set = set(df['City'].str.lower())
    
    results = []
    
    # for input_string in input_strings:
    city = None
    province_full_name = None
    
    # Tokenize the input string by splitting on non-alphanumeric characters
    tokens = re.split(r'[,\s-]+', input_string.lower())
    
    # Check all possible combinations of consecutive tokens for city names
    for i in range(len(tokens)):
        for j in range(i+1, len(tokens)+1):
            token_combination = ' '.join(tokens[i:j])
            if token_combination in cities_set:
                city = token_combination
                break
        if city:
            break
    
    if city:
        # Find the row in the DataFrame corresponding to the city
        city_row = df[df['City'].str.lower() == city]
        
        if not city_row.empty:
            province_full_name = city_row.iloc[0]['ProvinceFullName']
            results.append((city_row.iloc[0]['City'], province_full_name))
        else:
            results.append((city.capitalize(), 'Province not found'))
    else:
        results.append((None, None))
    
    return results

# Call the method to scrape and store jobs
if __name__ == "__scrapper__":
    scrape_and_store_jobs()
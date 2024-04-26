import requests
from bs4 import BeautifulSoup
import os
import time
import re
import urllib.parse
import json
import getpass

# Constants for credential file
CREDENTIALS_FILE = 'freesound_credentials.json'

# Create a session object to persist cookies
session = requests.Session()

def save_credentials(username, password):
    try:
        with open(CREDENTIALS_FILE, 'w') as file:
            json.dump({'username': username, 'password': password}, file)
        print("Credentials saved successfully.")
    except Exception as e:
        print(f"Error saving credentials: {e}")

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            data = json.load(file)
            return data['username'], data['password']
    except FileNotFoundError:
        print("Credentials file not found. Creating a new one.")
        save_credentials("", "")  # Save an empty username and password
        return "", ""
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None, None

def login_to_freesound():
    saved_username, saved_password = load_credentials()

    if saved_username and saved_password:
        print("Using saved credentials.")
        username = saved_username
        password = saved_password
    else:
        # Prompt the user for their Freesound credentials
        username = getpass.getpass("Enter your Freesound username: ").strip()
        password = getpass.getpass("Enter your Freesound password: ").strip()
        save_credentials(username, password)

    # Start a session to keep cookies
    session = requests.Session()
    
    # Fetch the login page to get the CSRF token
    response = session.get('https://freesound.org')
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    # Create the login payload
    payload = {
        'csrfmiddlewaretoken': csrf_token,
        'username': username,
        'password': password,
    }
    
    headers = {
        'Referer': 'https://freesound.org',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    # Make the POST request to the login action URL
    login_response = session.post('https://freesound.org/home/login/', data=payload, headers=headers)
    
    # Check if login was successful by checking for a redirect to the home page
    if login_response.history:
        print("Logged in successfully.")
        return session  # Return the session if login is successful for further requests
    else:
        print("Login failed, check your username and password.")
        return None  # Return None if login failed
        
def get_search_url(query, page):
    base_url = 'https://freesound.org'
    params = urllib.parse.urlencode({'q': query, 'page': page})
    return f'{base_url}/search/?{params}'

def get_soup(url, session):
    try:
        response = session.get(url)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
    return None

def extract_sound_details(soup):
    sound_elements = soup.find_all('div', class_='bw-search__result')
    sound_details = []

    for sound_elem in sound_elements:
        sound_link = sound_elem.find('a', class_='bw-link--black')
        # Assuming the username is in the same div, just a different 'a' tag or as part of the title attribute
        username_link = sound_elem.find('a', href=re.compile(r'/people/[^/]+/$'))  # regex to match user profile link
        username = username_link.text if username_link else "Unknown"  # if there is no link, default to "Unknown"
        
        if sound_link and 'href' in sound_link.attrs:
            sound_id = sound_link['href'].split('/')[-2]
            sound_name = sound_link.text.strip()
            sound_url = 'https://freesound.org' + sound_link['href']
            
            sound_details.append({
                'id': sound_id,
                'name': sound_name,
                'url': sound_url,
                'username': username  # add the username to the details
            })

    return sound_details

def download_sound(detail, session, dest_folder, query):
    # The path where you want to save the files
    download_path = os.path.join(dest_folder, query)
    os.makedirs(download_path, exist_ok=True)

    # Get the download URL
    download_url = detail['url'] + 'download/'
    response = session.get(download_url, stream=True)
    response.raise_for_status()

    # Extract filename from content-disposition, fall back to the detail's name
    content_disposition = response.headers.get('content-disposition', '')
    filename = ''
    if 'filename=' in content_disposition:
        filename = re.findall('filename="?(.+?)"?$', content_disposition)[0]  # Non-greedy match to prevent capturing trailing characters
    else:
        filename = detail['name'] + '.wav'  # Default to .wav if filename is not found in headers

    # Remove illegal characters and any surrounding whitespace from filename
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename).strip()

    # Ensure the filepath is valid and does not end with a dot or space
    filepath = os.path.join(download_path, filename)
    filepath = filepath.rstrip('. ')  # Remove any trailing dots or spaces which are illegal in Windows filenames

    # If the file already exists, skip the download
    if not os.path.exists(filepath):
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
        print(f'Downloaded: {filename}')
    else:
        print(f"File already exists: {filename}")
        
def process_search(query, session):
    page = 1  # Reset page number to 1 for each new search query
    while True:
        search_url = get_search_url(query, page)
        print(f"Searching: {search_url}")
        soup = get_soup(search_url, session)
        if not soup:
            print("Could not get the search page.")
            break

        sound_details = extract_sound_details(soup)
        if not sound_details:
            print('No more sounds found or end of results.')
            break
        print(f"Found {len(sound_details)} sounds on page {page} for query '{query}'.")
        
        specific_directory = 'DOWNLOADS\\GO\\HERE'

        for detail in sound_details:
            print(f'Downloading sound ID: {detail["id"]} by user: {detail["username"]}')
            download_sound(detail, session, specific_directory, query)

        page += 1
        print(f'Going to page {page}...')
        time.sleep(1)
        
        if input("Do you want to continue to the next page? (y/n): ").strip().lower() != 'y':
            if input("Do you want to search for another sound? (y/n): ").strip().lower() != 'y':
                break
            else:
                query = input('Enter the sound you want to search for: ').strip().replace(' ', '_')
                page = 1  # Reset page number to 1 for the new search query

# Main execution
if __name__ == "__main__":
    session = login_to_freesound()
    if session:
        try:
            search_query = input('Enter the sound you want to search for: ').strip().replace(' ', '_')
            process_search(search_query, session)
        except KeyboardInterrupt:
            print('\nProcess was interrupted by user.')

<!-- GETTING STARTED -->
## Freesound.org Scraper Tool (made with ChatGPT)

Freesound.org has a huge growing library of searchable sounds. 

Upon running this script, it'll prompt the user for a login. 
  - A 'freesound_credentials.json' is created when logging in and automatically logs you in the next time you run the script.

It'll prompt the user to search a sound and it'll proceed to download all the files related to that search page by page.
  - Each page lists 15 sounds per page (assuming there were more than 15 sounds related to your search.)
  - It'll prompt the user at the end of downloading each page if they want to proceed to the next page.

Once the downloads finish, it'll place the sounds in their respective folders based on the keywords used to search the sound.
For example: If the user searches 'space sounds', it'll save those sounds in a folder labeled 'space_sounds'.

This will not download any files that have been previously downloaded, it'll skip any sounds that have already been downloaded.

This script require BeautifulSoup & Requests:
```sh
   pip install requests beautifulsoup4
  ```

Update this to the directory in which you wish to have the sounds saved to: (the double backslashes are necessary)
```sh
  specific_directory = 'DOWNLOADS\\GO\\HERE'
  ```

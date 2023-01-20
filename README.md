<h1 style="text-align: center; font-weight: bold;">Update your Twitter profile picture and/or screen name to current moon phase</h1>

## Demo

!["Demo"](demo.gif "Demo")

## How to use
1. Clone this repository.
2. (Optional) Create a virtual environment.
3. Install dependencies using either `pip install -r requirements.txt` or `conda install --file requirements.txt`
4. Create a file named **.env** and enter your Twitter consumer_key, consumer_secret, access_token_key, and access_token_secret.
    ```
    CONSUMER_KEY = YOUR_CONSUMER_KEY
    CONSUMER_SECRET = YOUR_CONSUMER_SECRET
    ACCESS_TOKEN_KEY = YOUR_ACCESS_TOKEN_KEY
    ACCESS_TOKEN_SECRET = YOUR_ACCESS_TOKEN_SECRET  
    ```
5. Open **twitter_moon.py** and configure the program as desired. For example:
   - Change the `hemisphere` parameter to `north` if you live in the northern hemisphere.
   - Enter your current twitter screen name in the `current_screen_name` parameter if you want your screen name to automatically update based on the current moon phase.
6. Run the program using `python3 twitter_moon.py`
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Response

from api.models.response import APIResponse
from api.models.user import User
from twitter_moon import TwitterMoon

load_dotenv()
app = FastAPI(docs_url=None, redoc_url=None)
twitter_moon = TwitterMoon(
    hemisphere=os.getenv("HEMISPHERE"),
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    save_dir="tmp",
)


@app.get("/ping")
def ping():
    return {
        "message": "pong",
    }


@app.post("/picture", response_model=APIResponse, response_model_exclude_none=True)
def picture(user: User, response: Response):
    resp, code = twitter_moon.update_picture(
        user.access_token, user.access_token_secret
    )
    response.status_code = code
    return resp

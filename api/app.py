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
    save_dir=os.getenv("SAVE_DIR"),
    with_img_in_center=os.getenv("WITH_IMAGE_IN_CENTER").lower() in ("true", "t", "1"),
    img_in_center_path=os.getenv("CENTER_IMAGE_PATH"),
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

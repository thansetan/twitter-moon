import logging
import os
from time import gmtime, strftime, time

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from tweepy import errors

from api.models.response import APIResponse
from api.models.user import Secret, User
from exceptions import TimeoutError
from helper import float_or_none
from twitter_moon import TwitterMoon

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
app = FastAPI(docs_url=None, redoc_url=None)

twitter_moon = TwitterMoon(
    hemisphere=os.getenv("HEMISPHERE"),
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    save_dir=os.getenv("SAVE_DIR"),
    with_img_in_center=os.getenv("WITH_IMAGE_IN_CENTER").lower() in ("true", "t", "1"),
    img_in_center_path=os.getenv("CENTER_IMAGE_PATH"),
    download_timeout=float_or_none(os.getenv("DOWNLOAD_TIMEOUT_SECONDS")),
)


@app.get("/ping")
def ping():
    return APIResponse("pong", success=True)


@app.post("/picture", response_model=APIResponse, response_model_exclude_none=True)
async def picture(user: User, response: Response):
    try:
        msg, moon_id = await twitter_moon.update_picture(
            user.access_token, user.access_token_secret
        )
    except TimeoutError as timeout:
        response.status_code = 408
        return APIResponse(
            f"timed out while trying to download the image ({timeout.duration:.2f} s)",
            errors=[
                f"request to {timeout.__cause__.request.url} timed out after {timeout.duration:.2f} s"
            ],
        )
    except errors.HTTPException as http:
        logging.exception(
            "error while trying to update the profile picture", exc_info=http
        )
        response.status_code = 500
        return APIResponse(
            "there's an error",
            errors=http.api_errors if http.api_errors else [str(http)],
        )
    except Exception as e:
        logging.exception(
            "error while trying to update the profile picture", exc_info=e
        )
        response.status_code = 500
        return APIResponse("there's an error", errors=[str(e)])

    return APIResponse(
        msg,
        data={
            "moon_id": moon_id,
        },
        success=True,
    )


# sometimes the download takes too long, and cron-job.org timeout is 30s so I make a new endpoint
#  to pre-download the image before updating the profile picture
@app.post("/download", response_model=APIResponse, response_model_exclude_none=True)
async def download(secret: Secret, response: Response):
    if secret.key != os.getenv("DOWNLOAD_SECRET_KEY"):
        response.status_code = 403
        return APIResponse("forbidden", errors=["wrong key"])
    try:
        t0 = time()
        logging.info("Download starting...")
        await twitter_moon.get_image()
        t1 = time()
        logging.info(
            "Download finished [took %.2f s]!",
            t1 - t0,
        )
    except TimeoutError as timeout:
        response.status_code = 408
        logging.exception(
            "timed out while trying to download the image", exc_info=timeout
        )
        return APIResponse(
            f"timed out while trying to download the image ({timeout.duration:.2f} s)",
            errors=[
                f"request to {timeout.__cause__.request.url} timed out after {timeout.duration:.2f} s"
            ],
        )
    except Exception as e:
        logging.exception("error while trying to download the image", exc_info=e)
        response.status_code = 500
        return APIResponse(
            "there's an error",
            errors=[str(e)],
        )
    return APIResponse("image downloaded", success=True)

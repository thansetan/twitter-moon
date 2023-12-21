import os
import time
from datetime import datetime
from threading import Lock
from urllib import request

import tweepy
from tweepy import errors

from api.models.response import APIResponse


class TwitterMoon:
    lock = Lock()

    def __init__(
        self,
        hemisphere: str,
        consumer_key: str,
        consumer_secret: str,
        save_dir: str,
    ):
        self.hemisphere = hemisphere  # use "north" if you're on the northern hemisphere, "south" if you're on the southern hemisphere
        self.save_dir = save_dir
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    def __get_picture_id(self) -> str:
        # basically, the id represents the number of hours that have passed since January 1st.
        now = datetime.utcnow()
        id = str(
            round(
                (
                    (int(now.strftime("%j")) * 24 - 23 + int(now.strftime("%H"))) * 60
                    + int(now.strftime("%M"))
                )
                / 60
            )
        ).zfill(4)
        return id

    def __get_image(self) -> str:
        picture_id = self.__get_picture_id()
        os.makedirs(f"{self.save_dir}", exist_ok=True)
        # if the picture already exists, return immediately
        if os.path.isfile(f"{self.save_dir}/moon_{picture_id}.jpg"):
            return f"{self.save_dir}/moon_{picture_id}.jpg"
        url = (
            "https://svs.gsfc.nasa.gov/vis/a000000/a005000/a00504"
            + ("9" if self.hemisphere == "south" else "8")
            + "/frames/730x730_1x1_30p/moon."
            + self.__get_picture_id()
            + ".jpg"
        )
        for file in os.listdir(f"{self.save_dir}"):
            # remove moon pictures that are not the current one
            if file.startswith("moon_") and file[5:9] != picture_id:
                os.remove(f"{self.save_dir}/{file}")
        request.urlretrieve(url, f"{self.save_dir}/moon_{picture_id}.jpg")
        return f"{self.save_dir}/moon_{picture_id}.jpg"

    def __get_moon_emoji(self) -> str:
        def julian(year, month, day):
            if month <= 2:
                year -= 1
                month += 12
            A = year // 100
            B = A // 4
            C = 2 - A + B
            E = int(365.25 * (year + 4716))
            F = int(30.6001 * (month + 1))
            return C + day + E + F - 1524.5

        now = datetime.utcnow()
        jd = julian(now.year, now.month, now.day)
        p = (jd - julian(2000, 1, 6)) % 29.530588853

        moon_phases = {
            0: "🌑",
            1.84566: "🌒",
            5.53588: "🌓",
            9.22831: "🌔",
            12.91963: "🌕",
            16.61069: "🌖",
            20.30228: "🌗",
            23.99361: "🌘",
            27.68493: "🌑",
        }

        closest_key = (
            max(key for key in moon_phases.keys() if key <= (29.530588853 - p))
            if self.hemisphere == "south"
            else max(key for key in moon_phases.keys() if key <= p)
        )
        return moon_phases[closest_key]

    def update_picture(
        self, access_token: str, access_token_secret: str
    ) -> tuple[APIResponse, int]:
        try:
            with self.lock:
                image = self.__get_image()
        except Exception as e:
            return APIResponse("there's an error", [str(e)]), 500
        try:
            auth = self.auth
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            api.update_profile_image(image)
        except errors.HTTPException as e:
            return (
                APIResponse("there's an error", e.response.json()["errors"]),
                e.response.status_code,
            )
        return APIResponse("profile picture updated", success=True), 200

    def update_screen_name(
        self, access_token: str, access_token_secret: str, current_screen_name: str
    ) -> tuple[APIResponse, int]:
        new_name = current_screen_name + " " + self.__get_moon_emoji()
        try:
            auth = self.auth
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            api.update_profile(name=new_name)
        except errors.HTTPException as e:
            return (
                APIResponse("there's an error", e.response.json()["errors"]),
                e.response.status_code,
            )
        return APIResponse("screen name updated", success=True), 200


if __name__ == "__main__":
    import schedule
    from dotenv import load_dotenv

    load_dotenv()
    tm = TwitterMoon(
        hemisphere="south",
        consumer_key=os.getenv("CONSUMER_KEY"),
        consumer_secret=os.getenv("CONSUMER_SECRET"),
        save_dir="tmp",
    )
    print("Starting...")
    # you can use the schedule library, Github Actions, or create a HTTP API and use a tool like cron-job.org to run this script automatically every hour.
    # schedule.every().day.at("00:30").do(
    #     tm.update_screen_name,
    #     current_screen_name="aku",
    #     access_token=os.getenv("ACCESS_TOKEN"),
    #     access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"),
    # )
    schedule.every().hour.at(":30").do(
        tm.update_picture,
        access_token=os.getenv("ACCESS_TOKEN"),
        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"),
    )
    while True:
        schedule.run_pending()
        time.sleep(1)

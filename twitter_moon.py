import os
import time
from datetime import UTC, datetime
from threading import Lock

import requests
import tweepy
from PIL import Image

from exceptions import TimeoutError


class TwitterMoon:
    def __init__(
        self,
        hemisphere: str,
        consumer_key: str,
        consumer_secret: str,
        save_dir: str,
        with_img_in_center: bool = False,
        img_in_center_path: str | None = None,
        download_timeout: float | None = None,
    ):
        self.hemisphere = hemisphere  # use "north" if you're on the northern hemisphere, "south" if you're on the southern hemisphere
        self.save_dir = save_dir
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.with_img_in_center = with_img_in_center
        self.img_in_center_path = img_in_center_path
        self.lock = Lock()
        self.download_timeout = download_timeout

    def __get_picture_id(self) -> str:
        # basically, the id represents the number of hours that have passed since January 1st.
        now = datetime.now(UTC)
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

    async def get_image(
        self,
    ) -> tuple[str, int]:
        moon_id = self.__get_picture_id()
        img_dir = f"{self.save_dir}/moon_{moon_id}.jpg"
        os.makedirs(f"{self.save_dir}", exist_ok=True)
        # if the picture already exists, return immediately
        if os.path.isfile(img_dir):
            return img_dir, moon_id
        url = (
            "https://svs.gsfc.nasa.gov/vis/a000000/a005400/a00541"
            + ("5" if self.hemisphere == "south" else "6")
            + "/frames/730x730_1x1_30p/moon."
            + moon_id
            + ".jpg"
        )
        for file in os.listdir(f"{self.save_dir}"):
            # remove moon pictures that are not the current one
            if file.startswith("moon_") and file[5:9] != moon_id:
                os.remove(f"{self.save_dir}/{file}")
        try:
            t0 = time.time()
            try:
                req = requests.get(url, timeout=self.download_timeout, stream=True)
            except requests.exceptions.SSLError:
                print("SSL error, retrying without verification")
                req = requests.get(
                    url, timeout=self.download_timeout, stream=True, verify=False
                )
            with open(img_dir, "wb") as f:
                for chunk in req.iter_content(chunk_size=100 * 1024):
                    if chunk:
                        f.write(chunk)
        except requests.exceptions.Timeout as timeout:
            raise TimeoutError(time.time() - t0) from timeout
        except Exception:
            raise
        return (
            self.__add_image_in_center(
                img_dir,
                self.img_in_center_path,
                0.8,
            )
            if self.with_img_in_center
            else img_dir
        ), moon_id

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

    def __add_image_in_center(
        self, orig_img_path: str, img_to_add_path: str, img_to_add_scale: float
    ) -> str:
        orig_img = Image.open(orig_img_path)
        img_to_add = Image.open(img_to_add_path)
        img_to_add = img_to_add.resize(
            (
                int(img_to_add.width * img_to_add_scale),
                int(img_to_add.height * img_to_add_scale),
            )
        )
        orig_img.paste(
            img_to_add,
            (
                int((orig_img.width - img_to_add.width) / 2),
                int((orig_img.height - img_to_add.height) / 2),
            ),
            img_to_add,
        )
        orig_img.save(
            f"{orig_img_path}",
        )
        return orig_img_path

    async def update_picture(
        self, access_token: str, access_token_secret: str
    ) -> tuple[str, int]:
        with self.lock:
            image_path, moon_id = await self.get_image()
        try:
            auth = self.auth
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            api.update_profile_image(image_path)
        except Exception as e:
            raise
        return "profile picture updated", moon_id

    def update_screen_name(
        self, access_token: str, access_token_secret: str, current_screen_name: str
    ) -> str:
        new_name = current_screen_name + " " + self.__get_moon_emoji()
        try:
            auth = self.auth
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            api.update_profile(name=new_name)
        except Exception:
            raise
        return "screen name updated"


if __name__ == "__main__":
    import asyncio

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from dotenv import load_dotenv

    load_dotenv()
    tm = TwitterMoon(
        hemisphere="south",
        consumer_key=os.getenv("CONSUMER_KEY"),
        consumer_secret=os.getenv("CONSUMER_SECRET"),
        save_dir="tmp",
    )
    print("Starting...")
    scheduler = AsyncIOScheduler()
    # scheduler.add_job(
    #     func=tm.update_screen_name,
    #     args=[
    #         os.getenv("ACCESS_TOKEN"),
    #         os.getenv("ACCESS_TOKEN_SECRET"),
    #         "aku",
    #     ],
    #     trigger="cron",
    #     minute="31",
    #     hour="*",
    # )
    scheduler.add_job(
        func=tm.update_picture,
        args=[os.getenv("ACCESS_TOKEN"), os.getenv("ACCESS_TOKEN_SECRET")],
        trigger="cron",
        minute="30",
        hour="*",
    )
    scheduler.start()
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()

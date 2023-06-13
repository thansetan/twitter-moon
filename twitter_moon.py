import os
import time
from datetime import datetime
from urllib import request

import schedule

from twitter_auth import auth


class TwitterMoon:
    def __init__(self, hemisphere: str):
        self.hemisphere = hemisphere  # use "north" if you're on the northern hemisphere, "south" if you're on the southern hemisphere

    def __get_picture_id(self):
        # basically, the id represents the number of hours that have passed since January 1st.
        now = datetime.utcnow()
        id = str(int(now.strftime("%j")) * 24 - 23 + int(now.strftime("%H"))).zfill(4)
        print(f"moon id: {id}")
        return id

    def __get_image(self):
        url = (
            "https://svs.gsfc.nasa.gov/vis/a000000/a005000/a00504"
            + ("9" if self.hemisphere == "south" else "8")
            + "/frames/730x730_1x1_30p/moon."
            + self.__get_picture_id()
            + ".jpg"
        )
        os.makedirs("tmp", exist_ok=True)
        request.urlretrieve(url, "tmp/moon.jpg")
        return "tmp/moon.jpg"

    def __get_moon_emoji(self):
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

    def update_picture(self):
        image = self.__get_image()
        api = auth()
        api.update_profile_image(image)
        print("profile picture updated")

    def update_screen_name(self, current_screen_name: str):
        api = auth()
        new_name = current_screen_name + " " + self.__get_moon_emoji()
        api.update_profile(name=new_name)
        print(f"updated!, new name : {new_name}" if os.name != "nt" else "updated!")


if __name__ == "__main__":
    tm = TwitterMoon(hemisphere="south")
    print("Starting...")
    # you can use the schedule library, Github Actions, or create an API and use a tool like cron-job.org to run this script automatically every hour.
    # schedule.every().day.at("00:30").do(tm.update_screen_name, current_screen_name="aku")
    schedule.every().hour.at(":30").do(tm.update_picture)
    while True:
        schedule.run_pending()
        time.sleep(1)

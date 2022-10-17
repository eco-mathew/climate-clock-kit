#!/usr/bin/env python3

#import math
import os
import sys
import time
from datetime import datetime, timezone

import config
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from relativedelta import relativedelta

#GPIO INPUT/OUTPUT settings
import RPi.GPIO as g

STATE = 0

# TODO: Pull these from the network
#JSON = 'https://raw.githubusercontent.com/beautifultrouble/climate-clock-widget/master/src/clock.json'
SECONDS_PER_YEAR = 365.25 * 24 * 3600
CARBON_DEADLINE = datetime.fromisoformat("2029-07-22T16:00:03+00:00")

RENEWABLES = {
    "initial": 11.4,
    "timestamp": datetime.fromisoformat("2022-11-05T00:00:00+00:00"),
    "rate": 2.0428359571070087e-08,
}

relpath = lambda filename: os.path.join(sys.path[0], filename)
hex2color = lambda x: graphics.Color(int(x[-6:-4], 16), int(x[-4:-2], 16), int(x[-2:], 16))

def carbon_deadline():
    return relativedelta(CARBON_DEADLINE, datetime.now(timezone.utc))

def renewables():
    t = (datetime.now(timezone.utc) - RENEWABLES["timestamp"]).total_seconds()
    return RENEWABLES["rate"]*t + RENEWABLES["initial"]


#print climateclock display
def run(options):
    g.setmode(g.BCM)
    g.setup(24, g.IN, pull_up_down=g.PUD_UP)
    g.setup(25, g.IN, pull_up_down=g.PUD_UP)
    
    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()
    
    f1 = graphics.Font()
    f1.LoadFont(relpath("6x13B.bdf"))
    f2 = graphics.Font()
    f2.LoadFont(relpath("6x13.bdf"))
    f3 = graphics.Font()
    f3.LoadFont(relpath("8x13B.bdf"))
    L1 = 13
    L2 = 27
    
    red = hex2color("#ff0000")
    green = hex2color("#00ff00")
    
    alt_yellow = hex2color("#c8890a")
    yellow = hex2color("#ffd919")
    
    while not time.sleep(.05):
        canvas.Clear()

        #deadline
        now = datetime.now(timezone.utc)

        deadline_delta = relativedelta(CARBON_DEADLINE, now)
        years = deadline_delta.years
        rdays = relativedelta(months=deadline_delta.months, days=deadline_delta.days)
        days = ((rdays+now) - now).days
        hours = deadline_delta.hours
        minutes = deadline_delta.minutes
        seconds = deadline_delta.seconds
        cs = deadline_delta.microseconds // 10000

        deadline = [
            [f1, yellow, 1, f"{years:1.0f}"],
            [f1, alt_yellow, 1, "YEAR " if years == 1 else "YRS"],
            [f1, yellow, 1, f"{days:03.0f}"],
            [f1, alt_yellow, 1, "DAY " if days == 1 else "DAYS"],
        ]
        c_string = [
            f"{'STOP AT'}",
            f"{'1.5`C'}",
        ]
        
        #lineline
        r1 = renewables()

        lifeline = [
            [f1, yellow, 0, f"{hours:02.0f}"],
            [f1, yellow, 0, (":", " ")[cs < 50]],
            [f1, yellow, 0, f"{minutes:02.0f}"],
            [f1, yellow, 0, (":", " ")[cs < 50]],
            [f1, yellow, 0, f"{seconds:02.0f}"],
        ]

        if seconds < 55:
            x = 1
            for font, color, space, string in deadline:
                x += space + graphics.DrawText(canvas, font, x, L1, color, string)
            x = 8
            for font, color, space, string in deadline:
                x += space + graphics.DrawText(canvas, font, x, L2, color, string)
            canvas = matrix.SwapOnVSync(canvas)
        else:
            graphics.DrawText(canvas, f3, 5, 15, red, c_string[0])
            graphics.DrawText(canvas, f3, 20, 27, green, c_string[1])
            canvas = matrix.SwapOnVSync(canvas)

            
options = RGBMatrixOptions()
for key, value in vars(config).items():
    if not key.startswith('__'):
        setattr(options, key, value)

if __name__ == "__main__":
    run(options)

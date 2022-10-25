#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime, timezone
import RPi.GPIO as g

import config
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Pulled from dateutil without all the dependencies
from relativedelta import relativedelta

SECONDS_PER_YEAR = 365.25 * 24 * 3600

# Snapshot of API data (the Good Stuff™)
CARBON_DEADLINE_1 = datetime.fromisoformat("2028-01-01T12:00:00+00:00")
RENEWABLES_1 = {
    "initial": 11.4,
    "timestamp": datetime.fromisoformat("2022-01-01T00:00:00+00:00"),
    "rate": 2.0428359571070087e-08,
}


relpath = lambda filename: os.path.join(sys.path[0], filename)
hex2color = lambda x: graphics.Color(
    int(x[-6:-4], 16), int(x[-4:-2], 16), int(x[-2:], 16)
)

clock_display = False

def carbon_deadline_1():
    return relativedelta(CARBON_DEADLINE_1, datetime.now(timezone.utc))

def renewables_1():
    t = (datetime.now(timezone.utc) - RENEWABLES_1["timestamp"]).total_seconds()
    return RENEWABLES_1["rate"] * t + RENEWABLES_1["initial"]

def button_callback(channel):
    global clock_display
    clock_display = not clock_display

def run(options):
    #GPIO setting
    g.setwarnings(False)
    g.setmode(g.BCM)
    g.setup(25, g.IN, pull_up_down=g.PUD_UP)

    g.add_event_detect(25, g.RISING, callback=button_callback, bouncetime=200)

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    f1 = graphics.Font()
    f1.LoadFont(relpath("6x13B.bdf"))
    f2 = graphics.Font()
    f2.LoadFont(relpath("5x8.bdf"))
    f3 = graphics.Font()
    f3.LoadFont(relpath("8x13B.bdf"))
    L1 = 13
    L2 = 27
    L3 = 9

    alt_yellow = hex2color("#b55507")
    yellow = hex2color("#ffd919")

    while not time.sleep(0.05):
        canvas.Clear()

        # Deadline
        now = datetime.now(timezone.utc)

        # Use relativedelta for leap-year awareness
        deadline_delta = relativedelta(CARBON_DEADLINE_1, now)
        years = deadline_delta.years
        # Extract concrete days from the months & days provided by relativedelta
        # @rubberduck: 1. Create a relativedelta object rdays containing Δ months & days
        #              2. Create a concrete time object rdays in the future
        #              3. Create a timedelta object representing that value - now
        #              4. Extract its days
        rdays = relativedelta(months=deadline_delta.months, days=deadline_delta.days)
        days = ((rdays + now) - now).days
        hours = deadline_delta.hours
        minutes = deadline_delta.minutes
        seconds = deadline_delta.seconds
        cs = deadline_delta.microseconds // 10000

        #save current time data
        current_year = now.year
        current_month = now.month
        current_day = now.day
        current_hour = now.hour
        current_minute = now.minute
        current_second = now.second
        current_cs = now.microsecond // 10000

        deadline = [
            [f1, yellow, 1, f"{years:1.0f}"],
            [f2, alt_yellow, 1, "YEAR " if years == 1 else "YRS"],
            [f1, yellow, 1, f"{days:03.0f}"],
            [f2, alt_yellow, 1, "DAY " if days == 1 else "DAYS"],
        ]

        # Lifeline
        lifeline = [
            [f1, yellow, 0, f"{hours:02.0f}"],
            [f1, alt_yellow, 0, (":", " ")[cs < 50]],
            [f1, yellow, 0, f"{minutes:02.0f}"],
            [f1, alt_yellow, 0, (":", " ")[cs < 50]],
            [f1, yellow, 0, f"{seconds:02.0f}"],
        ]

        current_date = [
            [f1, yellow, 1, f"{current_year}"],
            [f1, alt_yellow, 1, ". "],
            [f1, yellow, 1, f"{current_month}"],
            [f1, alt_yellow, 1, ". "],
            [f1, yellow, 1, f"{current_day}"],
            [f1, alt_yellow, 1, "."],
        ]

        current_time = [
            [f3, yellow, 0, f"{current_hour:02.0f}"],
            [f3, alt_yellow, 0, (":", " ")[current_cs < 50]],
            [f3, yellow, 0, f"{current_minute:02.0f}"],
            [f3, alt_yellow, 0, (":", " ")[current_cs < 50]],
            [f3, yellow, 0, f"{current_second:02.0f}"],
        ]   

        if clock_display == False:
            x = 1
            for font, color, space, string in deadline:
                x += space + graphics.DrawText(canvas, font, x, L1, color, string)
            x = 8
            for font, color, space, string in lifeline:
                x += space + graphics.DrawText(canvas, font, x, L2, color, string)
            canvas = matrix.SwapOnVSync(canvas)
        else:
            x = 3
            for font, color, space, string in current_date:
                x += space + graphics.DrawText(canvas, font, x, L3, color, string)
            x = 0
            for font, color, space, string in current_time:
                x += space + graphics.DrawText(canvas, font, x, L2, color, string)
            canvas = matrix.SwapOnVSync(canvas)


options = RGBMatrixOptions()
for key, value in vars(config).items():
    if not key.startswith('__'):
        setattr(options, key, value)


if __name__ == "__main__":
    run(options)

#!/usr/bin/env python3

import json
import os
import sys
import time
from datetime import datetime, timezone

import config
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

import RPi.GPIO as g

TIME_COLOR = '#42e3a2'
TIME_ALT_COLOR = '#0db593'
BUDGET_COLOR = '#ff3838'
BUDGET_ALT_COLOR = '#e60082'
STATE = 0

# TODO: Pull these from the network
JSON = 'https://raw.githubusercontent.com/beautifultrouble/climate-clock-widget/master/src/clock.json'
SECONDS_PER_YEAR = 365.25 * 24 * 3600
START_DATE = datetime(2018, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
START_EMISSIONS_BUDGET = 4.2e11
START_EMISSIONS_YEARLY = 4.2e10


relpath = lambda filename: os.path.join(sys.path[0], filename)
hex2color = lambda x: graphics.Color(int(x[-6:-4], 16), int(x[-4:-2], 16), int(x[-2:], 16))

g.setmode(g.BCM)
g.setup(24, g.IN, pull_up_down=g.PUD_UP)
g.setup(25, g.IN, pull_up_down=g.PUD_UP)

#print climateclock display
def time_and_budget():
    '''
    Return the time (in seconds) until the carbon budget is spent, and the
    remaining carbon budget (in tons).
    '''
    now = datetime.now(timezone.utc)
    emissions_per_second = START_EMISSIONS_YEARLY / SECONDS_PER_YEAR
    emissions_budget_spent = ((now - START_DATE).total_seconds() * emissions_per_second)
    emissions_budget = START_EMISSIONS_BUDGET - emissions_budget_spent
    time_remaining = emissions_budget / emissions_per_second
    
    return time_remaining, emissions_budget


def run(options):
    if g.input(24) == 0:
        STATE = 0
    elif g.input(25) == 0:
        STATE = 1
    
    if STATE == 0:
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        font_file = ['5x8.bdf', '6x13B.bdf', '9x18B.bdf'][options.chain_length - 1]
        font = graphics.Font()
        font.LoadFont(relpath(font_file))

        t_color = hex2color(TIME_COLOR)
        ta_color = hex2color(TIME_ALT_COLOR)
        b_color = hex2color(BUDGET_COLOR)
        ba_color = hex2color(BUDGET_ALT_COLOR)

        while not time.sleep(.1):
            time_remaining, emissions_budget = time_and_budget()

            years, r = divmod(time_remaining, SECONDS_PER_YEAR)
            days, r = divmod(r, 24 * 3600)
            hours, r = divmod(r, 3600)
            minutes, seconds = divmod(r, 60)

            canvas.Clear()

            days = days + 200
            t_strings = [
                f"{years:1.0f}",
                f"{'YR' if years == 1 else 'YRS'}",
                f"{days:3.0f}",
                f"{'DAY' if days == 1 else 'DAYS'}",
                f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}",
            ]
            b_strings = [
                f"{int(emissions_budget):,}"[:12],
                f"{int(emissions_budget):,}"[12:],
                f"TONS",
            ]

            # Place text fragments according to number of screens
            t_colors = [t_color, ta_color, t_color, ta_color, t_color]
            b_colors = [b_color, b_color, ba_color]
            if options.chain_length == 3:
                t_pos = (2, 14), (16, 14), (47, 14), (78, 14), (118, 14)
                b_pos = (2, 28), (111, 28), (145, 28)
            elif options.chain_length == 2:
                t_pos = (2, 14), (10, 14), (31, 14), (51, 14), (78, 14)
                b_pos = (2, 28), (74, 28), (96, 28)
            elif options.chain_length == 1:
                t_pos = (3, 7), (9, 7), (26, 7), (42, 7), (3, 15), (42, 15)
                t_strings.append(f".{int(seconds%1*1000):03d}")
                t_colors.append(t_color) 
                b_pos = (3, 23), (3, 31), (22, 31)
                b_strings[2] = "TONS CO₂"

            for pos, strings, colors in ((t_pos, t_strings, t_colors), (b_pos, b_strings, b_colors)):
                for (x, y), s, c in zip(pos, strings, colors):
                    graphics.DrawText(canvas, font, x, y, c, s)

            canvas = matrix.SwapOnVSync(canvas)

    elif STATE == 1:
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        font_file = ['5x8.bdf', '6x13B.bdf', '9x18B.bdf'][options.chain_length - 1]
        font = graphics.Font()
        font.LoadFont(relpath(font_file))

        y_color = hex2color('#e8f005')

        timezone(timedelta(hours=9))
        today = date(2022, 11, 5)
        
        while not time.sleep(.1):
            canvas.Clear()

            graphics.DrawText(canvas, font, 3, 7, y_color, today.year)

            canvas = matrix.SwapOnVSync(canvas)

            
options = RGBMatrixOptions()
for key, value in vars(config).items():
    if not key.startswith('__'):
        setattr(options, key, value)

run(options)

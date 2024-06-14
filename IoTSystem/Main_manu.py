import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import RPi.GPIO as GPIO
import sys
import os

RST = 0

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()

width = disp.width
height = disp.height
padding = -2
top = padding
bottom = height-padding
x = 0

font = ImageFont.load_default()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 1
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 2

logo_image = Image.open('logo.png').convert('1')
disp.image(logo_image)
disp.display()

time.sleep(3)
disp.clear()
disp.display()

text = [
    "AGREFEED SYSTEM",
    "***************",
    "",
    "Leaf Disease 1",
    "fertilizer analysis 2"
]


y = top + (height - len(text) * 8) // 2

for line in text:
    x = (width - draw.textlength(line, font=font)) // 2
    draw.text((x, y), line, font=font, fill=255)
    y += 8 


disp.image(image)
disp.display()

while True:

    if GPIO.input(17) == GPIO.LOW:
        draw.rectangle((0,0,width,height), outline=0, fill=0) 
        text_width, text_height = draw.textsize("leaf disease", font=font)
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), "You choices :\nleaf disease", font=font, fill=255) 
        disp.image(image)
        disp.display()
        print("Leaf Disease")
        time.sleep(3)
        disp.clear()
        disp.display()
        os.execvp('python3', ['python3', 'LeafDisease.py'])
        
    if GPIO.input(18) == GPIO.LOW:
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        text_width, text_height = draw.textsize("fertilizer analysis", font=font)
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), "You choices :\nfertilizer analysis", font=font, fill=255)
        disp.image(image)
        disp.display()
        print("Fertilizer Analysis")
        time.sleep(3)
        disp.clear()
        disp.display()
        os.execvp('python3', ['python3', 'Fertilizer.py'])

    time.sleep(0.1)

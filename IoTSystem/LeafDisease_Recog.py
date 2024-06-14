from picamera import PiCamera
import time
import boto3
from io import BytesIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import os
import sys
import datetime

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

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://myapp-35c69-default-rtdb.firebaseio.com'
})

def capture_image():
    camera = PiCamera()
    camera.resolution = (1280, 720)
    camera.vflip = True
    camera.contrast = 10
    time.sleep(2)

    stream = BytesIO()
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    camera.close()  
    return stream

def upload_to_s3(stream, bucket_name):
    stream.seek(0)
    s3 = boto3.client('s3')
    key = 'img_{}.jpg'.format(time.strftime("%Y%m%d-%H%M%S"))
    s3.upload_fileobj(stream, bucket_name, key)
    return key

def get_latest_image(bucket_name):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        latest_image = max(response['Contents'], key=lambda x: x['LastModified'])
        return latest_image['Key']
    else:
        return None  # Return None if the bucket is empty

def detect_custom_labels(project_version_arn, bucket_name, region):
    rekognition = boto3.client('rekognition', region_name=region)
    latest_image_key = get_latest_image(bucket_name)
    if latest_image_key:
        response = rekognition.detect_custom_labels(
            ProjectVersionArn=project_version_arn,
            Image={'S3Object': {'Bucket': bucket_name, 'Name': latest_image_key}}
        )
        return response
    else:
        print("No images found in the bucket.")
        return None

if __name__ == "__main__":
    aws_access_key_id = 'your aws access key id'
    aws_secret_access_key = 'your aws access key'
    bucket_name = "your aws s3 bucket name"
    region = "us-east-1"
    project_version_arn = "your aws data model link"

    try:
        logo_image = Image.open('process.png').convert('1')
        disp.image(logo_image)
        disp.display()
        time.sleep(3)

        stream = capture_image()
        key = upload_to_s3(stream, bucket_name)
        print("Image uploaded to S3 bucket:", key)

        response = detect_custom_labels(project_version_arn, bucket_name, region)

        if response is not None and 'CustomLabels' in response:
            for label in response['CustomLabels']:
                draw.rectangle((0,0,width,height), outline=0, fill=0)
                draw.text((x, top), "Disease: {}".format(label['Name']), font=font, fill=255)
                draw.text((x, top + 8), "Confidence: {:.2f}%".format(label['Confidence']), font=font, fill=255)
                # Display the updated image on the OLED screen
                disp.image(image)
                disp.display()
                print("Name:", label['Name'])
                print("Confidence:", label['Confidence'])
                ref = db.reference('leafdisease')
                ref.update({
                    'Disease': label['Name'],
                    'Confidence': label['Confidence'],
                    'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                time.sleep(5) 
                draw.rectangle((0,0,width,height), outline=0, fill=0)
                disp.image(image)
                disp.display()
        else:
            print("No custom labels detected.")
            draw.rectangle((0,0,width,height), outline=0, fill=0)
            draw.text((x, top), "No custom labels", font=font, fill=255)
            draw.text((x, top + 8), "detected.", font=font, fill=255)
            disp.image(image)
            disp.display()
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
      time.sleep(5)
      draw.rectangle((0,0,width,height), outline=0, fill=0)
      disp.image(image)
      disp.display()
      os.system('python3 Mainmanu.py')
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
import os
import datetime
# Initialize OLED display
RST = 0
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()
width = disp.width
height = disp.height
padding = -2
top = padding
x = 0
font = ImageFont.load_default()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Initialize Firebase
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
    camera.close()  # Close the camera to release resources
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
        return None

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
    aws_access_key_id = 'AKIA3FLDYBA7DTC6FQ65'
    aws_secret_access_key = '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'
    bucket_name = "testssdata"
    region = "us-east-1"
    project_version_arn = "arn:aws:rekognition:us-east-1:767397726270:project/firtilizer/version/firtilizer.2024-04-11T21.36.50/1712851610024"

    try:
        # Display the logo image on the OLED screen
        logo_image = Image.open('logo.png').convert('1')
        disp.image(logo_image)
        disp.display()
        
        # Wait for 3 seconds
        time.sleep(3)

        # Capture image
        stream = capture_image()
        key = upload_to_s3(stream, bucket_name)
        print("Image uploaded to S3 bucket:", key)
        # Detect custom labels
        response = detect_custom_labels(project_version_arn, bucket_name, region)

        # Display response on OLED screen
        if response is not None and 'CustomLabels' in response:
            for label in response['CustomLabels']:
                # Clear the OLED screen
                draw.rectangle((0,0,width,height), outline=0, fill=0)

                # Set default text color and background color
                text_color = 255
                background_color = 0

                # Default message
                message = "Disease: {}".format(label['Name'])

                # Determine text color, background color, and message based on label name
                if label['Name'] == 'swap1':
                    text_color = 255  # Yellow
                    background_color = 0  # Black
                    urea_amount = "25 - 80 (KG/ha)"
                    color = "Yellowish Green"
                    message = "Type : Yellowish Green\nDosage: {}\nGives approximate values".format(urea_amount)
                    print("Yellowish Green")
                    print("Confidence:", label['Confidence'])
                elif label['Name'] == 'swap2':
                    text_color = 128  # Intermediate green
                    urea_amount = "15 - 40 (KG/ha)"
                    message = "Type : Intermediate Green\nDosage: {}\nGives approximate values".format(urea_amount)
                    color = "Intermediate Green"
                    print("Intermediate Green")
                    print("Confidence:", label['Confidence'])
                elif label['Name'] == 'swap3':
                    text_color = 0  # Green
                    urea_amount = " 7.5 (KG/ha)"
                    message = "Type : Green\nDosage: {}\nGives approximate values".format(urea_amount)
                    color = "Green"
                    print("Green")
                    print("Confidence:", label['Confidence'])
                elif label['Name'] == 'swap4':
                    text_color = 64  # Intermediate dark green
                    message = "Type : Dark Green\nDosage:\n No Urea wanted"
                    color = "Dark Green"
                    print("Dark Green")
                    urea_amount = ""
                    print("Confidence:", label['Confidence'])
                draw.text((x, top), message, font=font, fill=text_color)
                

                # Display the updated image on the OLED screen
                disp.image(image)
                disp.display()

                # Update Firebase with label information
                if 'swap' in label['Name']:
                    ref = db.reference('Fertilizer')
                    ref.update({
                        'Name': label['Name'],
                        'Confidence': label['Confidence'],
                        'Urea Amount': urea_amount,
                        'color': color,
                        'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                time.sleep(5)  # Display for 5 seconds

                # Clear the OLED screen after displaying for 5 seconds
                draw.rectangle((0,0,width,height), outline=0, fill=background_color)
                disp.image(image)
                disp.display()
        else:
            # No custom labels detected
            print("No custom labels detected.")
            # Display the message on the OLED screen
            draw.rectangle((0,0,width,height), outline=0, fill=0)
            draw.text((x, top), "No custom labels", font=font, fill=255)
            draw.text((x, top + 8), "detected.", font=font, fill=255)
            # Display the message on the OLED screen
            disp.image(image)
            disp.display()
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        # Clear the display after 5 seconds
        time.sleep(5)
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        disp.image(image)
        disp.display()
        # Close the current Python script
        os.system('python3 Mainmanu.py')

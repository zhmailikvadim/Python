import os
import requests
import urllib3
import pyautogui
import time
import keyboard
import img2pdf
from PIL import Image
import os
import PyPDF2
from pypdf import PdfWriter
from PyPDF2 import PdfFileMerger
import PyPDF2
#url = 'https://library.sap-press.com/reader/fromsearch/1d27035d0156639e0e3b9865e536bb61/3/?secret=#/?navigation=page_01'
#our_dir = './download_pdf'
#urllib3.disable_warnings()
#response = requests.get(url,verify=False)

#if response.status_code == 200:
#    file_path = './download_pdf1'
#    with open(file_path, 'wb') as f:
#        f.write(response.content)



repetitions = 650
for i in range(repetitions):
    myScreenshot = pyautogui.screenshot()
    screenshot_path = f"D:/SapPress/img{i:05}.png"
    screenshot_path_jpg = f"D:/SapPress/img{i:05}.jpg"
    pdf_path =  f"D:/SapPress/img{i:05}.pdf"
    pdf_path_all =  f"D:/SapPress/book.pdf"
    myScreenshot.save(os.path.abspath(screenshot_path))   
    myScreenshot.close
    pyautogui.moveTo(148, 623) # координаты первого объекта
    pyautogui.click()
    pyautogui.hotkey('ctrl', 'right')
    time.sleep(2)

    image = Image.open(screenshot_path)
    pdf_bytes = img2pdf.convert(image.filename)
    file = open(pdf_path, "wb")
    file.write(pdf_bytes)
    rgb_im = image.convert('RGB')
    rgb_im.save(screenshot_path_jpg)
    rgb_im.close()
    image.close()
    file.close()
    print("Successfully made pdf file")

source_dir = 'D:/SapPress/'
merger = PyPDF2.PdfMerger()

for item in os.listdir(source_dir):
    if item.endswith('pdf'):
        #print(item)
        merger.append(source_dir + item)

merger.write(source_dir + 'A-Complete.pdf')       
merger.close()







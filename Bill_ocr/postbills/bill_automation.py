from paddleocr import PaddleOCR,draw_ocr
import re 
from PIL import Image
import numpy as np

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def extract_gst_number(word):
    gst_pattern =  r'\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]{2}'
    a = re.findall(gst_pattern,word)
    return a


def extract_dates(text):
    date_pattern1 = r'\d{2}/\d{2}/\d{4}'
    date_pattern2 = r'\d{2}/(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/\d{4}'
    date_pattern3 = r'\d{2}\.\d{2}\.\d{4}'
    date_pattern4 = r'\d{2}\-\d{2}\-\d{4}'
    date_pattern5 = r'\d{1,2}-(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)-\d{2,4}'
    
    
    lst = []
    dates1 = re.findall(date_pattern1, text,flags=re.IGNORECASE)
    dates2 = re.findall(date_pattern2, text,flags=re.IGNORECASE)
    dates3 = re.findall(date_pattern3, text,flags=re.IGNORECASE)
    dates4 = re.findall(date_pattern4, text,flags=re.IGNORECASE)
    dates5 = re.findall(date_pattern5, text,flags=re.IGNORECASE)
    if dates1:
        lst.extend(dates1)
    if dates2:
        lst.extend(dates2)
    if dates3:
        lst.extend(dates3)
    if dates4:
        lst.extend(dates4)
    if dates5:
        lst.append(dates5)
    return lst

def has_number(s):
    for i in s:
        try:
            float(i)
            return False
        except ValueError:
            pass
    return True

def has_common_word(s):
    co = ['gst','invoice','tax','date','code','bill','rate','total','amount','date','copy']
    for i in co:
        if(i.capitalize() in s.capitalize()):
            return False
    return True

def avg_height(boxes):
    avg_height = 0
    n = 0
    for i in boxes:
        n+=1 
        avg_height += abs(i[2][1]-i[1][1])
    return avg_height/n

def overlapping_parmeter(x1,x2,xn1,xn2):
    #assuming threshhold to be 20
    if(x1 == xn1  and x2 == xn2):
        return True
    if(x1<=xn1 and x2>=xn2):
        return True
    if(xn1<=x1  and xn2>=x2):
        return True
    if(x1 > xn1 and x1>=xn2):
        return False
    if(xn1>x1 and xn1>=x2):
        return False
    if(xn1>=x1 and xn1<=x2):
        if(x2-xn1>20):
            return True
        return False
    if(xn2>=x1 and xn2<=x2):
        if(xn2-x1>20):
            return True
        return False
    
def ocr_by_paddleocr(image):
    try:
        print('Starting OCR processing...')

        # Initialize PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        print('PaddleOCR initialized.')

        # Perform OCR on the image
        result = ocr.ocr(image, cls=True)
        print('OCR processing completed.')
    except Exception as e:
        print(f'Error in OCR processing: {e}')
        return None
    print('HELLO')

    result = result[0]
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]

    for i in range(len(txts)):
        print(txts[i])

    lst_gst = []
    lst_date = []
    lst_company_name = []
    lst_Amount = []
    lst_total = []
    lst_tax = []

    average_height = avg_height(boxes)
    target_length = len(txts)/8
    for i in range(int(target_length)):
        temp_box  =   boxes[i]
        temp_text = txts[i]
        high = abs(temp_box[2][1]-temp_box[1][1])
        # print(temp_text,high,average_height)
        if(high>average_height):
            lst_company_name.append(temp_text)

    for i in range(len(txts)):
        if('AMOUNT' in txts[i].upper()  or 'AMT' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])

            lst_Amount.append({txts[i]:tmp_lst})
        if('TOTAL' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])
            lst_total.append({txts[i]:tmp_lst})
        
        if('TAX' in txts[i].upper()):
            tmp_lst = []
            x1,y1,x2,y2 = boxes[i][0][0], boxes[i][0][1],boxes[i][2][0],boxes[i][2][1]
            for j in range(len(txts)):
                xn1,yn1,xn2,yn2 = boxes[j][0][0], boxes[j][0][1],boxes[j][2][0],boxes[j][2][1]
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True  and is_number(txts[j]) == False and yn1>=y2):
                    break
                if(overlapping_parmeter(x1,x2,xn1,xn2) == True and is_number(txts[j]) == True and yn1>=y2):
                    # print(x1,x2,xn1,xn2,txts[i],txts[j])
                    tmp_lst.append(txts[j])
            lst_tax.append({txts[i]:tmp_lst})

            
    lst_company_name = sorted(lst_company_name)[-6:]
    latest_company_name = []

    for i  in lst_company_name:
        if(has_common_word(i) == True and has_number(i) == True):
            latest_company_name.append(i)

    for i in txts:
        a = extract_dates(i)
        if(len(a)>0):
            lst_date.append(a)
        a = extract_gst_number(i)
        if(len(a)>0):
            lst_gst.append(a)
    

    response = {
        'dates': lst_date,
        'gst_numbers': lst_gst,
        'company_names': latest_company_name,
        'amounts': lst_Amount,
        'totals': lst_total,
        'taxes': lst_tax
    }

    print(response)
    return response
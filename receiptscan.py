from imutils.perspective import four_point_transform
import pytesseract
import argparse
import imutils
import cv2
import re
from pytesseract import Output
#The four_point_transform function from the imutils package takes an image and four coordinates that define a quadrilateral (typically the corners of a document or region of interest) and applies a perspective transform to "warp" that region into a top-down, bird's-eye view. This is particularly useful when you need to extract a flat, rectangular representation of an image region—for example, when scanning documents or receipts, where the image might be taken at an angle.

pytesseract.pytesseract.tesseract_cmd = r'../Tesseract-OCR\tesseract.exe'

ap= argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="path to input receipt image")
ap.add_argument("-d", "--debug", type=int, default=-1,
                help="whether or not we are visualizing each step of the pipeline")
args=vars(ap.parse_args())


orig = cv2.imread(args["image"])
if orig is None:
    raise FileNotFoundError("Image not found at provided path.")
image= orig.copy()
image= imutils.resize(image,width=500)
ratio= orig.shape[1]/ float(image.shape[1])

print("Parsed arguments:", args)


#converting to grayscale, bluring slightly, applying edge detection
gray= cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray,(5,5), 0)
edged = cv2.Canny(blurred, 75,200)


if args["debug"]>0:
    cv2.imshow("input", image)
    cv2.imshow("Edged", edged)
    cv2.waitKey(0)

cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)
cnts= imutils.grab_contours(cnts)
cnts= sorted(cnts, key=cv2.contourArea, reverse=True)



receiptCnt = None


for c in cnts:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)


    if len(approx) ==4:
        receiptCnt = approx
        print("found receipt outline")
        break

    

if receiptCnt is None:
     raise Exception(("coudn't find receipt outline."
                        "Try debugging your edge detection and contour steps"))
    

   

if args["debug"] > 0:
        output = image.copy()
        cv2.drawContours(output,[receiptCnt], -1,(0,255,0),2)
        cv2.imshow("Receipt Outline", output)
        cv2.waitKey(0)
        print("receipt outline image shown")


receipt = four_point_transform(orig,receiptCnt.reshape(4,2) * ratio)

#show transformed image
cv2.imshow("Receipt Transform", imutils.resize(receipt, width=500))
cv2.waitKey(0)


options = "--psm 4"
text = pytesseract.image_to_string(
     cv2.cvtColor(receipt, cv2.COLOR_BGR2RGB),
     config=options
)

# show the raw output of the OCR process
print(" raw output:")
print(text)
print("\n")


# price pattern
pricePattern = r'([0-9]+\.[0-9]+)'
print(" price line items:")

for row in text.split("\n"):
	if re.search(pricePattern, row) is not None:
		print(row)
            
        

results = pytesseract.image_to_data(receipt, output_type=Output.DICT)

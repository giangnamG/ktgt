from PIL import Image
import numpy as np
import itertools
import cv2

# ref: https://stackoverflow.com/questions/69674698/issue-related-to-dct-based-steganography

class DiscreteCosineTransform:
    #created the constructor
    def __init__(self):
        self.message = None
        self.numBits = 0

    #utility and helper function for DCT Based Steganography
    #helper function to stich the image back together
    def chunks(self,l,n):
        m = int(n)
        for i in range(0,len(l),m):
            yield l[i:i+m]
    #function to add padding to make the function dividable by 8x8 blocks
    def addPadd(self,img,row,col):
         img = cv2.resize(img,(col+(8-col%8),row+(8-row%8)))
         return img

    #main part 
    #encoding function 
    #applying dct for encoding 
    def DCTEncoder(self,img,secret):
        self.message = str(len(secret)).encode()+b'*'+secret
        #get the size of the image in pixels
        row, col = img.shape[:2]
        if((col/8)*(row/8)<len(secret)):
            print("Error: Message too large to encode in image")
            return False
        if row%8 or col%8:
            img = self.addPadd(img,row,col)
        row,col = img.shape[:2]
        #split image into RGB channels
        hImg,sImg,vImg = cv2.split(img)
        #message to be hid in saturation channel so converted to type float32 for dct function
        #print(bImg.shape)
        sImg = np.float32(sImg)
        #breaking the image into 8x8 blocks
        imgBlocks = [np.round(sImg[j:j+8,i:i+8]-128) for (j,i) in itertools.product(range(0,row,8),range(0,col,8))]
        #print('imgBlocks',imgBlocks[0])
        #blocks are run through dct / apply dct to it
        dctBlocks = [np.round(cv2.dct(ib)) for ib in imgBlocks]
        print('imgBlocks', imgBlocks[0])
        print('dctBlocks', dctBlocks[0])
        #blocks are run through quantization table / obtaining quantized dct coefficients
        quantDCT = dctBlocks
        print('quantDCT', quantDCT[0])
        #set LSB in DC value corresponding bit of message
        messIndex=0
        letterIndex=0
        print(self.message)
        for qb in quantDCT:
            #find LSB in DCT cofficient and replace it with message bit
            bit = (self.message[messIndex] >> (7-letterIndex)) & 1
            DC = qb[0][0]
            DC = (int(DC) & ~31) | (bit * 15)
            qb[0][0] = np.float32(DC)
            letterIndex += 1
            if letterIndex == 8:
                letterIndex = 0
                messIndex += 1
                if messIndex == len(self.message):
                    break
        #writing the stereo image
        #blocks run inversely through quantization table
        #blocks run through inverse DCT
        sImgBlocks = [cv2.idct(B)+128 for B in quantDCT]
        #puts the new image back together
        aImg=[]
        for chunkRowBlocks in self.chunks(sImgBlocks, col/8):
            for rowBlockNum in range(8):
                for block in chunkRowBlocks:
                    aImg.extend(block[rowBlockNum])
        aImg = np.array(aImg).reshape(row, col)
        #converted from type float32
        aImg = np.uint8(aImg)
        #show(sImg)
        return cv2.merge((hImg,aImg,vImg))

    #decoding
    #apply dct for decoding 
    def DCTDecoder(self,img):
        row, col = img.shape[:2]
        messSize = None
        messageBits = []
        buff = 0
        #split the image into RGB channels
        hImg,sImg,vImg = cv2.split(img)
        #message hid in saturation channel so converted to type float32 for dct function
        sImg = np.float32(sImg)
        #break into 8x8 blocks
        imgBlocks = [sImg[j:j+8,i:i+8]-128 for (j,i) in itertools.product(range(0,row,8),range(0,col,8))]
        dctBlocks = [np.round(cv2.dct(ib)) for ib in imgBlocks]
        # the blocks are run through quantization table
        print('imgBlocks',imgBlocks[0])
        print('dctBlocks',dctBlocks[0])
        quantDCT = dctBlocks
        i=0
        flag = 0
        #message is extracted from LSB of DCT coefficients
        for qb in quantDCT:
            if qb[0][0] > 0:
                DC = int((qb[0][0]+7)/16) & 1
            else:
                DC = int((qb[0][0]-7)/16) & 1
            #unpacking of bits of DCT
            buff += DC << (7-i)
            i += 1
            #print(i)
            if i == 8:
                messageBits.append(buff)
                #print(buff,end=' ')
                buff = 0
                i =0
                if messageBits[-1] == 42 and not messSize:
                    try:
                        messSize = int(chr(messageBits[0])+chr(messageBits[1]))
                        print(messSize,'a')
                    except:
                        print('b')
            if len(messageBits) - len(str(messSize)) - 1 == messSize:
                return messageBits
        print("msgbits", messageBits)
        return None


COVER_IMAGE_FILEPATH = 'covers/'
STEGO_IMAGE_FILEPATH = 'stegos/'

class DCTApp:
    def __init__(self, message, cover_image_name, stego_image_name):
        # Allow file type: jpg
        self.image = cv2.imread(f'./{COVER_IMAGE_FILEPATH}/{cover_image_name}',cv2.IMREAD_UNCHANGED)

        self.stego_image_name = stego_image_name

        self.enc_msg = message.encode('utf-8')
        #print(enc_msg)

        self.dct = DiscreteCosineTransform() 
        
    def Encode(self):
        dct_img_encoded = self.dct.DCTEncoder(self.image, self.enc_msg) 
        cv2.imwrite(f'{STEGO_IMAGE_FILEPATH}/{self.stego_image_name}',dct_img_encoded)
        
    def Decode(self):
        eimg = cv2.imread(f'{STEGO_IMAGE_FILEPATH}/{self.stego_image_name}',cv2.IMREAD_UNCHANGED)

        text = self.dct.DCTDecoder(eimg)
        print(text)

        decoded = bytes(text[3:])
        print(decoded)
        return decoded.decode('utf-8')
    
# app = DCTApp(
#     message='Flag{welcome_to_my_challenge}',
#     cover_image_name='1002.jpg',
#     stego_image_name='stego.png')

# app.Encode()
# app.Decode()
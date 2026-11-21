"""Original neutral cloud artwork; not MEGA brand/trademark."""
from PIL import Image,ImageDraw
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.mkdir(parents=True,exist_ok=True)
def draw(size):
    im=Image.new('RGBA',(size,size),(30,49,69,255));d=ImageDraw.Draw(im)
    d.ellipse((size*.22,size*.39,size*.57,size*.74),fill=(245,248,250))
    d.ellipse((size*.38,size*.23,size*.79,size*.75),fill=(245,248,250))
    d.rounded_rectangle((size*.18,size*.53,size*.85,size*.77),radius=size*.07,fill=(245,248,250))
    d.line((size*.3,size*.8,size*.7,size*.8),fill=(105,191,229),width=max(1,size//17))
    return im
for n in (16,32):draw(n).save(p/f'appicon_{n}.png')
draw(256).save(p/'appicon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

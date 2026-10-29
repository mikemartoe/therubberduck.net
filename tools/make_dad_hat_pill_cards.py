"""Dad hat card photos that show the red pill honestly (Mike t1969u/t1970u).
Printful stitches the red pill on the BACK of the dad hat, above the strap (file emb-dadhat-back-redpill on every
variant); it cannot embroider the bill. So each card photo is the real front mockup plus a round inset of the real
Printful back mockup (pill above the strap), labelled "BACK". Gold / Tiffany Blue / Hot Pink backs are tinted from
the real White back mockup with the same multiply recolor used for their fronts (tools/make_dad_hat_special_photos.py);
the pill stitching is masked out of the tint so it stays the real render.
Output: store-img/{duck,signed}-dad-hat-fb_<color>.jpg/.webp (800x800) and duck-dad-hat-fb_black-128.webp."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as nd
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(HERE,'..','store-img')
MP=sys.argv[1] if len(sys.argv)>1 else '/workspace/trd-merch/mockups-printful'
def back(c):
    im=Image.open(f'{MP}/duck-dad-hat_{c}_productonly_embroidery_back_15087.png').convert('RGBA')
    bg=Image.new('RGBA',im.size,(236,233,228,255)); return Image.alpha_composite(bg,im).convert('RGB')   # same studio grey as the fronts
W=np.asarray(back('white')).astype(float); B=np.asarray(back('black')).astype(float)
diff=np.abs(W-B).sum(2)
hat=nd.binary_fill_holes(nd.binary_closing(diff>150,iterations=6))
red=(W[...,0]>120)&(W[...,0]>W[...,1]*1.6)              # the pill's red thread
pillbox=nd.binary_dilation(red,iterations=4)            # pill incl. its white highlight + shadow edge
m=np.clip((diff-120)/180,0,1); m[pillbox]=0
m=np.asarray(Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8))).astype(float)[...,None]/255
crown=np.array([201,202,204.])
T={'gold':(200,145,45),'tiffany':(112,192,186),'hotpink':(222,40,112)}
backs={'black':back('black'),'white':back('white'),'navy':back('navy')}
for k,t in T.items():
    rec=np.clip(W*(np.array(t)/crown),0,255)
    backs[k]=Image.fromarray((W*(1-m)+rec*m).round().astype('uint8'))
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def card(c):
    fr=Image.open(f'{D}/duck-dad-hat-f_{c}.jpg').convert('RGB').resize((800,800))
    S=300; x0,y0=800-S-22,800-S-22
    crop=backs[c].crop((300,330,700,730)).resize((S,S),Image.LANCZOS)   # pill + strap, 1000px mockup
    mask=Image.new('L',(S*4,S*4),0); ImageDraw.Draw(mask).ellipse((0,0,S*4-1,S*4-1),fill=255); mask=mask.resize((S,S),Image.LANCZOS)
    sh=Image.new('L',(800,800),0); ImageDraw.Draw(sh).ellipse((x0-2,y0+6,x0+S+2,y0+S+12),fill=110); sh=sh.filter(ImageFilter.GaussianBlur(10))
    out=Image.composite(Image.new('RGB',(800,800),(0,0,0)),fr,sh)
    ring=Image.new('L',(800,800),0); ImageDraw.Draw(ring).ellipse((x0-6,y0-6,x0+S+6,y0+S+6),fill=255)
    out.paste((240,236,228),(0,0),ring)
    out.paste(crop,(x0,y0),mask)
    d=ImageDraw.Draw(out); f=ImageFont.truetype(FONT,22); txt='BACK'
    tw=d.textlength(txt,font=f); bx=x0+S//2-tw/2-14; by=y0+S-26
    d.rounded_rectangle((bx,by,bx+tw+28,by+36),radius=18,fill=(20,20,20),outline=(240,236,228),width=2)
    d.text((bx+14,by+6),txt,font=f,fill=(240,236,228))
    return out
for c in ['black','white','navy','gold','tiffany','hotpink']:
    im=card(c)
    for pre in ('duck','signed'):
        stem=f'{D}/{pre}-dad-hat-fb_{c}'
        im.save(stem+'.jpg',quality=88,optimize=True,progressive=True); im.save(stem+'.webp',quality=84,method=6)
    if c=='black': im.resize((128,128),Image.LANCZOS).save(f'{D}/duck-dad-hat-fb_black-128.webp',quality=86,method=6)
    print(c)

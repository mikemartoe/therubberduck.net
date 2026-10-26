"""Duck Dad Hat card photos for the special colors (Gold, Tiffany Blue, Hot Pink): Printful has no such blank color, so these are
recolors of the real Printful White mockup (duck-dad-hat_white_product.jpg). The embroidery is protected using the aligned Black
mockup; only the cap fabric is tinted (multiply), so stitching, shading and shadow stay real."""
from PIL import Image, ImageFilter
import numpy as np, sys
from scipy import ndimage as nd
D=sys.argv[1] if len(sys.argv)>1 else __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"..","store-img")
W=np.asarray(Image.open(D+'/duck-dad-hat_white_product.jpg').convert('RGB')).astype(float)
B=np.asarray(Image.open(D+'/duck-dad-hat_black_product.jpg').convert('RGB')).astype(float)
diff=np.abs(W-B).sum(2)
hat=nd.binary_fill_holes(nd.binary_closing(diff>150,iterations=6))
low=(diff<300)&hat
box=np.zeros_like(low); box[170:390,280:550]=True
emb=nd.binary_closing(low&box,iterations=2)
lab,n=nd.label(emb); sizes=nd.sum(emb,lab,range(1,n+1)); emb=np.isin(lab,1+np.where(sizes>200)[0])
emb=nd.binary_erosion(emb,iterations=2)
m=np.clip((diff-120)/180,0,1); bx=box&hat; m[bx]=1.0; m[emb]=0
m=np.asarray(Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8))).astype(float)[...,None]/255
crown=np.array([201,202,204.])
T={'gold':(200,145,45),'tiffany':(112,192,186),'hotpink':(222,40,112)}
for k,t in T.items():
    rec=np.clip(W*(np.array(t)/crown),0,255)
    out=Image.fromarray((W*(1-m)+rec*m).round().astype('uint8'))
    stem=D+'/duck-dad-hat_%s_product'%k
    out.save(stem+'.jpg',quality=88,optimize=True,progressive=True); out.save(stem+'.webp',quality=84,method=6)
    print(stem)

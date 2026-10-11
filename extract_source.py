from zipfile import ZipFile
from lxml import etree
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import json
root=Path('D:/Sunset Website'); out=root/'source-extracted'; out.mkdir(exist_ok=True)
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(root/'SUNSET GELATO.docx') as z:
 x=etree.fromstring(z.read('word/document.xml'))
 lines=[]
 for i,p in enumerate(x.findall('.//w:p',ns)):
  t=''.join(p.xpath('.//w:t/text()',namespaces=ns))
  imgs=p.xpath('.//a:blip/@r:embed',namespaces={**ns,'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'})
  if t or imgs: lines.append({'paragraph':i,'text':t,'images':imgs})
 rel=etree.fromstring(z.read('word/_rels/document.xml.rels'))
 mapping={e.get('Id'):e.get('Target') for e in rel}
 for name in z.namelist():
  if name.startswith('word/media/'):
   (out/Path(name).name).write_bytes(z.read(name))
 (out/'content.json').write_text(json.dumps({'paragraphs':lines,'relationships':mapping},ensure_ascii=False,indent=2),encoding='utf-8')
 for l in lines: print(l)
 ims=[]
 for p in out.iterdir():
  try:
   im=Image.open(p); print(p.name,im.size)
   thumb=ImageOps.contain(im.convert('RGB'),(260,190)); tile=Image.new('RGB',(280,225),'#eeeeee'); tile.paste(thumb,((280-thumb.width)//2,0)); ImageDraw.Draw(tile).text((8,198),p.name,fill='black'); ims.append(tile)
  except Exception: pass
 sheet=Image.new('RGB',(280*3,225*((len(ims)+2)//3)),'white')
 for n,im in enumerate(ims):sheet.paste(im,((n%3)*280,(n//3)*225))
 sheet.save(out/'contact-sheet.jpg')

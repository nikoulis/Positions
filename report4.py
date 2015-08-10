import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
 
doc = Canvas("report4.pdf")
story=[]

logo = "artemis-header-4.jpg"
im = Image(logo, 2.56*inch, 1*inch)
story.append(im)
story.append(Spacer(1, 12))
 
formatted_time = time.ctime()
styles=getSampleStyleSheet()
#styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
ptext = '<font size=12>%s</font>' % formatted_time 
story.append(Paragraph(ptext, styles["Normal"]))
story.append(Spacer(1, 12))

data= [['00', '01', '02', '03', '04'],
       ['10', '11', '12', '13', '14'],
       ['20', '21', '22', '23', '24'],
       ['30', '31', '32', '33', '34']]
t=Table(data,5*[0.4*inch], 4*[0.4*inch])
story.append(t)
story.append(Spacer(1, 12))

f = Frame(inch, inch, 3*inch, 3*inch, showBoundary=1)
f.addFromList(story, doc)
doc.save()

#doc.build(story)

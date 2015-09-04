import pdb

f = open('sectors-US.csv')
fOut = open('sectors-US-new.txt', 'w')
for line in f:
    data = line.strip().split(',')
    numData = len(data)
    for i in range(numData):
    	fOut.write(data[i] + '|')
    fOut.write('\n')
f.close()
fOut.close()

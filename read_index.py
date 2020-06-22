import os
import re
from bs4 import BeautifulSoup
from nltk import PorterStemmer
import argparse
import time
import gc
from bs4.element import Comment
import cProfile


class Indexing:
    ST_key=0

    def tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def doFiltering(self, texts):
        visible_texts = "".join(filter(self.tag_visible, texts))
        #print('****visible text****')
        #print(visible_texts)
        #visible_texts =  re.sub("[()-:!'’—?&@œ.{}×[\]|=;%$â€»_◄►#™©“”`→\"]", " ", visible_texts)  #also deleting numbers
        #visible_texts = re.sub('http|mauth|auth|html|utf|content|apache|openssl|ssl|unix|php|ok|charset|IIS|msgtype|ASP|NET|Mon|Tue|wed|fri|sun|Sat|jan|mar|oct|Feb|GMT|cache|DTD|XHTML|www|com||ORG|TR||server|pragma', '', visible_texts, flags=re.I)
        #visible_texts = re.sub(r'\b\w{1,1}\b', '', visible_texts)
        #print(visible_texts)
        visible_texts = re.compile('[^a-zA-Z ]').sub(' ', visible_texts)
        return visible_texts

    def removeStopWords(self, text):
        inFile = open(os.getcwd() + r"\data" + '\\' + 'stoplist.txt')
        stopWords = [line.strip() for line in inFile]
        text = [word for word in text if word not in stopWords]
        return text

    def doStemming(self,text):
        stemmer = PorterStemmer()
        text = [stemmer.stem(plural) for plural in text]
        return text

    def makeTokens(self,html):
        #parsing
        soup = BeautifulSoup(html, "html.parser")
        texts = soup.findAll(text=True)
        #print('***soup text***')
        #print(texts)

        #filtering
        texts = self.doFiltering(texts)

        #splitting
        splitted = texts.split()
        #print(splitted)

        #lowercasing
        splitted = [j.lower() for j in splitted]

        #removing stop words
        noStop = self.removeStopWords(splitted)

        #stemming
        stemmed = self.doStemming(noStop)
        #print(stemmed)
        return stemmed

    def makeSeperateTerms(self, text):
        #print(text)
        seen = set()
        new = [x for x in text if not (x in seen or seen.add(x))]           #perserving set order and extracting unique
        #seperateTerms.append(new)               #find alternative!
        seperateTerms[self.ST_key] = new
        self.ST_key+=1
        #print(seperateTerms)

    def makeTerms(self):
        terms = set(x for l in seperateTerms.values() for x in l)            #extract unique from list of lists [seperateTerms]
        #print(terms)
        #print(sorted(terms))
        return sorted(terms)

    def writeTerms(self,terms):
        termFile = open('termsids.txt', 'w', encoding="utf-8")
        terms = [(str(i),term) for i,term in enumerate(terms,1)]
        terms = ["\t".join(term) for term in terms]
        terms = "\n".join(terms)
        termFile.write(terms)
        termFile.close()

    def processCorpus(self):
        corpusFile = open('processedCorpus.txt','w', encoding="utf-8")
        docFile = open('docids.txt','w', encoding="utf-8")
        docID = 1
        count=1
        path = "".join([os.getcwd(), '\corpus'])
        tokens =[]
        for filename in os.listdir(path):                 #accessing all documents in corpus folder
            print(count)
            count+=1
            filepath = "".join([path, '\\', filename])
            inFile = open(filepath, errors='ignore')
            text = inFile.read()
            #document = [docID, filename.split(sep='.')[0], text]                #cutting extension
            #corpus.append(document)
            inFile.close()

            #tokenization
            tokens = self.makeTokens(text)

            #write docid and filename to new file
            docFileRow = [str(docID),'\t',filename.split(sep='.')[0],'\n']
            docFileRow = "".join(docFileRow)
            docFile.write(docFileRow)

            #extract all unique items from token and add them in new list, comparing it with new file elements as well
            self.makeSeperateTerms(tokens)

            docID += 1
            #WRITE ONLY TOKENS IN A FILE
            row = "\t".join(tokens)
            #print(row)
            corpusFile.write(row)
            corpusFile.write('\n')
            #corpusFile.close()
            #return
        corpusFile.close()
        docFile.close()

    def getTermsfromFile(self):
        termsFile = open('termsids.txt', 'r',encoding="utf-8")
        rows = [re.split('[\t |\n]', line) for line in termsFile]
        #making a hash of it
        value = 1
        termsFromFile = {}
        for r in rows:
            termsFromFile[r[1]] = value
            value+=1
        rows[:] =[]
        return termsFromFile

    def prcssCorpusFrmFile(self):
        corpusFile = open('processedCorpus.txt', 'r', encoding="utf-8")
        docFile = open('docids.txt', 'r', encoding="utf-8")
        corpus1 = {}
        #HASHMAPS?
        key=1
        for line in corpusFile:
            row = re.split('[\t |\n]', line)
            row.pop()
            row.pop()
            corpus1[key] = row
            key+=1
        corpusFile.close()
        docFile.close()
        return corpus1


class ForwardIndex:
    indxObj = Indexing()

    def getTermID(self,term, terms):
        return terms[term]

    def makeForwardIndex(self):
        terms = self.indxObj.getTermsfromFile()
        corpus = self.indxObj.prcssCorpusFrmFile()

        fwdIndex = open('doc_index.txt', 'w', encoding="utf-8")
        for doc in corpus:
            for term in terms:
                termPos ={}
                pos=1
                termId = self.getTermID(term, terms)
                found = 0
                for token in corpus[doc]:
                    if(token == term):
                        found=1
                        termPos[pos] = pos
                    pos+=1
                if(found):
                    docTerm = [str(doc),'\t',str(termId),'\t']
                    docTerm = "".join(docTerm)
                    fwdIndex.write(docTerm)
                    for pos in termPos:
                        posStr = [str(pos), '\t']
                        posStr = "".join(posStr)
                        fwdIndex.write(posStr)
                    fwdIndex.write('\n')
                termPos.clear()
        fwdIndex.close()


class InvertedIndex:
    indxObj = Indexing()

    def doSomeDeltaEncoding(self, row):
        subrows = len(row)
        if(subrows > 1):
            i = 0
            prev = row[i][0]
            next = row[i+1][0]
            while(i < subrows - 1):
                new = next - prev           #encoding docIDs
                prev = next
                row[i+1][0] = new
                i+=1
                if(i < subrows-1):
                    next = row[i+1][0]

            for subrow in row:
                positions = len(subrow)
                if(positions > 2):
                    j=1
                    prev = subrow[j]
                    next = subrow[j + 1]
                    while(j < positions-1):
                        new = next - prev               # encoding positions
                        prev = next
                        subrow[j + 1] = new
                        j += 1
                        if (j < positions - 1):
                            next = subrow[j + 1]

        return row

    def makeInvertedIndex(self):
        terms = self.indxObj.getTermsfromFile()
        corpus = self.indxObj.prcssCorpusFrmFile()
        invFile = open('term_index.txt', 'w', encoding="utf-8")
        for term in terms:
            row = []
            for doc in corpus:
                found = 0
                termPos = 1
                subRow = []
                for token in corpus[doc]:
                    if(token == term):
                        if(found == 0):
                            subRow.extend([doc,termPos])
                            found = 1
                        elif(found):
                            subRow.append(termPos)
                    termPos+=1
                if(found):
                    row.append(subRow)
            if(len(row)>0):
                #print(row)
                row = self.doSomeDeltaEncoding(row)
                termIDstr = [str(terms[term]),'\t']
                termIDstr = "".join(termIDstr)
                invFile.write(termIDstr)
                for subrow in row:
                    doneOnce = 0
                    pos=1
                    x = len(subrow)-1
                    while pos <= x:
                        if(doneOnce==0):
                            subrowStr = [str(subrow[0]),':',str(subrow[pos]),'\t']
                            subrowStr = "".join(subrowStr)
                            invFile.write(subrowStr)        #\t not working with : and vice versa
                            doneOnce=1
                        elif(doneOnce):                                                     #remaining delta encoding
                            subrowStr = ['0:',str(subrow[pos]),'\t']
                            subrowStr = "".join(subrowStr)
                            invFile.write(subrowStr)
                        pos+=1
                invFile.write('\n')
            row[:] = []
                #print(row)
        invFile.close()
        #print(row)

    def genTextInfo(self):
        trmIndxFile = open('term_index.txt', 'r', encoding="utf-8")
        termInfoFile = open('term_info.txt', 'w', encoding="utf-8")
        offset= 0
        for line in trmIndxFile:
            data = []
            nmbrOfDocs = 0
            data.extend([n for n in line.strip().split('\t')])
            totalOccurence = len(data) - 1
            i=1
            while(i < len(data)):
                if(int(data[i][0]) > 0):
                   nmbrOfDocs+=1
                i+=1
            #writing
            infoStr = [data[0],'\t',str(offset),'\t'+str(totalOccurence),'\t',str(nmbrOfDocs),'\n']
            infoStr = "".join(infoStr)
            termInfoFile.write(infoStr)
            offset += (len(line) + 1)
        trmIndxFile.close()
        termInfoFile.close()


class Reader:
    def reader(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--term')
        parser.add_argument('--doc')
        args = parser.parse_args()

        if(args.term and args.doc):
            self.getBoth(args.term, args.doc)
        elif(args.doc):
            self.getDoc(args.doc)
        elif(args.term):
            self.getTerm(args.term)

    def getDoc(self, docName):
        found=0
        docF = open('docids.txt', 'r')
        for line in docF:
            row = re.split('[\t |\n]', line)
            if(row[1] == docName):
                found = 1
                break
        if(found):
            doctermsF = open("processedCorpus.txt", "r")
            i = 1
            for line in doctermsF:
                if(i == int(row[0])):
                    trms = re.split('[\t |\n]', line)
                    trms.pop()
                    trms.pop()
                    total = len(trms)
                    distinct = len(set(trms))
                    #Printing
                    str1 = ["Listing for Document: ",docName]
                    str1 = "".join(str1)
                    print(str1)
                    str1 = ["DOCID: ",row[0]]
                    str1 = "".join(str1)
                    print(str1)
                    str1 = ["Distinct Terms: ", str(distinct)]
                    str1 = "".join(str1)
                    print(str1)
                    str1 = ["Total Terms: " + str(total)]
                    str1 = "".join(str1)
                    print(str1)
                    break
                i+=1
        else:
            print("No such document in the corpus")

    def getTerm(self, term):
        found=0
        termsF = open('termsids.txt', 'r')
        for line in termsF:
            row = re.split('[\t |\n]', line)
            if(row[1]==term):
                found=1
                break
        if (found):
            terminfoFile = open("term_info.txt", "r")
            for line in terminfoFile:
                newrow = re.split('[\t |\n]', line)
                if (newrow[0] == row[0]):
                    # Printing
                    str = ["Listing for Term: ", term]
                    str = "".join(str)
                    print(str)
                    str = ["TERMID: ", row[0]]
                    str = "".join(str)
                    print(str)
                    str = ["Number of Documents containing Term: " , newrow[3]]
                    str = "".join(str)
                    print(str)
                    str = ["Term Frequency in Corpus: " , newrow[2]]
                    str = "".join(str)
                    print(str)
                    str = ["Inverted List Offset: " , newrow[1]]
                    str = "".join(str)
                    print(str)
                    break
        else:
            print("No such term exists in the corpus")

    def decodeAndFindPos(self, posting, docID):
        index = -1
        i=1
        prev = int(posting[0][0])
        if(prev == int(docID)):
            index = 0
        #decoding postIDs
        while(i < len(posting)):
            if(int(posting[i][0]) > 0):
                posting[i][0] = int(posting[i][0]) + prev
                prev = posting[i][0]
                if (prev == int(docID)):
                    index = i
            elif(int(posting[i][0]) == 0):
                posting[i][0] = prev
            i+=1
        #decode positions
        #print(posting)
        if(index == -1):
            print("Term does not exist in the Document")
        else:
            #print(posting[index])
            count = 1
            temp = index + 1
            positions = []
            positions.append(posting[index][1])
            while(int(posting[index][0]) == posting[temp][0]):
                count+=1
                posting[temp][1] = int(posting[temp][1]) + int(posting[temp-1][1])
                positions.append(str(posting[temp][1]))
                temp+=1
                if(temp == len(posting)):
                    break
            str1 = ['Term frequency in document: ', str(count)]
            str1 = "".join(str1)
            print(str1)
            print('Positions:- ')
            print(positions)
            return

    def getBoth(self,term, docName):
        terminfoF = open('term_info.txt', 'r')
        termIndexF = open('term_index.txt','r')
        docF = open('docids.txt', 'r')
        termsF = open('termsids.txt', 'r')
        found=0
        for line in docF:
            row = re.split('[\t |\n]', line)
            if(row[1] == docName):
                found = 1
                break
        if(found):
            found=0
            for line in termsF:
                newrow = re.split('[\t |\n]', line)
                if (newrow[1] == term):
                    found = 1
                    break
            if (found):
                for line in terminfoF:
                    inforow = re.split('[\t |\n]', line)
                    if(inforow[0] == newrow[0]):
                        posting = termIndexF.readline(termIndexF.seek(int(inforow[1])))
                        posting = posting.split('\t')
                        posting.pop()               #\n
                        str = ['TERMID: ', posting[0]]
                        str = "".join(str)
                        print(str)
                        posting.pop(0)              #termID
                        #separating docs and positions
                        i=0
                        for info in posting:
                            posting[i] = info.split(':')
                            i+=1
                        #getting the positions in the document
                        str = ['DOCID: ',row[0]]
                        str = "".join(str)
                        print(str)
                        self.decodeAndFindPos(posting, row[0])
                        break
            else:
                print("No such term in the corpus")
        else:
            print("No such document in the corpus")
        return

#Main

gc.disable()
start_time = time.time()
#seperateTerms = []
seperateTerms = {}
IndxObj = Indexing()
fwdIndxObj = ForwardIndex()
invIndxObj = InvertedIndex()
#readObj = Reader()


#Indexing
#IndxObj.processCorpus()
#terms = IndxObj.makeTerms()
#IndxObj.writeTerms(terms)


#Forward Indexing
fwdIndxObj.makeForwardIndex()


#Inverted Indexing
#invIndxObj.makeInvertedIndex()
#invIndxObj.genTextInfo()

#readObj.reader()

#fix '\t' issue

#Printing
#for docs in corpus:
#    print(docs)
#for t in seperateTerms:
#    print(t)
#print(terms)
gc.enable()
print('***Finished***')
print("TIME(s) taken: " , (time.time() - start_time))







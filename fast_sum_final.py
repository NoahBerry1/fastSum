#Created By Noah Berry: January 14, 2022
import sys
import time
from sys import exit
import re
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM 
from shutil import Error
from multiprocessing import Pool
import os,binascii

#A note on code style:
#Local variables are in camelcase starting with a lower case charachter i.e. someVariable
#Variables that are used throught the program are written with capitals and underscores i.e. SOME_OTHER_VARIABLE

#This will put the output file in the same directory as the input file 
#The program takes .txt files.

#Run Modes: 
#To run the program with a single thread with a short length summary:
#python3 fast_sum_final.py <your file name here> single short 
#To run the program with a single thread with a medium length summary:
#python3 fast_sum_final.py <your file name here> single medium
#To run the program with a single thread with a long summary:
#python3 fast_sum_final.py <your file name here> single long

#To run the program with a multiple threads with a short length summary:
#python3 fast_sum_final.py <your file name here> multi short 
#To run the program with a multiple threads with a medium length summary:
#python3 fast_sum_final.py <your file name here> multi medium 
#To run the program with a multiple threads with a long summary:
#python3 fast_sum_final.py <your file name here> multi long 


#Assigning start variables. 

#Note down the start time for the program.
START_TIME = time.time()

#Set tokenizer type. 
#More information about the model can be found here. https://huggingface.co/facebook/bart-large-cnn
TOKENIZER = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
MODEL = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
#Run using a single thread or multiple threads: single, multi
THREADING_METHOD=sys.argv[2]
#Set how many processor cores are used on multi mode. 
NUMBER_OF_THREADS=6
#Variable for the summary length: will be either short, medium or long. 
TEXT_SPLIT_LENGTH_INPUT=str(sys.argv[3])
#The thing to be summarized. This must be a .txt file. 
INPUT_FILE_PATH= sys.argv[1]

print("assigned start variables")







#Output the results to a file.  
def outputResults(elements):
  #Get the first part of the file name so if the file name is something.txt this will get 'something'.
  prefex=str(INPUT_FILE_PATH.split('.')[0])
  finalString=""
  #Iterate through the elements to make the text that will be output. 
  for element in elements:
    element=" ".join(element.split())
    finalString=finalString+element+"\n\n"
  #Get the run time.
  finalString=finalString+"--- %s seconds ---" % (time.time() - START_TIME)
  #Add appropriate endings to the file names based on the run method used.  
  if(THREADING_METHOD=="single"):
    textPathOut=prefex+"_shortVersion_single"
  elif(THREADING_METHOD=="multi"):
    textPathOut=prefex+"_shortVersion_multi"
  if(TEXT_SPLIT_LENGTH_INPUT=="long"):
    textPathOut=textPathOut+"_long"
  elif(TEXT_SPLIT_LENGTH_INPUT=="short"):
    textPathOut=textPathOut+"_short"
  elif(TEXT_SPLIT_LENGTH_INPUT=="medium"):
    textPathOut=textPathOut+"_medium"
  else:
    #Something went wrong tell the user and exit. 
    print("Error")
    exit()
  #Make the output file a text file. 
  textPathOut=textPathOut+".txt"
  #Write a new text file with the output in the same directory as the input file. 
  with open(textPathOut, 'w') as f:
      f.write(finalString)
      f.close()
#end of outputResults(elements)





#A method to generate a summary of a paragraph or line. 
def summarizeParagraph(paragraphItem): 
  if(paragraphItem[1]==True):
    paragraphItem=paragraphItem[0]
    tokens = TOKENIZER(paragraphItem, truncation=False, padding="longest", return_tensors="pt")
    summary = MODEL.generate(**tokens)
    returnValue=str(TOKENIZER.decode(summary[0])[7:-4])
    #Prints doing summary for line and then a random hex value just to see progress being made. 
    #This line can be safely commented out if you prefer not to see output. 
    #Sometimes the program can take a long time to run. 
    #So for me it can be nice to see that something is still happening. 
    print(f"doing summary for line{binascii.b2a_hex(os.urandom(15))}TSL:{getTextSplitLength()}")
    return str(returnValue)
  if(paragraphItem[1]==False):
    return paragraphItem[0]
#End of summarizeParagraph 





#Apply the model to the elements using either a single threaded or multi threaded approach
def getElemenetsWithAppropriateApproach(lineList):
  elements=[]
  if(getApproach()=="MULTI_THREAD_APPROACH"):
    p=Pool(NUMBER_OF_THREADS)  
    elements=p.map_async(summarizeParagraph, lineList).get()
    p.close()
  else: #(APPROACH=="SINGLE_THREAD_APPROACH")
    elements=map(summarizeParagraph, lineList)
  return elements
#End of getElemenetsWithAppropriateApproach(lineList). 



#Method to set appropriate paragraph lengths based on the input given from the user. 
def getTextSplitLength():
  if(TEXT_SPLIT_LENGTH_INPUT=="long"):
    return 512
  elif(TEXT_SPLIT_LENGTH_INPUT=="short"):
    return 1024
  elif(TEXT_SPLIT_LENGTH_INPUT=="medium"):
    return 768
  else:
    print("please enter a summary length of long or short")
    exit()
#end of getTextSplitLength(). 




#tldr. Split the text into sentences. 
#Build up paragraphs that are an appropriate length based on input paramaters from those sentences. 
#If some things end up being too long then they are not split into sentences (for instance bulletpoints)
#Bulletpoints or similar are not summarized.
#Things that are made out of normal sentendes do get summarized. 
#These are marked with false or true respectively. 

def getLineList(data):
  #Get the data as a bunch of words 
  maxLength=getTextSplitLength()
  dataList=data.split()
  #Make empty arrays for the paragraphs and the sentences
  paragraphs=[]
  Sentences=[]
  #This will be used multiple times to make new sentences as needed 
  sentence=""
  #Making a counter this counter is used if you reach the end so that the end can be added and used. 
  i=0
  #Go through words and if the words end with end of sentence charachters '!, ., or ?' make into a new sentence. 
  for word in dataList:
    i=i+1
    sentence=sentence+word+" "
    if(word[-1]=="!" or word[-1]=="." or word[-1]=="?"):
      #print(f"appending{sentence}")
      Sentences.append(sentence)
      sentence=""
     #if at the absolute end add to the list of sentences.
    elif(i==len(dataList)-1):
      Sentences.append(sentence)
      sentence=""
  #Empty paragraph.
  paragraph=""
  m=0
  #Go through the sentences. 
  for part in Sentences:
    m=m+1
    #If this paragraph would be an appropriate length add the sentence to the paragraph.
    if(len(paragraph+part)<maxLength):
      paragraph=paragraph+part
      #if it is the end then add what you have and make it a sentence. 
      if(m==len(Sentences)):
        paragraphs.append(paragraph)
        paragraph=""
    #If it would be too long add what you have to the list of existing paragraphsm 
    else:
      paragraphs.append(paragraph)
      #Reset the paragraph so that it is blank.
      paragraph=""
      #add the unadded part to the next paragraph.
      paragraph=paragraph+part
      if(m==len(Sentences)):
        #If at the end take what you have and add this to the list of paragraphs. 
        paragraphs.append(paragraph)
        paragraph=""
  #Set as true or false if it complies with the paragraph length limit.  
  w=0
  for paraItem in paragraphs:
    if len(paraItem)>maxLength:
      paragraphs[w]=[paragraphs[w],False]
    else:
      paragraphs[w]=[paragraphs[w],True]
    w=w+1
  return paragraphs
#end of getLineList()





#Set the approach that will determine what version of the program will run.
#Single for single threaded or multi for multi threaded. 
def getApproach():
  #'single' or 'multi' respectively. 
  if(THREADING_METHOD=="single"):
    return "SINGLE_THREAD_APPROACH"
  elif(THREADING_METHOD=="multi"):
    return "MULTI_THREAD_APPROACH"
  #Notify the user if they did not put single or multi and stop the program. 
  else:
    print("invalid thread method please input 'single' or 'multi'")
    exit()
#end of getApproach()







#Method to read the text from the input file. 
def getDataFromInputFile():
   textFile = open(INPUT_FILE_PATH, "r")
   data = textFile.read()
   textFile.close()
   return data
#End of getDataFromInputFile()









#Inital method that runs when the program starts. 
def main():
  if __name__ =='__main__':#This cannot be removed.   
    print("running")
    outputResults(getElemenetsWithAppropriateApproach(getLineList(getDataFromInputFile())))
    print("done")
#end of main(). 





#'This is where the fun begins.'-Anakin Skywalker.
#Program Start point. 
main()

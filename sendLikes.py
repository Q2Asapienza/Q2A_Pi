#!/usr/bin/python3
from q2a import Q2A,Question,Like
import json

#globals
loginData = json.load(open('./data/login.json', 'r'))
USERNAME = loginData["username"]
PASSWORD = loginData["password"]

if __name__ == "__main__":
    separator = lambda: print("===============")
    
    #creating interface
    q2a = Q2A(USERNAME,PASSWORD)

    #loading session from disk
    print("SESSION FILE... ",end="")
    if(not q2a.sessionLoad()):
        #couldn't load, creating new session
        print("NOT OK\nLOGIN... ",end="")
        q2a.sessionCreate()
        q2a.sessionSave()
    print("OK")
    
    separator()

    #getting questions
    print("GETTING QUESTIONS...")
    questions = q2a.getQuestions()
    print("GOT: " + str(len(questions)) + " questions")
    separator()

    print("GETTING LIKES...")
    likes = q2a.getLikes(questions,True)
    
    like:Like
    likeableLikes = [like for like in likes if like.voted == False]
    print("GOT: "+str(len(likes))+" likes ("+str(len(likeableLikes))+" not liked)")
    separator()

    #sending likes
    print("SENDING LIKES:")
    sent = 0
    for like in likeableLikes:
        result = like.vote()
        if(result == True):
            sent += 1
        else:
            print("NOT ALL LIKES SENT!!!")
            print(result)
            break
    print("LIKES SENT: " + str(sent))
    separator()
    
    print("DONE!")  

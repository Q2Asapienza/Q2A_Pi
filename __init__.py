import pickle
import requests
import cssselect

from lxml import html
from typing import List


class Keys:
    # KEYS FOR DICTIONARIES
    #types
    TYPE            = 'types'
    TYPE_QUESTIONS  = 'questions'
    TYPE_ANSWERS    = 'answers'
    TYPE_COMMENTS   = 'comments'

    #general data
    ID                  = 'id'
    TEXT                = 'text'
    PARENT              = 'parent'
    #edits
    CREATED             = 'created'
    LAST_EDIT           = 'last_edit'

    EDIT        = WHAT  = 'edit'
    TIMESTAMP   = WHEN  = 'timestamp'
    USER        = WHO   = 'user'


    #question data
    TITLE               = 'title'
    #answer data
    BEST                = 'best'
    #like data
    VOTED               = 'voted'

#urls
URL_BASE        = "https://q2a.di.uniroma1.it/"
URL_QUESTIONS   = "https://q2a.di.uniroma1.it/questions/"
URL_LOGIN       = "https://q2a.di.uniroma1.it/login?to="
URL_USER        = "https://q2a.di.uniroma1.it/user"
URL_USERS       = "https://q2a.di.uniroma1.it/users"
URL_ACTIVITIES  = "https://q2a.di.uniroma1.it/activity/"

def Q2ADictToSerializable(q2a_dict:dict):
    q2a_dict = q2a_dict.copy()
    for key,value in q2a_dict.items():
        if key == Keys.PARENT and isinstance(value,dict):
            #removing circular reference
            q2a_dict[key] = value[Keys.ID]
        elif isinstance(value,dict):
            q2a_dict[key] = Q2ADictToSerializable(value)
    
    return q2a_dict

class Q2A:
    LIKE_HEADERS = {
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "origin": URL_BASE,
    }
    #region HIDDEN METHODS
    def __init__(self, username:str = None, password:str = None, session_file:str = None, category = "fondamenti-di-programmazione-19-20"):
        """
        """
        #initializing class attributes
        self.cache  = {}
        self.category = category
        self.username = username
        self.password = password
        self.session = None

        #PREPARING SESSION
        #if there is a session file i load it
        if session_file != None:
            self.sessionLoad(session_file)
        
        #if i don't have a session loaded
        if self.session == None:
            #if i have a password i create it, otherwise i start a blank session
            if password != None:
                self.sessionCreate()
            else:
                self.session = requests.session()
                self.session.headers.update({"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36"})

    #region INNER UTILITIES
    def __getHTMLFromURL(self, url:str, cache=True) -> html.HtmlElement:
        if not cache or url not in self.cache:
            self.cache[url] = html.fromstring(self.session.get(url).text)
        return self.cache[url]

    @staticmethod
    def __getCode(tree:html.HtmlElement) -> str:
        return tree.cssselect('input[name="code"]')[0].attrib['value']

    @staticmethod
    def __userID(userUrl:str) -> str:
        return userUrl.split('/')[-1]

    @staticmethod
    def __getEdit(tree:html.HtmlElement,index:int) -> dict:
        edit_timestamp = tree.cssselect('.updated .value-title')[index].attrib['title']
        edit_who = Q2A.__userID(tree.cssselect('.author a')[index].attrib['href'])
        edit_what = tree.cssselect('.qa-q-view-what, .qa-a-item-what, .qa-c-item-what')[index].text
        return {Keys.USER: edit_who, Keys.TIMESTAMP:edit_timestamp, Keys.EDIT: edit_what}

    @staticmethod
    def __firstEdit(tree:html.HtmlElement) -> dict:
        return Q2A.__getEdit(tree,0)

    @staticmethod
    def __lastEdit(tree:html.HtmlElement) -> dict:
        return Q2A.__getEdit(tree,-1)

    def __questionsFromURL(self,url:str) ->dict:
        tree = self.__getHTMLFromURL(url)
        questions = {}
        pageQuestions = tree.cssselect('.qa-part-q-list .qa-q-list-item')
        for questionDiv in pageQuestions:
            question = {Keys.TYPE:Keys.TYPE_QUESTIONS}
            #getting out data from question
            
            question[Keys.ID]            = questionDiv.attrib['id'][1:]
            question[Keys.TITLE]         = questionDiv.cssselect(".qa-q-item-title span")[0].text
            #getting last edit from what, when, who, not really reliable as it depends on if you use questions or activities
            #who = questionDiv.cssselect('.qa-user-link')[0].attrib['href']
            #question[Keys.LAST_EDI T] = {
            #    'what':questionDiv.cssselect('.qa-q-item-what')[0].text,
            #    'when':questionDiv.cssselect('.qa-q-item-when-data')[0].text,
            #    'who':who[who.rfind('/')]
            #}

            #navigating to question to get inner data
            questionInnerDiv = self.__getHTMLFromURL(URL_BASE+question[Keys.ID]).cssselect('div.question')[0]
            question[Keys.CREATED]       = Q2A.__firstEdit(questionInnerDiv)
            question[Keys.LAST_EDIT]     = Q2A.__lastEdit(questionInnerDiv)
            question[Keys.TEXT]          = questionInnerDiv.cssselect(".entry-content")[0].text_content()

            #appending question to questions
            questions[question[Keys.ID]] = question

        return questions
    #endregion
    #endregion

    #region SESSION management
    def sessionCreate(self):
        """Create a new requests session for comunicating with Q2A.
        Creating a session is necessary for acting as a logged in user
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written
        """

        # Get csrf token
        page = self.session.get(URL_BASE).text
        tree = html.fromstring(page)
        self

        loginPOSTBody = {
            "emailhandle": self.username, 
            "password": self.password,
            "remember": '1',
            "code": Q2A.__getCode(tree),
            "dologin": "Login",
        }

        # Perform login
        self.session.post(URL_LOGIN, data = loginPOSTBody)

        if(not self.logged_in()):
            raise Exception("CAN'T LOGIN")

    #region sessionfile
    def sessionLoad(self, filename = "./data/q2a.ses") -> bool:
        """
        Save current session to a file.
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written

        Return:
        True if the session was loaded and still valid, False otherwise
        """
        try:
            #try to load the last session
            with open(filename,'rb') as sess_file:
                self.session = pickle.load(sess_file)
        except Exception:
            return False

        return self.logged_in()

    def sessionSave(self, filename = "./data/q2a.ses"):
        """
        Save current session to a file.
        WARNING: SAVING CURRENT SESSION TO A FILE IS INSECURE AND AKIN TO SAVING PASSWORD TO A TEXT FILE, BE CAREFUL!

        Params:
        filename(str): the path of the file in wich the session will be written
        """
        with open(filename, 'wb') as sess_file:
            pickle.dump(self.session, sess_file)
    #endregion

    #endregion

    #region PROFILE INFO
    def logged_in(self):
        return self.username in self.session.get(URL_USER).url

    def profileInfo(self):
        pass
    #endregion

    #region Utility for user
    def getQuestions(self, category:str = None) -> dict:
        """
        Get questions from all the pages.

        Params:
        category(str): The id of the category

        Return:
        A list containing the Questions found
        """
        page = 1
        questions = {}
        while(True):
            added = self.getQuestionsFromPage(category=category,page=page)
            #going to next page
            if(len(added) == 0):
                break
            questions.update(added)
            page += 1
        return questions
    
    def getQuestionsFromPage(self, page:int = 1, category:str = None) -> dict:
        """
        Get questions from a page.

        Params:
        page(int): The number of the page
        category(str): The id of the category

        Return:
        A list containing the Questions found
        """
        if(category == None):
            category = self.category

        return self.__questionsFromURL(URL_QUESTIONS+category +"?start=" +str((page-1)*20))
    
    def getQuestionsFromActivities(self, category:str = None) -> dict:
        """
        Get questions from activities.

        Params:
        page(int): The number of the page
        category(str): The id of the category

        Return:
        A list containing the Questions found
        """
        if(category == None):
            category = self.category
        return self.__questionsFromURL(URL_ACTIVITIES + category)
    
    def getAnswersFromQuestions(self,questions:dict, update=True) -> dict:
        answers = {}
        for question in questions.values():
            answers.update(self.getAnswersFromQuestion(question, update))
        return answers

    def getAnswersFromQuestion(self,question:dict, update=True) -> dict:
        pageAnswers = self.__getHTMLFromURL(URL_BASE + question[Keys.ID]).cssselect("div.answer")
        answers = {}
        for answerDiv in pageAnswers:
            answer = {Keys.TYPE:Keys.TYPE_ANSWERS}

            #getting data from answer
            answer[Keys.ID]            = answerDiv.attrib['id'][1:]
            
            #this is necessary otherwise it will get the last edit from the last comment inside the answer
            editDiv = answerDiv.cssselect(".qa-a-item-wrapper")[0]
            answer[Keys.CREATED]    = Q2A.__firstEdit(editDiv)
            answer[Keys.LAST_EDIT]     = Q2A.__lastEdit(editDiv)

            answer[Keys.TEXT]          = answerDiv.cssselect(".entry-content")[0].text_content()

            answer[Keys.PARENT]        = question
            
            if(len(answerDiv.cssselect('.qa-a-selected')) != 0):
                question [Keys.BEST] =  answer[Keys.ID] 

            #appending question to questions
            answers[answer[Keys.ID] ] = answer
        if(update):
            question[Keys.TYPE_ANSWERS] = answers
        return answers

    def getCommentsFromAnswers(self,answers:dict, update=True):
        comments = {}
        for answer in answers.values():
            comments.update(self.getCommentsFromAnswer(answer,update))
        return comments

    def getCommentsFromAnswer(self, answer:dict, update=True):
        answerComments = self.__getHTMLFromURL(URL_BASE + answer[Keys.PARENT][Keys.ID]).cssselect(f'#a{answer[Keys.ID]} .comment')
        comments = {}
        for commentDiv in answerComments:
            comment = {Keys.TYPE:Keys.TYPE_COMMENTS}

            #getting data from answer
            comment[Keys.ID]            = commentDiv.attrib['id'][1:]
            comment[Keys.CREATED]       = Q2A.__firstEdit(commentDiv)
            comment[Keys.LAST_EDIT]     = Q2A.__lastEdit(commentDiv)
            comment[Keys.TEXT]          = commentDiv.cssselect(".entry-content")[0].text_content()

            comment[Keys.PARENT]        = answer

            #appending question to questions
            comments[comment[Keys.ID] ] = comment
        if(update):
            answer[Keys.TYPE_COMMENTS] = comments
        return comments

    def sendVote(self, like:dict, upVote:bool = True):
        #navigate to Question otherwise site goes MAD (and meanwhile i update code)
        question_id = like['question']['id']
        like_id = like['id']

        tree = self.__getHTMLFromURL(URL_BASE+question_id)
        form = tree.xpath("//div[@id='voting_"+like_id+"']/ancestor::form")[0]

        headers = self.LIKE_HEADERS.copy()
        headers['referer'] = question_id

        postData = {
            "postid": like_id,
            "vote": int(upVote),
            "code": Q2A.__getCode(form),
            "qa": "ajax",
            "qa_operation": "vote",
            "qa_root": "./",
            "qa_request": question_id,
        }


        result = self.session.post(URL_BASE, headers=headers, data = postData).text.split('\n')
        if result[1] == '1':
            return True
        
        return result[2]
    #endregion


    def getLikes(self,**questions)-> list:
        likes = []
        for question in questions:
            tree = self.__getHTMLFromURL(URL_BASE+question[Keys.ID])
            for like in tree.cssselect(".qa-voting"):
                name = like.cssselect(".qa-vote-one-button")[0].get("name")
                voted = name if name == None else (name.split("_")[2] == '0')
                likes.append({Keys.ID:like.attrib["id"].split("_")[1], Keys.VOTED:voted})
        return likes

# flake8: noqa #This is required for my mental stability
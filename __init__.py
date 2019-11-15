import pickle
import requests
import cssselect

from lxml import html
from typing import List

#urls
URL_BASE        = "https://q2a.di.uniroma1.it/"
URL_QUESTIONS   = "https://q2a.di.uniroma1.it/questions/"
URL_LOGIN       = "https://q2a.di.uniroma1.it/login?to="
URL_USER        = "https://q2a.di.uniroma1.it/user"
URL_USERS       = "https://q2a.di.uniroma1.it/users"
URL_ACTIVITIES  = "https://q2a.di.uniroma1.it/activity/"

#KEYS FOR DICTIONARIES
#types
KEY_TYPE        = 'types'
KEY_QUESTIONS   = 'questions'
KEY_ANSWERS     = 'answers'
KEY_COMMENTS    = 'comments'

#general data
KEY_ID          = 'id'
KEY_TEXT        = 'text'
KEY_PARENT      = 'parent'
#edits
KEY_CREATED     = 'created'
KEY_LAST_EDIT   = 'last_edit'

KEY_TIMESTAMP   = 'timestamp'
KEY_USER        = 'user'

#question data
KEY_TITLE       = 'title'
#answer data
KEY_BEST        = 'best'
#like data
KEY_VOTED       = 'voted'

def Q2ADictToSerializable(q2a_dict:dict):
    q2a_dict = q2a_dict.copy()
    for key,value in q2a_dict.items():
        if key == KEY_PARENT and isinstance(value,dict):
            #removing circular reference
            q2a_dict[key] = value[KEY_ID]
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
        return {KEY_USER: edit_who, KEY_TIMESTAMP:edit_timestamp}

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
            question = {KEY_TYPE:KEY_QUESTIONS}
            #getting out data from question
            
            question[KEY_ID]            = questionDiv.attrib['id'][1:]
            question[KEY_TITLE]         = questionDiv.cssselect(".qa-q-item-title span")[0].text
            #getting last edit from what, when, who, not really reliable as it depends on if you use questions or activities
            #who = questionDiv.cssselect('.qa-user-link')[0].attrib['href']
            #question[KEY_LAST_EDI T] = {
            #    'what':questionDiv.cssselect('.qa-q-item-what')[0].text,
            #    'when':questionDiv.cssselect('.qa-q-item-when-data')[0].text,
            #    'who':who[who.rfind('/')]
            #}

            #navigating to question to get inner data
            questionInnerDiv = self.__getHTMLFromURL(URL_BASE+question[KEY_ID]).cssselect('div.question')[0]
            question[KEY_CREATED]       = Q2A.__firstEdit(questionInnerDiv)
            question[KEY_LAST_EDIT]     = Q2A.__lastEdit(questionInnerDiv)
            question[KEY_TEXT]          = questionInnerDiv.cssselect(".entry-content")[0].text_content()

            #appending question to questions
            questions[question[KEY_ID]] = question

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
            answers.update(self.getAnswersFromQuestion(question), update)
        return answers

    def getAnswersFromQuestion(self,question:dict, update=True) -> dict:
        pageAnswers = self.__getHTMLFromURL(URL_BASE + question[KEY_ID]).cssselect("div.answer")
        answers = {}
        for answerDiv in pageAnswers:
            answer = {KEY_TYPE:KEY_ANSWERS}

            #getting data from answer
            answer[KEY_ID]            = answerDiv.attrib['id'][1:]
            
            #this is necessary otherwise it will get the last edit from the last comment inside the answer
            editDiv = answerDiv.cssselect(".qa-a-item-wrapper")[0]
            answer[KEY_CREATED]    = Q2A.__firstEdit(editDiv)
            answer[KEY_LAST_EDIT]     = Q2A.__lastEdit(editDiv)

            answer[KEY_TEXT]          = answerDiv.cssselect(".entry-content")[0].text_content()

            answer[KEY_PARENT]        = question
            
            if(len(answerDiv.cssselect('.qa-a-selected')) != 0):
                question [KEY_BEST] =  answer[KEY_ID] 

            #appending question to questions
            answers[answer[KEY_ID] ] = answer
        if(update):
            question[KEY_ANSWERS] = answers
        return answers

    def getCommentsFromAnswers(self,answer:dict, update=True):
        comments = {}
        for question in questions.values():
            comments.update(self.getAnswersFromQuestion(question),update)
        return comments

    def getCommentsFromAnswer(self, answer:dict, update=True):
        answerComments = self.__getHTMLFromURL(URL_BASE + answer[KEY_PARENT][KEY_ID]).cssselect(f'#a{answer[KEY_ID]} .comment')
        comments = {}
        for commentDiv in answerComments:
            comment = {KEY_TYPE:KEY_ANSWERS}

            #getting data from answer
            comment[KEY_ID]            = commentDiv.attrib['id'][1:]
            comment[KEY_CREATED]    = Q2A.__firstEdit(commentDiv)
            comment[KEY_LAST_EDIT]     = Q2A.__lastEdit(commentDiv)
            comment[KEY_TEXT]          = commentDiv.cssselect(".entry-content")[0].text_content()

            comment[KEY_PARENT]        = answer

            #appending question to questions
            comments[comment[KEY_ID] ] = comment
        if(update):
            answer[KEY_COMMENTS] = comments
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
            tree = self.__getHTMLFromURL(URL_BASE+question[KEY_ID])
            for like in tree.cssselect(".qa-voting"):
                name = like.cssselect(".qa-vote-one-button")[0].get("name")
                voted = name if name == None else (name.split("_")[2] == '0')
                likes.append({KEY_ID:like.attrib["id"].split("_")[1], KEY_VOTED:voted})
        return likes

if __name__ == "__main__":
    import pprint,json
    pp = pprint.PrettyPrinter()
    

    q2a = Q2A()
    questions = q2a.getQuestionsFromActivities()
    question1 = questions[list(questions.keys())[0]]
    
    answers = q2a.getAnswersFromQuestion(question1)
    answer1 = answers[list(answers.keys())[0]]

    comments = q2a.getCommentsFromAnswer(answer1)
    comment1 = comments[list(comments.keys())[0]]
        
    print(json.dumps(questions, indent=4, sort_keys=True))
    #print(pprint.pformat(questions))
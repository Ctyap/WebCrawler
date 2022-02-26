import re
import requests
from collections import defaultdict 
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urldefrag
import urllib
from bs4 import BeautifulSoup


#Dictionary (word -> count): to keep count of 50 most common words -- refers to Question 3.
wordDict = defaultdict(int) 

#Dict{URL: COUNT}: to keep track of each URL and total word count
longest_page = defaultdict(int)

#Record of all links explored-- set collection makes it unique
total_links = set()

#Dictionary that keeps track of all ics.uci.edu subdomains
subdomains = dict()

#List that includes all English stop words to be skipped when tokenizer -- refers to Question 3.
stop_words = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as",
             "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
             "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
             "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
             "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
             "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
             "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of",
             "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
             "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
             "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
             "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under",
             "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
             "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
             "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
             "yourself", "yourselves"]

#List of invalid extensions found in the URL
bad_extension = ["pdf","js","bmp","gif","jpe?g","ico","png","tiff?","mid","mp2","mp3","mp4","wav","avi","mov","mpeg","ram","m4v","mkv","ogg","ogv","css","ps","eps","tex","ppt","pptx","doc","docx","xls","xlsx","names","data","dat","exe","bz2","tar","msi","bin","7z","psd","dmg","iso","epub","dll","cnf","tgz","sha1","thmx","mso","arff","rtf","jar","csv","rm","smil","wmv","swf","wma","zip","rar","gz","ppsx"]


def scraper(url, resp):
    
    retrieved_links = []
    
    #e_n_l functions returns boolean based on valid and resp.status
    if extract_next_links(url, resp):
        links = extract_next_links(url, resp)
        for link in links:
            if is_valid(link):
                retrieved_links.append(link) 
    
    #Add newly extracted links to set of total links.
    total_links.update(retrieved_links)

    #For visual when testing
    print("The size increased from {} to {}: ".format(len(total_links) - len(retrieved_links), len(total_links)))
    
    #Updates report.txt with data collected.
    createReport()
    
    return retrieved_links


#Parameters:  (URL: http://www.ics.uci.edu, RESP: Page itself)
def extract_next_links(url, resp):
    
    #Print statement for visual when testing
    print("URL being Crawled: " + str(url))
    
    #List of links retrieved that will be returned
    retrievedLinks = set()
    
    #Create parsed url object
    parsed = urlparse(url)
    
    #Create a base_url variable for creating final url with .urljoin
    BASE_URL = "https://" + parsed.netloc
    
    #List of tokens that are alnum and not an english stopword of current webpagae being crawled.
    token_lst = list()
    
    #Checks if given url is valid or not and status code is acceptable or not.
    if is_valid(url) is True and (200 <= resp.status <= 299): #ONCE WE UNDERSTAND HOW TO TEST: and (resp.status is 200|201|202)
    
        #Status meaning there is no content
        if resp.status == 204:
            return False
        
        #Variable that holds html text to be passed through to create soup object.
        html_text = resp.raw_response.content
        
        #Create a soup object to parse HTML documents (allows us to extract info we need from webpages).
        soup = BeautifulSoup(html_text, "html.parser")
        
        #List of text of a group that strips whitespace characters: (Upcoming Events,Apr 19 | 4:00pm - 5:00pm, Towards an Atlas of AI: A Conversation with Kate Crawford )
        text_list = [text for text in soup.stripped_strings]

        #A list of valid words/tokens found in current webpage
        word_lst = tokenizer(text_list)
        
        #The word count of current page
        word_count = len(word_lst)
        
        #Removes pages that have low information value
        #Why 150: 150 words is a size of a paragraph which wouldn't be enough information for a webpage to be relevant.
        if word_count < 150:
            return False
        
        #Adding valid tokens/words to token list to be passed in a dictionary.
        token_lst.extend(word_lst)

        #Adds current URL and its word count to longest_page dictionary.
        longest_page[url] = word_count

        #Adds valid words and its count of page to the commonWord Dictionary -- refers to question 3.
        create_commonWord_Dictionary(token_lst)
        
        #For each link for every link found in a web page
        for link in soup.find_all('a'):
            
            #Retrieves the full link
            fullLink = link.get('href')
            
            #(Base: page crawler is on, FullLink: the href of an anchor of that page)
            newLink = urllib.parse.urljoin(BASE_URL, fullLink)
            
            #Splits link at # character (eg. "http://www.address.com/something#something" ->('http://www.address.com/something', 'something') )
            url, fragment = urldefrag(newLink)
            
            #If the extracted URL is valid, add it to the total of retrieved links.
            if is_valid(url): 

                retrievedLinks.add(url)
        
        #Returns a set of all extracted valid links of passed URL.
        return retrievedLinks
    
    else:
        #If passed URL is invalid or returns non acceptable status code, return empty list.
        return []


#Helper function that returns a list of words from page.
def tokenizer(text_list):
    
    #String of punctuation to be removed.
    punc = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''

    #Create a local token list that will be returned.
    token_lst = list()
    
    #Lowers of all the text passed through text_list
    word_lst = [word.lower() for word in text_list]

    #Iterates through each group of words.
    for word_group in word_lst:
        
        #Iterates through each word of each group of words.
        for word in word_group.split():
            
            #Iterates through each char of word.
            for char in word:
                
                #Checking if punctation exists in word, if so remove.
                if char in punc:
                    word = word.replace(char,"")
                    
                    #Deals with '_' characters in a word. It divides it into one word.
                    if '_' in word:
                        
                        #Create a list of divided by underscore
                        word_lst = word.split('_')
                        
                        #Add words to token list if: alphanumeric and not an english stopword.
                        token_lst.extend(split_word for split_word in word_lst if split_word.isalnum() and split_word not in stop_words)
            
            #If no punctuation exists, then add to token list if alphanumeric and not an english stopword.
            if word.isalnum() and word not in stop_words:

                token_lst.append(word)

    #Returns list of valid tokens extracted from webpage.
    return token_lst


#Helper funciton that catches a URL trap
def catch_traps(parsed_url):
    #https://support.archive-it.org/hc/en-us/articles/208332963-How-to-modify-your-crawl-scope-with-a-Regular-Expression
    
    #Checks for long URL trap
    #E.G: https://help.dragonmetrics.com/en/articles/213691-url-too-long
    if (len(str(parsed_url.geturl()))) > 100:
        return True
    
    #Checks for repeating directories
    elif re.match(" ^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", parsed_url.path):
        return True
    
     #Checks for extra directories.
    elif re.match("^.*(/misc|/sites|/all|/themes|/modules|/profiles|/css|/field|/node|/theme){3}.*$", parsed_url.path):
        return True
    
    #Checks for calendar traps
    elif re.match("^.*calendar.*$", parsed_url.path):
        return True
    
    #Checks for invalid extensions found un URL
    for i in bad_extension:
        if i in parsed_url.path or parsed_url.query:
            return True
    
    else:
        
        #No traps were found
        return False


#Helper function that creates the Dictionary of common words with frequency -- refers to question 3
def create_commonWord_Dictionary(token_lst):
    
    #Increment value/count if token already exists
    for token in token_lst:
        wordDict[token] += 1
    

def is_valid(url):
    """
    Return URLs that are within the domains and paths of: (*.ics.uci.edu/*, *.cs.uci.edu/*, *.informatics.uci.edu/*, *.stat.uci.edu/*, 
    today.uci.edu/department/information_computer_sciences/* )
    """
    try:
        """
        Creates a parsed object: 6-item named tuple:
        EXMAPLE: 'http://abc.hostname.com/somethings/anything/'
        RETURNS: ParseResult(scheme='http', netloc='abc.hostname.com', path='/somethings/anything/', params='', query='', fragment='')
        """
        parsed = urlparse(url)
        
        #Example: abc.hostname.com or www.ics.uci.edu -- includes subdomain
        domain = parsed.netloc
        
        
    
        
        #Scheme must be http or https.
        if parsed.scheme not in set(["http", "https"]):
            #print("HTTP NOT IN SET")
            return False
        
        #Returns false if trap is found in URL.
        if catch_traps(parsed):
            return False
        
        #Checks if link is already crawled.
        if url in total_links:
            return False
        
        #Calls helper function to check if domain is valid.
        elif checkDomain(domain, parsed, url) is False:
            return False
        
        #If path has an following extension existing, return false.
        elif re.search(
                r".*\.(pdf|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|css"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppsx)$", parsed.path.lower()):
                    print("NON ACCEPTABLE EXTENSION")
                    return False

        else:
   
            
            #If passes all valid tests, then return True.
            return True
        
    
    #Exception.
    except TypeError:
        print ("TypeError for ", parsed)
        raise
    

#Helper function that checks if given domain is valid or not.
def checkDomain(domain, parsed, url):
    
    #List of valid domains that we are allowed to crawl specified by prompt
    validDomains = ["ics.uci.edu","cs.uci.edu", "stat.uci.edu",
              "informatics.uci.edu"]
    
    #Removes www. to compare to valid domains
    if domain.startswith("www."):
        domain = domain.strip("www. ")


    """
    Through the validDomains list, we see each domain can be split at its period at a maximum length of 3.
    This means a subdomain exists if the length of the split domain is greater than 3.
    This will separate the subdomain and domain into two new variables.
    """
    if len(domain.split('.')) > 3:
        #Variable that holds only subdomain.
        subdomain = domain.split('.')[0]
        
        #Variable that holds domain.
        domain = '.'.join(domain.split('.')[1:])
        
        #Helper function that adds subdomain name if under ics.uci.edu
        addSubdomain(subdomain, domain, parsed, url)
        
    #If the domain of passed URL is a valid domain return true.
    if domain not in validDomains:
        return False
    
    #Checks for special case of today.uci.edu domain because it requires a specific path for it be return True.
    if domain == "today.uci.edu" and  "/department/information_computer_sciences" in parsed.path:
        return True
    
    #If doesn't pass the tests, then it is not a valid domain.
    else:
        return True
    

#populates subdomain dictionary

def addSubdomain(subdomain, domain, parsed, url):
    
    #Checks if domain is ics.uci.edu
    if domain == "ics.uci.edu":
        
        #Checks if the domain, which includes the subdomain, exists in subdomain dict or not (mcs.ics.uci.edu).
        sub_plus_domain = parsed.scheme+"://" + parsed.netloc
        
        #If the subdomain has not already been checked/added.
        if sub_plus_domain not in subdomains:
            try: 
                #Creates a soup object to collected its unqique pages.
                request_obj = requests.get(url)
                soup = BeautifulSoup(request_obj.content, "html.parser")
                
                #Add count of extracted links of current subdomain.
                subdomains[sub_plus_domain] = len(set([link for link in soup.find_all('a')]))
            
            #Excepts connection error.
            except:
                subdomains[sub_plus_domain] = 0
                pass
        
                    
    
def createReport():
    #Extracts required data from collections to create the report.txt
    f = open("report.txt","w+")
    
    uniquePages = set()
    
    #Question 1
    for link in total_links:
        uniquePages.add(link)
    
    uniquePageCount = len(uniquePages)
    f.write("Number of unique pages found: " + str(uniquePageCount) + "\n")
    
    lst = sorted(longest_page.items(), key = lambda t: (-t[1],t[0]))
    
    #Question 2
    f.write("Longest page in terms of word: {} \n".format(str(lst[0][0])))
    f.write("Longest page word count: {}\n".format(str(lst[0][1])))
    
    #Question3
    for token, count in sorted(wordDict.items(), key=lambda item: (-item[1], item[0]))[:50]:
        f.write("\n" + token + " -> " + str(count))
        
    #Question 4
    f.write("\n")
    f.write("\nSubdomains: \n")
    f.write("Total number of subdomains within ics.uci.edu: {}".format(len(subdomains)))
    subdomainLst = sorted(subdomains.items(), key = lambda t: (t[0]))
    for subdomain, count in subdomainLst:
        f.write("\n{} {}".format(subdomain, count))
    
    f.close()

    

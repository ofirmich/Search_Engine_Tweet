import math
import string
import copy

from nltk import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from document import Document
import re


class Parse:

    def __init__(self, toStem):
        self.stop_words = stopwords.words('english')
        self.shortcuts = {'imma': "I am", 'im' : "I am" ,'gov':'governor','jan': 'january','governm': "government" ,  "aint": 'is not', "arent": 'are not', "cant": 'cannot', "cantve": 'cannot have',
                     'cause': 'because',
                     "couldve": 'could have', "couldnt": 'could not',
                     "couldntve": 'could not have', "didnt": 'did not', "doesnt": 'does not', "dont": 'do not',
                     "hadnt": 'had not', "hadntve": 'had not have', "hasnt": 'has not',
                     "havent": 'have not', "hed": 'he had', "hes": 'he is', "howll": 'how will', "hows": 'how is',
                     "Id": 'I would', "Ill": 'I will', "Im": 'I am', "Ive": 'I have', "isnt": 'is not',
                     "itd": 'it had', "itll": 'it will', "its": 'it is', "lets": 'let us', "maam": 'madam',
                     "maynt": 'may not',
                     "mightve": 'might have', "mightnt": 'might not', "mustve": 'must have',
                     "mustnt": 'must not', "mustntve": 'must not have', "neednt": 'need not',
                     "needntve": 'need not have',
                     "oclock": 'of the clock', "shant": 'shall not', "shed": 'she had',
                     "shes": 'she is', "shouldve": 'should have', "shouldnt": 'should not', "sove": 'so have',
                     "thatd": 'that would', "thats": 'that is', "thered": 'there would',
                     "theres": 'there is', "theyd": 'they would', "theyll": 'they will', "theyre": 'they are',
                     "theyve": 'they have', "wasnt": 'was not', "well": 'we will',
                     "we've": 'we have', "weren't": 'were not', "whatll": 'what will', "whatre": 'what are',
                     "whats": 'what is',
                     "whatve": 'what have',
                     "whens": 'when is', "wheres": 'where is', "who'll": 'who will', "whos": 'who is',
                     "willve": 'will have',
                     "wont": 'will not',
                     "wouldve": 'would have', "wouldnt": 'would not', "yall": 'you all',
                     "youd": 'you would', "youll": 'you all', "youre": 'you are', "youve": 'you have', 'gonna': 'going to'}
        self.add_stop = ["get","though","anyway","maybe","ways","different","back","somehow","plus","am" ,"less","far","round","will","willing","down","potentially","successful","anymore","anyone","across" , "fewer", "few" ,"results","resulted" ,"resulting","significant","instead" ,"also","returns","return","tooks" ,"took","look", "looks","nobody","rt" ,"every","definitely","got","would" ,"and" "you","how", "ok", "yeah","how","ncov","status", "web", "no","but" ,"it" ,"no", "yes","the", 'if','www' ,'of', 'this', 'twitter.com','https', 'RT' ,'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',"something", "date", "like"]
        self.stop_words.extend(self.add_stop)
        self.toStem = toStem


    def parse_sentence(self, text):
        """
        This function tokenize, remove stop words and apply lower case for every word within the text
        :param text:
        :return:
        """
        text_tokens = word_tokenize(text)
        text_tokens_without_stopwords = []
        skip_ind = 0


        entities_dict = {}


        for index in range(len(text_tokens)):
            if skip_ind > 0:
                skip_ind -= 1
                continue

            word = text_tokens[index]


            if self.isAscii(word) is False:
                continue

            word = self.clean_end_begining(word)
            if len(word) == 0:
                continue

            if word.lower() in self.stop_words or word in string.punctuation or (index + 1 < len(text_tokens) and text_tokens[index + 1] == '…'):
                continue

            """----------------------remove curses---------------------"""

            curse_list = ['fuck', 'shit', 'piss', 'dick', 'tit', 'asshole', 'bitch', 'damn', 'cunt', 'bollocks', 'choad','bugger', 'rubbish', 'shag', 'wanker','twat', 'crap', 'arse', 'bint', 'bullshit','clunge', 'gash', 'pussy', 'cock', 'dickhead', 'bastard', 'motherfucker' ]
            if word.lower() in curse_list:
                continue

            """----------------------check shortcuts---------------------"""

            if word.lower() in self.shortcuts:
                new_lst = self.shortcuts[word.lower()].split()
                for check in new_lst:
                    if check.lower() in new_lst in self.stop_words:
                        new_lst.remove(check)
                text_tokens_without_stopwords.extend(new_lst)
                continue

            """----------------------check initialias like U.S---------------------"""
            if index + 2 < len(text_tokens) and word[0].isupper() and len(word) == 1 and '.' in text_tokens[index+1] and text_tokens[index+2][0].isupper() and len(text_tokens[index+2][0])==1:
                text_tokens_without_stopwords.append(word + text_tokens[index+1] + text_tokens[index+2])
                skip_ind = 2
                continue

            """----------------------check enitites---------------------"""

            if word[0].isupper() and index + 1 < len(text_tokens) and text_tokens[index + 1][0].isupper():
                temp_ind = index + 1
                temp_word = word
                counter_skip = 0
                while temp_ind < len(text_tokens) and text_tokens[temp_ind][0].isupper() and text_tokens[temp_ind] not in self.stop_words:
                    temp_word = temp_word + " " + text_tokens[temp_ind]
                    temp_ind = temp_ind + 1
                    counter_skip += 1
                if " " in temp_word:
                    if temp_word in entities_dict:
                        entities_dict[temp_word] += 1

                    else:
                        part_of_entity = False
                        entities_dict[temp_word] = 1
                        sep_entity = temp_word.split()
                        text_tokens_without_stopwords.extend(sep_entity)

                    if counter_skip > 0:
                        skip_ind = counter_skip
                        continue

            if ' ' in word:
                if "t.co" in word:
                    word_to_split = word.split('\n')
                    if word_to_split[0].isdigit():
                        word = word_to_split[0]

                """-----------check url------------"""

            elif "http" in word or "t.co" in word or "www" in word:
                returned_token = self.check_url(word)  # check if the term is url
                text_tokens_without_stopwords.extend(returned_token)
                continue

                """-----------check hashtag------------"""

            elif word[0] == "#":
                text_tokens_without_stopwords.extend(self.check_hashtag(word))
                continue

                """-----------check tag------------"""
            elif word[0] == "@":
                text_tokens_without_stopwords.append(word)
                continue

                """--------check if the term is number--------"""
            elif word.replace(",", "").isdigit() or word.replace(".", "").isdigit():
                if word.count('.') > 1:
                    text_tokens_without_stopwords.append(word)
                    continue
                elif index + 1 < len(text_tokens):
                    next_word = text_tokens[index + 1]
                    """--------check percent--------"""
                    if next_word == "%" or next_word == "percent" or next_word == "percentage":
                        skip_ind = 1
                        text_tokens_without_stopwords.append(word + "%")
                        continue

                        """--------check fric--------"""
                    elif "/" in next_word and 'http' not in next_word:
                        skip_ind = 1
                        if next_word[0].isdigit() and next_word[len(next_word)-1].isdigit():
                            text_tokens_without_stopwords.append(word+" "+next_word)
                            continue
                        """--------check dollar--------"""
                    elif next_word == "$" or next_word == "Dollar" or next_word == "Dollars" or next_word == "dollar" or next_word == "dollars":
                        skip_ind = 1
                        text_tokens_without_stopwords.append(word + "$")
                        continue
                    else:
                        """--------check thousands/million/billion--------"""
                        returned_token = self.check_mbk(word, text_tokens[index + 1])  # with million or billion or thousend
                        if returned_token != None:  # is mbk
                            skip_ind = 1
                            text_tokens_without_stopwords.append(returned_token)
                            continue
                        else:
                            returned_token = self.check_number(word)  # regular number
                            if not isinstance(returned_token, str):
                                text_tokens_without_stopwords.extend(returned_token)
                            else:
                                text_tokens_without_stopwords.append(returned_token)
                            continue
                else:
                    text_tokens_without_stopwords.append(word)
                    continue

            else:
                text_tokens_without_stopwords.append(word)
            """--------stemming--------"""
        if self.toStem:
            text_tokens_without_stopwords = self.stemmer(text_tokens_without_stopwords)

        return [text_tokens_without_stopwords, entities_dict]

    def parse_url(self, url):
        sep_list = re.split('":"', url)
        long_url = sep_list[1][:-2]
        return long_url

    def parse_doc(self, doc_as_list):
        """
        This function takes a tweet document as list and break it into different fields
        :param doc_as_list: list re-preseting the tweet.
        :return: Document object with corresponding fields.
        """

        tweet_id = doc_as_list[0]
        tweet_date = doc_as_list[1]
        full_text = doc_as_list[2]
        url = doc_as_list[3]
        indices = doc_as_list[4]
        retweet_text = doc_as_list[5]
        retweet_url = doc_as_list[6]
        retweet_indices = doc_as_list[7]
        quote_text = doc_as_list[8]
        quote_url = doc_as_list[9]
        quoted_indices = doc_as_list[10]
        retweet_quoted_text = doc_as_list[11]
        retweet_quoted_urls = doc_as_list[12]
        retweet_quoted_indices = doc_as_list[13]

        term_dict = {}
        entities_dict={}
        tokenized_text = []
        """--------parse url and quote--------"""
        if len(url) > 2:
            url_finished = str(self.parse_url(url))
            returned_token = self.check_url(url_finished)  # check if the term is url
            check_spec = '2019'
            if check_spec in returned_token:
                returned_token.remove(check_spec)

            if len(returned_token) > 0:
                tokenized_text.extend(returned_token)
            else:
                tokenized_text.append(returned_token)

        to_insert_list_dict = self.parse_sentence(full_text)
        tokenized_text += to_insert_list_dict[0]
        for key in to_insert_list_dict[1]:
            if key in entities_dict:
                entities_dict[key] = entities_dict[key] + to_insert_list_dict[1][key]
            else:
                entities_dict[key] = to_insert_list_dict[1][key]

        if quote_text != None and len(quote_text) > 2:
            to_insert_list_dict = self.parse_sentence(quote_text)
            for term_from_quote in to_insert_list_dict[0]:
                if term_from_quote in tokenized_text:
                    to_insert_list_dict[0].remove(term_from_quote)
            tokenized_text += to_insert_list_dict[0]
            for key in to_insert_list_dict[1]:
                if key in entities_dict:
                    entities_dict[key] = entities_dict[key] + to_insert_list_dict[1][key]
                else:
                    entities_dict[key] = to_insert_list_dict[1][key]

        doc_length = len(tokenized_text)  # after text operations.

        for term in tokenized_text:

            if len(term) == 0 or term.lower() in self.stop_words or self.isAscii(term) == False or (term.isdigit() and len(term) > 15):
                continue


            if len(term) == 0:
                continue


            term_dict = self.upperCase_handler(term, term_dict)

        document = Document(tweet_id, tweet_date, full_text, url, retweet_text, retweet_url, quote_text,
                            quote_url, term_dict, entities_dict, doc_length)

        return document



    def stemmer(self , text_tokens):
        finale_list = []
        ps = PorterStemmer()
        for text_obj in text_tokens:
            if text_obj == text_obj.title():
                obj_stemming = ps.stem(text_obj).title()
            elif text_obj.isupper():
                obj_stemming = ps.stem(text_obj).upper()
            else:
                obj_stemming = ps.stem(text_obj)
            finale_list.append(obj_stemming)
        return finale_list

    def upperCase_handler(self, term, term_dict):
        if '#' == term[0] or '@' == term[0] or term[0].isdigit():
            if term not in term_dict.keys():
                term_dict[term] = 1
                return term_dict
            else:
                term_dict[term] += 1
                return term_dict
        if term[0].islower():
            if term.lower() in term_dict.keys():  # lowercase in dict
                term_dict[term.lower()] += 1
                return term_dict
            elif term.upper() in term_dict.keys():  # uppercase in dict
                # term is lower and appears in dict as upper, make the term lower case and add the num of shows
                term_dict[term.lower()] = term_dict[term.upper()]  # add the prev info of upper key
                term_dict[term.lower()] += 1
                del term_dict[term.upper()]
                return term_dict
            else:
                term_dict[term.lower()] = 1
                return term_dict
        else:  # term[0] is upper
            if term.upper() in term_dict.keys():
                term_dict[term.upper()] += 1
                return term_dict
            elif term.lower() in term_dict.keys():
                term_dict[term.lower()] += 1
                return term_dict
            else:
                term_dict[term.upper()] = 1
                return term_dict

    def check_hashtag(self,word):
        """check if the term is hashtag of _ or uppercases"""
        try:
            if "_" in word or "-" in word or "'" in word:
                if "_" in word:
                    seperator = "_"
                elif "-" in word:
                    seperator = "-"
                else:
                    seperator = "'"
                sep_list = re.split(seperator, word[1:])
                sep_list = [x.lower() for x in sep_list]
                sep_list.append((word.replace("_", "")).lower())
                empty_str = ''
                if empty_str in sep_list:
                    sep_list.remove(empty_str)
            else:
                sep_list = []
                sep = re.split('(?=[A-Z])', word[1:])
                sep = " ".join(sep).split()
                if sep[0][0] == '#':
                    sep[0] = sep[0][1:]
                res = []
                collect = ""
                for word_check in sep:
                    if any(char.isdigit() for char in word_check):
                        if word_check.isdecimal():
                            sep_list.append(word_check)
                            continue
                        if word_check[0].isdigit():
                            temp = re.compile("([0-9]+)([a-zA-Z]+)")
                            res = temp.match(word_check).groups()
                        else:
                            temp = re.compile("([a-zA-Z]+)([0-9]+)")
                            res = temp.match(word_check).groups()

                        if len(res) > 0:
                            for inside_word in res:
                                if inside_word.isalpha():
                                    collect += inside_word.lower()
                                    word_check = word_check[len(inside_word):]
                                else:
                                    if len(collect) > 0:
                                        sep_list.append(collect)
                                        collect = ''
                                    sep_list.append(inside_word)
                                    word_check = word_check[len(inside_word):]
                                    if len(word_check) > 0:
                                        sep_list.append(word_check)

                        else:
                            if word_check.isalpha():
                                sep_list.append(inside_word.lower())
                            else:
                                sep_list.append(inside_word)
                    else:
                        if len(word_check) == 1:
                            collect += word_check.lower()
                        else:
                            if len(collect) > 0:
                                sep_list.append(collect)
                                collect = ''
                            sep_list.append(word_check.lower())
                if len(collect) > 0 and collect not in sep_list:
                    sep_list.append(collect)
                sep_list.append(word.lower())

            return sep_list
        except:
            print(word)

    def isAscii(self,s):
        return all(ord(c) < 128 for c in s)

    def check_mbk(self,word, next_word):
        if next_word.lower() == "thousand":
            return word + "K"
        if next_word.lower() == "million":
            return word + "M"
        if next_word.lower() == "billion":
            return word + "B"

    def check_number(self,word):
        to_number = float(word.replace(",", ""))
        str_num = ""

        if 0 <= to_number < 1000:
            b = int(to_number * 1000) / 1000.
            last_num = float("%.3f" % b)
            if last_num.is_integer():
                str_num = str(int(last_num))
            else:
                str_num = str(last_num)
            return str_num

        to_return = []
        if 1000 <= to_number < 1000000:
            if 1910 <= to_number <= 2050:
                to_return.append(word)
            num = to_number / 1000
            cast = float("%.3f" % num)
            if cast.is_integer():
                str_num = str(int(cast))
            else:
                str_num = str(cast)

            to_return.append((str_num + "K"))
            return to_return

        if 1000000 <= to_number < 1000000000:
            num = to_number / 1000000
            cast = ((math.floor(num * 10 * 3)) / (10 * 3))
            if cast.is_integer():
                str_num = str(int(cast))
            else:
                str_num = str(cast)

            return str_num + "M"

        if 1000000000 <= to_number:
            num = to_number / 1000000000
            cast = ((math.floor(num * 10 * 3)) / (10 * 3))
            if cast.is_integer():
                str_num = str(int(cast))
            else:
                str_num = str(cast)

            return str_num + "B"
        return word

    def remove_words_url(self,lst):
        # remove words without meaning from url
        delete_from_this = copy.deepcopy(lst)
        for i in range(len(lst)):
            word = lst[i]
            if '.' in word or '=' in word or 'http' or 'www' in word or '@' in word or word in self.stop_words:
                delete_from_this.remove(word)
        return delete_from_this


    def check_url(self,word):
        start_index = word.find('http')
        if start_index > 0:
            word = word[start_index:]  # if the start_index is not -1

        if 'twitter.com' in word or 't.co' in word:
            return []

        lst = re.split('\\?|://|/|\\|=|-|@|#|"_"|","|%', word)
        lst = self.remove_words_url(lst)
        return lst

    def clean_end_begining(self, word):
        while len(word) != 0:
            if (word[-1].isalpha() == False) and (word[-1].isdigit() == False) and (
                    word[-1] not in ["#", "%", "@"]):  # , "$"
                if len(word) > 1:
                    word = word[:-1]
                else:
                    break
            else:
                break
        while len(word) != 0:
            if (word[0].isalpha() == False) and (word[0].isdigit() == False) and (
                    word[0] not in ["#", "@"]):  # , "$"  "%"
                if len(word) > 1:
                    word = word[1:]
                elif len(word) == 1:
                    word = ''
                    break
                else:
                    break
            else:
                break
        return word

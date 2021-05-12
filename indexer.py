# DO NOT MODIFY CLASS NAME
import math
import os
import json

import utils


class Indexer:
    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def __init__(self, config):
        self.inverted_idx = {}
        self.postingDict = {}
        self.config = config
        self.entity_dict_of_corpus = {}
        self.documents = {}
        self.num_of_documents = 0
        self.dict_of_method = {}
        self.total_len_of_docs = 0

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def add_new_doc(self, document):
        """
        This function perform indexing process for a document object.
        Saved information is captures via two dictionaries ('inverted index' and 'posting')
        :param document: a document need to be indexed.
        :return: -
        """

        self.num_of_documents += 1
        "----------------merging between entities dict and doc terms-------------------"
        dict_1 = document.term_doc_dictionary
        dict_2 = document.entities_dict
        key_list = {*dict_1, *dict_2}
        added_dict = {}
        for key in key_list:
            added_dict[key] = dict_1.get(key, 0) + dict_2.get(key, 0)

        if len(added_dict.values()) > 0:
            all_values = added_dict.values()
            all_keys = list(added_dict.keys())
            distinct_list_size = len(
                set([x.lower() for x in all_keys]))  # choose all distinct terms without considering upper lower case
            max_value = max(all_values)
            value_to_doc = {'max_tf': max_value, 'num_unique': distinct_list_size, 'length': sum(dict_1.values()),
                            'w_ij': 0}
            self.documents[document.tweet_id] = value_to_doc

        "--------------insert each term to II and PS considering up and low cases-------------------"
        document_dictionary = document.term_doc_dictionary
        # Go over each term in the doc
        for term in document_dictionary.keys():
            term_to_add = term
            term_test = self.check_upper_lower(self.inverted_idx, term)
            if term_test[1] == False:  # the term not in dict-> we need tto insert for the first time
                self.inverted_idx[term_test[0]] = 1
                self.postingDict[term_test[0]] = {'total': document_dictionary[term],
                                                  'tf': {document.tweet_id: [document.term_doc_dictionary[term], 0]}}
                # [name of file, num of docs ,(tweetid , shows per tweet,wij)]
            elif term_test[1] == True:  # the term already in dicts-> need to add its values
                self.inverted_idx[term_test[0]] += 1
                self.postingDict[term_test[0]]['total'] += document_dictionary[term]
                self.postingDict[term_test[0]]['tf'][document.tweet_id] = [document.term_doc_dictionary[term], 0]
            else:  # need to replace- there is upper in dict and this term lower
                self.inverted_idx[term_test[0]] = self.inverted_idx[term_test[0].upper()] + 1
                del self.inverted_idx[term.upper()]
                self.postingDict[term_test[0]] = self.postingDict[term.upper()]  # add the prev info of upper key
                self.postingDict[term_test[0]]['total'] += document_dictionary[term]
                self.postingDict[term_test[0]]['tf'][document.tweet_id] = [document.term_doc_dictionary[term],
                                                                           0]  # add new info
                del self.postingDict[term.upper()]

        entity_dict_of_document = document.entities_dict

        for entity in entity_dict_of_document.keys():
            if entity not in self.entity_dict_of_corpus.keys() and entity not in self.inverted_idx.keys():  # first time in corpus
                # add to dict of entities in corpus- optional entity
                self.entity_dict_of_corpus[entity] = [
                    [document.tweet_id, entity_dict_of_document[entity]]]
            elif entity in self.inverted_idx.keys() and entity not in self.entity_dict_of_corpus.keys():  # already entity
                #  add to inverted index and posting dict- real entity-> need to be treated as a term
                self.inverted_idx[entity] += 1
                if entity not in self.postingDict.keys():
                    #  shouldnt happen- the terms in inverted and posting are the same
                    self.postingDict[entity] = {
                        'total': entity_dict_of_document[entity],
                        'tf': {document.tweet_id: [entity_dict_of_document[entity], 0]}}
                else:
                    self.postingDict[entity]['total'] += entity_dict_of_document[entity]
                    self.postingDict[entity]['tf'][document.tweet_id] = [entity_dict_of_document[entity], 0]
                    self.documents[document.tweet_id]['length'] += entity_dict_of_document[entity]
            else:  # create new entity
                self.inverted_idx[entity] = 2
                # its a real entity- at least twice in corpus -> we need to add to inverted both of the appearences
                if entity not in self.postingDict.keys():
                    self.postingDict[entity] = {
                        'total': entity_dict_of_document[entity] + self.entity_dict_of_corpus[entity][0][1],
                        'tf': {document.tweet_id: [entity_dict_of_document[entity], 0],
                               self.entity_dict_of_corpus[entity][0][0]: [self.entity_dict_of_corpus[entity][0][1], 0]}}
                    self.documents[document.tweet_id]['length'] += entity_dict_of_document[entity]
                    self.documents[self.entity_dict_of_corpus[entity][0][0]]['length'] += \
                    self.entity_dict_of_corpus[entity][0][1]
                    del self.entity_dict_of_corpus[entity]

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def load_index(self, fn):
        """
        Loads a pre-computed index (or indices) so we can answer queries.
        Input:
            fn - file name of pickled index.
        """
        all_dicts = utils.load_obj(fn)
        return all_dicts

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def save_index(self, fn):
        """
        Saves a pre-computed index (or indices) so we can save our work.
        Input:
              fn - file name of pickled index.
        """
        utils.save_obj([self.inverted_idx, self.postingDict, self.documents, self.dict_of_method], fn)

    # feel free to change the signature and/or implementation of this function
    # or drop altogether.
    def check_upper_lower(self, dict, term):
        """
        Checks if a term exist, how we need to save it.
        input: the term and inverted index
        output: list [term, boolien]
        term = how we should save the term
        boolien = exists in inverted index or not: True= exists False= doesnt exists replace
        * replace = in the inverted index the term is in uppercase and we are trying to insert the term in lowercase-
            we need to replace the uppercase in th dict to lowercase and add the new appearance
        """
        if '#' == term[0] or '@' == term[0] or term[0].isdigit():
            if term not in dict.keys():
                return [term, False]
            else:
                return [term, True]
        if term[0].islower():
            if term.lower() in dict.keys():  # lowercase in dict
                return [term.lower(), True]
            elif term.upper() in dict.keys():  # uppercase in dict
                # term is lower and appears in dict as upper, make the term lower case and add the num of shows
                return [term.lower(), "replace"]
            else:
                return [term.lower(), False]
        else:  # term[0] is upper
            if term.upper() in dict.keys():
                return [term.upper(), True]
            elif term.lower() in dict.keys():
                return [term.lower(), True]
            else:
                return [term.upper(), False]

    # feel free to change the signature and/or implementation of this function
    # or drop altogether.
    def slice_uncommon_terms(self):
        """
        Return the posting list from the index for a term.
        """
        # remove from inverted and posting all terms that appear only in one tweet in corpus
        self.postingDict = dict([(key, value) for key, value in self.postingDict.items() if self.inverted_idx[key] > 1])
        self.inverted_idx = dict([(key, value) for key, value in self.inverted_idx.items() if value > 1])

        # if the inverted is bigger then 100000 terms remove all terms that appear in 2 docs and then 3 and so
        # we kwwp removing until we get the correct size
        i = 2
        while len(self.inverted_idx) > 100000:
            self.postingDict = dict(
                [(key, value) for key, value in self.postingDict.items() if self.inverted_idx[key] > 1])
            self.inverted_idx = dict([(key, value) for key, value in self.inverted_idx.items() if value > i])

    def calculate_wij_idf(self):
        for term in self.inverted_idx.keys():
            "--------------------calculate idf---------------------"

            idf = math.log2(self.num_of_documents / self.inverted_idx[term])
            self.postingDict[term]['idf'] = idf

            "--------------------calculate wij---------------------"
            for tweet_id in self.postingDict[term]['tf'].keys():
                max_tf = self.documents[tweet_id]['max_tf']
                appearance_term_file = self.postingDict[term]['tf'][tweet_id][0]

                wij_single_term = (appearance_term_file / max_tf) * idf
                self.postingDict[term]['tf'][tweet_id][1] = wij_single_term
                self.documents[tweet_id]['w_ij'] += wij_single_term ** 2

        "--------------------calculate average doc length---------------------"
        average = 0
        for doc in self.documents.keys():
            average += self.documents[doc]['length']
        self.documents['-average-'] = average / self.num_of_documents

    def set_dict_methods(self, dict_from_engine):
        self.dict_of_method = dict_from_engine

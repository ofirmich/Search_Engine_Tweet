from ranker import Ranker
from nltk.corpus import wordnet
from spellchecker import SpellChecker
from nltk.corpus import stopwords, lin_thesaurus as thes


# DO NOT MODIFY CLASS NAME
class Searcher:
    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit. The model
    # parameter allows you to pass in a precomputed model that is already in
    # memory for the searcher to use such as LSI, LDA, Word2vec models.
    # MAKE SURE YOU DON'T LOAD A MODEL INTO MEMORY HERE AS THIS IS RUN AT QUERY TIME.
    def __init__(self, parser, indexer, model=None):
        self._parser = parser
        self._indexer = indexer
        self._ranker = Ranker()
        self._model = model

    # DO NOT MODIFY THIS SIGNATURE
    # You can change the internal implementation as you see fit.
    def search(self, query, k=None):
        """
        Executes a query over an existing index and returns the number of
        relevant docs and an ordered list of search results (tweet ids).
        Input:
            query - string.
            k - number of top results to return, default to everything.
        Output:
            A tuple containing the number of relevant search results, and
            a list of tweet_ids where the first element is the most relavant
            and the last is the least relevant result.
        """
        # all_dicts = self._indexer.load_index('inverted_idx.pkl')
        inverted_index = self._indexer.inverted_idx
        posting = self._indexer.postingDict
        documents = self._indexer.documents
        dict_of_methods = self._indexer.dict_of_method

        if dict_of_methods['wordnet']== True:
            #wordnet method
            doc_query_app = self.finished_dict(query, inverted_index) #  first parse query words
            list_of_query = doc_query_app.keys()
            words_to_add = {}
            # get each query word its synsets and add to query the ones that in inverted index
            for word in list_of_query:
                opt = wordnet.synsets(word)
                for i in range(len(opt)):
                    check_word = opt[i].lemmas()[0].name()
                    if check_word in doc_query_app.keys() or check_word in words_to_add.keys():
                        continue
                    tested = self._indexer.check_upper_lower(inverted_index, check_word)
                    if tested[1] is False or tested[0] in doc_query_app.keys() or tested[0] in words_to_add.keys():
                        continue
                    if tested[1] is True:
                        words_to_add[tested[0]] = 0.0001
                    elif tested[1] is 'replace':
                        words_to_add[tested[0].upper()] = 0.0001
            doc_query_app.update(words_to_add)

        elif dict_of_methods['spell_correction']== True:
            spell = SpellChecker(case_sensitive=True)
            query_as_list = query.split()
            for index in range(len(query_as_list)):
                is_upper = False
                word = query_as_list[index]
                # if word from query not in inverted index look for correction- take the first one that is in inverted index
                if self._indexer.check_upper_lower(inverted_index, word)[1] is False:  # word not in inverted index
                    if word[0].isupper() is True:
                        is_upper = True
                    options = spell.candidates(word)
                    is_found = False
                    i = 0
                    options = list(options)
                    while i < len(options):
                        if self._indexer.check_upper_lower(inverted_index, options[i])[1] is True:
                            corrected = options[i]
                            is_found = True
                            break
                        i += 1
                    # corrected = spell.correction(word)
                    if is_found is not False and corrected != query_as_list[index]:
                        if is_upper is True:
                            corrected = corrected.capitalize()
                        query_as_list[index] = corrected
            doc_query_app = self.finished_dict(" ".join(query_as_list), inverted_index)

        elif dict_of_methods['word2vec'] == True:
            words_to_add = {}
            doc_query_app = self.finished_dict(query, inverted_index)
            query_as_list = query.split()
            insert_new_words = []
            for word in query_as_list:
                if word in self._model.wv.wv.vocab:
                    lst_sim_word_model = self._model.most_similar(word.lower())
                    for similiar_word in lst_sim_word_model:
                        if similiar_word[1] > 0.33:
                            insert_new_words.append(similiar_word[0])

            # if len(insert_new_words) == 0:
            #     continue
            idx = 0
            while idx < len(insert_new_words):
                if insert_new_words[idx] in doc_query_app.keys() or insert_new_words[idx] in words_to_add.keys():
                    idx += 1
                    continue
                tested = self._indexer.check_upper_lower(inverted_index, insert_new_words[idx])
                if tested[1] is False or tested[0] in doc_query_app.keys() or tested[0] in words_to_add.keys():
                    idx += 1
                    continue
                if tested[1] is True:
                    words_to_add[tested[0]] = 0.6
                    break
                elif tested[1] is 'replace':
                    words_to_add[tested[0].upper()] = 0.6
                    break
                idx += 1
            doc_query_app.update(words_to_add)

        elif dict_of_methods['thesaurus'] == True:
            doc_query_app = self.finished_dict(query, inverted_index) #  first parse query words
            list_of_query = list(doc_query_app.keys())
            words_to_add = {}
            # get each query word its synonyms and add to query the first that is in inverted index
            stop = set(stopwords.words('english'))
            results = [thes.synonyms(i, fileid="simN.lsp") for i in list_of_query if i not in stop]
            results_as_list = list(results)
            for words in results_as_list:
                inside_list = list(words)
                if len(inside_list) == 0:
                    continue
                idx = 0
                while idx < len(inside_list):
                    if inside_list[idx] in doc_query_app.keys() or inside_list[idx] in words_to_add.keys():
                        idx += 1
                        continue
                    tested = self._indexer.check_upper_lower(inverted_index, inside_list[idx])
                    if tested[1] is False or tested[0] in doc_query_app.keys() or tested[0] in words_to_add.keys():
                        idx += 1
                        continue
                    if tested[1] is True:
                        words_to_add[tested[0]] = 0.0001
                        break
                    elif tested[1] is 'replace':
                        words_to_add[tested[0].upper()] = 0.0001
                        break
                    idx += 1
            doc_query_app.update(words_to_add)

        else:  # dict_of_methods['parser'] = True
            doc_query_app = self.finished_dict(query, inverted_index)

        if len(doc_query_app) == 0:
            return []

        dict_relevant_docs = self._relevant_docs_from_posting(doc_query_app, posting)
        ranked_doc_ids = Ranker.rank_relevant_docs(dict_relevant_docs , posting, documents, doc_query_app)
        n_relevant = len(ranked_doc_ids)
        return n_relevant, ranked_doc_ids

    # feel free to change the signature and/or implementation of this function
    # or drop altogether.

    def finished_dict(self, query, inverted_index):
        # parse query
        query_as_list = self._parser.parse_sentence(query)  # output : [[terms] , {entity: num of shows}]
        new_query_list = []
        for term in query_as_list[0]:
            if term in inverted_index:
                new_query_list.append(term)
                continue
            term_to_add = self._indexer.check_upper_lower(inverted_index, term)
            "------handle upper and lower cases of query-----"
            if term_to_add[1] is True:
                new_query_list.append(term_to_add[0])
            elif term_to_add[1] == 'replace':
                new_query_list.append(term_to_add[0].upper())

        temp_entity_dict = {}
        for entity in query_as_list[1]:
            if entity in inverted_index:
                temp_entity_dict[entity] = query_as_list[1][entity]

        query_as_list[0] = new_query_list
        query_as_list[1] = temp_entity_dict

        "------calculate words from query wiq------"
        doc_query_app = {}
        for term in query_as_list[0]:
            if term not in doc_query_app:
                doc_query_app[term] = 1
            else:
                doc_query_app[term] += 1

        for entity in query_as_list[1].keys():
            if entity not in doc_query_app:
                doc_query_app[entity] = 1
            else:
                doc_query_app[entity] += 1
        return doc_query_app


    def _relevant_docs_from_posting(self, all_terms, posting):
        """
        This function loads the posting list and count the amount of relevant documents per term.
        :param query_as_list: parsed query tokens
        :return: dictionary of relevant documents mapping doc_id to document frequency.
        """
        if len(all_terms) == 0: #if empty
            return {}

        all_terms_in_same_file = []
        relevant_docs = {}

        for term in all_terms.keys():
            relevant_docs[term] = posting[term]['tf']

        return relevant_docs

# you can change whatever you want in this module, just make sure it doesn't 
# break the searcher module
from math import sqrt
from spellchecker import SpellChecker
from nltk.corpus import wordnet


class Ranker:
    def __init__(self):
        pass

    @staticmethod
    def rank_relevant_docs(relevant_docs, posting, documents, doc_query_appear, k=None):
        """
        This function provides rank for each relevant document and sorts them by their scores.
        The current score considers solely the number of terms shared by the tweet (full_text) and query.
        :param k: number of most relevant docs to return, default to everything.
        :param relevant_docs: dictionary of documents that contains at least one term from the query.
        :return: sorted list of documents by score
        """
        "----------------------get parameters for calculate------------------------------"

        fqd = {}
        ktemp = 2
        btemp = 0.3

        similarity_dict_of_docs = {}

        for term in relevant_docs.keys():
            for tweet in posting[term]['tf'].keys():
                "-------------calculate bm25------------------"
                cwq = doc_query_appear[term]
                cwd = relevant_docs[term][tweet][0]
                doc_size = documents[tweet]['length']
                avg_doc_size = documents['-average-']
                term_idf = posting[term]['idf']
                if tweet not in fqd.keys():
                    fqd[tweet] = cwq * (((ktemp + 1) * cwd) / (cwd + ktemp * (1 - btemp + btemp * (doc_size / avg_doc_size)))) * term_idf
                else:
                    fqd[tweet] += cwq * (((ktemp + 1) * cwd) / (cwd + ktemp * (1 - btemp + btemp * (doc_size / avg_doc_size)))) * term_idf

                "---------------calculate cossimilarity-----------------"

                wij_of_tweet = documents[tweet]['w_ij']
                wij_single_term = posting[term]['tf'][tweet][1]
                wiq_single_term = doc_query_appear[term]
                wiq_for_sigma = ((doc_query_appear[term]) ** 2)

                if tweet not in similarity_dict_of_docs.keys():
                    similarity_dict_of_docs[tweet] = [0, 0, 0]
                    similarity_dict_of_docs[tweet][0] = wij_single_term * wiq_single_term  # sigma of wij and wiq
                    similarity_dict_of_docs[tweet][1] = wij_of_tweet  # update only once
                    similarity_dict_of_docs[tweet][2] = wiq_for_sigma

                else:
                    similarity_dict_of_docs[tweet][0] += wij_single_term * wiq_single_term  # sigma of wij and wiq
                    similarity_dict_of_docs[tweet][2] += wiq_for_sigma

            "----------------------ranking docs by cos simality and bm25---------------------"
        score_dict_relevant_docs = {}
        for document in similarity_dict_of_docs:
            sigma_ij_iq = similarity_dict_of_docs[document][0]
            sigma_ij_power = similarity_dict_of_docs[document][1]
            sigma_iq_power_query = similarity_dict_of_docs[document][2]
            similarity = sigma_ij_iq / sqrt(sigma_iq_power_query * sigma_ij_power)
            # the similarity is effected by both cossim and bm25
            score_dict_relevant_docs[document] = (similarity * 0.10) + (fqd[document] * 0.90)

        ranked_results = dict(sorted(score_dict_relevant_docs.items(), key=lambda item: item[1], reverse=True))
        max_val = list(ranked_results.values())[0]
        # take only the document that their similarity is bigger them 1/5 of the bigest similarity
        ranked_results = {key: value for key, value in ranked_results.items() if value >= max_val/5}
        ranked_results = list(ranked_results.keys())
        if k is not None:
            ranked_results = ranked_results[:k]
        return ranked_results

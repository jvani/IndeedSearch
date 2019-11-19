# -*- coding: utf-8 -*-
import re
import nltk
import string
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from lxml import html as lhtml
from nltk.corpus import stopwords
from elasticsearch import Elasticsearch

plt.style.use("ggplot")


class DegreeList:
    url  = "https://en.wikipedia.org/wiki/List_of_tagged_degrees"
    resp = requests.get(url)
    tree = lhtml.fromstring(resp.content)
    # -- Get a unique list of degree names.
    degrees = np.unique(
        [ii for ii in
            [
                # -- Take the last str after 'of' or 'in'.
                re.split(" of | in ", "".join(ii.xpath(".//text()")))[-1]
                # -- For each li object (i.e., degree listing). 
                for ii in tree.xpath(
                    "//div[@class='mw-parser-output']" + 
                    "//li[not(contains(@class, 'toclevel'))]"
                ) 
            ] if ii not in ["Science", "Theory", "Teaching", "Business"]
        ]
    ).tolist()[5:]


class ProgrammingLanguages:
    url = "https://en.wikipedia.org/wiki/List_of_programming_languages"
    resp = requests.get(url)
    tree = lhtml.fromstring(resp.content)
    langs = [
        re.sub(' \(.*?\)','', language) for language in 
        tree.xpath("//div[@class='div-col columns column-width']//li/a/text()")
    ]


class IndeedData:
    def __init__(self, nrecords=1000):
        self.es = Elasticsearch()
        self.results = self.es.search("indeed", size=1000)
        self.data = [hit["_source"] for hit in self.results["hits"]["hits"]]
        self.df = pd.DataFrame(self.data)

    @classmethod
    def in_sentence(cls, words, sentence):
        """"""
        for word in words:
            if word in sentence:
                return True
        return False

    @classmethod
    def wordize(cls, text):
        excl = stopwords.words("english") + list(string.punctuation)
        return [word for word in nltk.word_tokenize(text) if word not in excl]

    def find_programming_languages(self, languages):
        """"""
        self.df["ProgrammingLanguages"] = self.df.Description.apply(
            lambda x: np.array(languages)[np.isin(languages, nltk.word_tokenize(x))].tolist()
        )

    def plot_programming_languages(self, q=0.7):
        """"""
        languages = [ii for sublist in self.df.ProgrammingLanguages for ii in sublist]
        values = pd.value_counts(languages)
        values[values > values.quantile(q)].sort_values().plot(kind="barh", color="#E24A33")
        plt.show()

    def find_degrees(self, degrees):
        """"""
        degree_qualifiers = [
            "degree", "graduate", "bachelor", "bachelors",
            "bsc", "ms", "m.s", "phd", "b.sc"
        ]

        self.df["Degrees"] = self.df.Description.apply(
            lambda x: np.array(degrees)[
            np.isin(degrees, nltk.word_tokenize(
                " ".join(
                    [
                        sentence for sentence in nltk.sent_tokenize(x) 
                        if self.in_sentence(degree_qualifiers, sentence)
                    ]
                )
            )
        )].tolist()
        )

    def plot_degrees(self, q=0.7):
        """"""
        degrees = [ii for sublist in self.df.Degrees for ii in sublist]
        values = pd.value_counts(degrees)
        subset = values[values > values.quantile(q)].sort_values()
        subset.plot(kind="barh", color="#E24A33")
        plt.show()

    def find_skills(self):
        """"""
        skill_qualifiers = [
            "ability", "skill", "experience", "qualified", "capable",
            "background"
        ]

        self.df["skills"] = self.df.Description.apply(
            lambda x: 
            self.wordize(
                " ".join(
                    [
                        sentence for sentence in nltk.sent_tokenize(x)
                        if self.in_sentence(skill_qualifiers, sentence)
                    ]
                )
            )
        )

    def plot_skills(self, q=0.7):
        """"""
        skills = [ii for sublist in self.df.skills for ii in sublist]
        values = pd.value_counts(skills)
        subset = values[values > values.quantile(q)].sort_values()
        subset.plot(kind="barh", color="#E24A33")
        plt.show()




import re

from nltk.stem.snowball import SnowballStemmer

from russian_extrac_configs import russian_stop_words, punctuation


class InvertedIndex:
    SPLITTER = re.compile(r"\b\S+\b")

    def __init__(self):
        self.index = {}
        self.stemmer = SnowballStemmer("russian")

    # (count of occurrences, dict_of_documents)
    def add(self, stemmed_word, message_id, channel):
        if stemmed_word in self.index:
            item = self.index[stemmed_word][0]
            self.index[stemmed_word][1] += 1
            if (message_id, channel) in item:
                item[(message_id, channel)] += 1
            else:
                item[(message_id, channel)] = 1
        else:
            self.index[stemmed_word] = [{(message_id, channel): 1}, 1]

    def replace_punctuation(sentence: str):
        res = sentence
        for punc in punctuation:
            res = res.replace(punc, " ")
        return res

    def enrich_words_set(self, word_list, doubled=True):
        doubledWords = set()
        if doubled:
            for i in range(len(word_list)):
                if len(word_list[i]) <= 3: continue
                for j in range(max(0, i - 1), min(len(word_list), i + 2)):
                    if i == j: continue
                    if len(word_list[j]) <= 3: continue
                    doubledWords.add(word_list[j] + word_list[i])
                    doubledWords.add(word_list[i] + word_list[j])
        return word_list + list(doubledWords)

    def process_text(self, sentence: str):
        processed_sentence = InvertedIndex.replace_punctuation(sentence)
        words = re.findall(InvertedIndex.SPLITTER, processed_sentence)
        words_set = self.enrich_words_set([self.stemmer.stem(word.lower()) for word in words if word not in russian_stop_words])
        return words_set



    # rows = [[sentence, message_id, channel]]
    def create_index(self, rows):
        for row in rows:
            text = row[0]
            message_id = row[1]
            channel = row[2]
            words = self.process_text(text)
            for word in words:
                self.add(
                    stemmed_word=word,
                    message_id=message_id,
                    channel=channel
                )

    def search_phrase(self, query, limit=3):
        query_words = self.process_text(query)
        result = {}
        for word in query_words:
            if word in self.index:
                messages = self.index[word][0]
                count = self.index[word][1]
                for message in messages.keys():
                    if message in result:
                        result[message] += messages[message] / float(count)
                    else:
                        result[message] = messages[message] / float(count)
        result = sorted(result.items(), key=lambda x: x[1], reverse=True)[:limit]
        return result

# index = InvertedIndex()
# rows = [
#     ["Григорий пошёл домой на селиваново!", "1", "канал1"],
#     ["Григорий пошёл домой на селиваново!", "1", "канал2"],
#     ["Иванов пошёл домой на селиваново!", "2", "канал2"],
#     ["Дрозды летели низко, но это хорошо!", "4", "канал1"],
# ]
# index.create_index(rows)
#
# print(index.search_phrase("Дрозды пошёл"))
#
# print(index.index)

from nltk.stem.snowball import SnowballStemmer

from russian_extrac_configs import russian_stop_words, punctuation


class InvertedIndex:

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

    def process_sentence(self, sentence: str):
        processed_sentence = InvertedIndex.replace_punctuation(sentence)
        words = processed_sentence.split(" ")
        words = [self.stemmer.stem(word) for word in words if word not in russian_stop_words]
        return words

    # rows = [[sentence, message_id, channel]]
    def create_index(self, rows):
        for row in rows:
            sentence = row[0]
            message_id = row[1]
            channel = row[2]
            words = self.process_sentence(sentence)
            for word in words:
                self.add(
                    stemmed_word=word,
                    message_id=message_id,
                    channel=channel
                )

    def search_phrase(self, query, limit=3):
        query_words = self.process_sentence(query)
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

from nltk.stem.snowball import SnowballStemmer

from russian_extrac_configs import russian_stop_words, punctuation


class InvertedIndex:

    def __init__(self):
        self.index = {}
        self.stemmer = SnowballStemmer("russian")

    # (count of occurrences, dict_of_documents)
    def add(self, not_stemmed_word, message_id, channel):
        stemmed_word = self.stemmer.stem(not_stemmed_word)
        if stemmed_word in self.index:
            item = self.index[stemmed_word]
            if (message_id, channel) in item:
                item[(message_id, channel)] += 1
            else:
                item[(message_id, channel)] = 1
        else:
            self.index[stemmed_word] = {(message_id, channel): 1}


    def replace_punctuation(sentence: str):
        res = sentence
        for punc in punctuation:
            res = res.replace(punc, " ")
        return res

    def process_sentence(sentence : str):
        processed_sentence = InvertedIndex.replace_punctuation(sentence)
        words = processed_sentence.split(" ")
        words = [word for word in words if word not in russian_stop_words]
        return words

    # rows = [[sentence, message_id, channel]]
    def create_index(self, rows):
        for row in rows:
            sentence = row[0]
            message_id = row[1]
            channel = row[2]
            words = InvertedIndex.process_sentence(sentence)
            for word in words:
                self.add(
                    not_stemmed_word=word,
                    message_id=message_id,
                    channel=channel
                )

# index = InvertedIndex()
# rows=[
#     ["Григорий пошёл домой на селиваново!","1","первый"],
#     ["Григорий пошёл домой на селиваново!","1","второй"],
#     ["Иванов пошёл домой на селиваново!","3","второй"],
# ]
# index.create_index(rows)
#
# print(index.index)
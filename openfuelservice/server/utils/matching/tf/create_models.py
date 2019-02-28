import json
import os
import pickle
import random
import time
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path, PosixPath

import nltk
import numpy as np
import tensorflow as tf
import tflearn
from tflearn import DNN
from tqdm import tqdm

from openfuelservice.server import file_folder, ann_settings, ofs_settings, car_brands, verbose
from openfuelservice.server.utils.database.queries import Wikipedia
from openfuelservice.server.utils.misc.data_handling import powerset, get_positive_brand_intents
from openfuelservice.server.utils.misc.file_management import delete_file

word_list_en_path = file_folder.joinpath(ann_settings['word_lists']['en'])
word_list_de_path = file_folder.joinpath(ann_settings['word_lists']['de'])
_wordlist_en = None
cpu = ofs_settings['general']['cpu']
manufacturer_aliases = car_brands['aliases']
if not verbose:
    tf.logging.set_verbosity(tf.logging.ERROR)


def preprocess_remove_list(remove_list, manufacturer):
    return {x.replace(manufacturer, '').replace(manufacturer.casefold(), '') for x in remove_list}


def preprocess_training_data(brand: str, class_limit: int = None, manufacturer_cars: dict() = None,
                             max_sentence: int = None, remove_list: [] = None, manual_intents_marker: bool = True,
                             wiki_pages: bool = True, intent_cars_only: bool = False):
    intents = {}
    training_data = []
    carcounter = 0
    car: str
    manual_intents = {}
    manual_intents = get_positive_brand_intents(brand_name_or_path=brand)
    for car in manufacturer_cars:
        if class_limit != None and carcounter > class_limit:
            break
        carcounter += 1
        other_tags = [k.replace(brand, '').strip() for k in manufacturer_cars.keys() if k != car]
        car_data = {}
        patterns = []
        brand_aliases: [] = []
        wiki_name = manufacturer_cars[car].wiki_name
        manual_car_intents = None
        tag_name = wiki_name
        car_data['tag'] = tag_name
        car_name = manufacturer_cars[car].car_name
        patterns.append(tag_name)
        patterns.append(tag_name.casefold())
        patterns.append(tag_name.title())
        patterns.append(car_name)
        patterns.append(car_name.casefold())
        patterns.append(car_name.title())
        # tag_name_words = nltk.word_tokenize(tag_name)
        # tag_name_powerset = powerset(tag_name_words)
        # tag_name_powerset = [power for power in tag_name_powerset if
        #                      power != brand or power.casefold() != brand.casefold()]
        # tag_name_powerset_lower = [power.casefold() for power in tag_name_powerset]
        # [patterns.append(power) for power in tag_name_powerset]
        # [patterns.append(power) for power in tag_name_powerset_lower]
        if brand in manufacturer_aliases:
            brand_aliases.extend(manufacturer_aliases[brand])
        if manual_intents_marker and manual_intents is not None:
            for intent in manual_intents['intents']:
                if intent['tag'] == wiki_name:
                    print("Using manual intents for car:", wiki_name)
                    manual_car_intents = intent['patterns']
        if manual_car_intents is not None:
            for intent in manual_car_intents:
                intent_words = nltk.word_tokenize(intent)
                intent_powerset = powerset(intent_words)
                intent_powerset = [power for power in intent_powerset if
                                   power != brand or power.casefold() != brand.casefold()]
                intent_powerset_lower = [word.casefold() for word in intent_powerset]
                [patterns.append(power) for power in intent_powerset]
                [patterns.append(power) for power in intent_powerset_lower]
                patterns.append(intent)
                patterns.append(intent.casefold())
                patterns.append(intent.title())
        if manual_car_intents is None and wiki_pages is False:
            pass
        elif wiki_pages:
            car_text: str = manufacturer_cars[car].page_text
            if type(car_text) != str:
                sentences: list = ['']
            else:
                sentences: list = nltk.sent_tokenize(car_text)
            for alias in brand_aliases:
                pattern_words_combined = "".join(alias).join(car_name)
                patterns.append(pattern_words_combined)
                patterns.append(pattern_words_combined.capitalize())
                patterns.append(pattern_words_combined.title())
            sentence_counter = 0
            sentences_length: int = len(sentences)
            for sentence in sentences:
                if sentence_counter >= sentences_length - 1 or max_sentence is not None and sentence_counter >= max_sentence:
                    break
                else:
                    cleaned_sentences = check_sentence(sentence=sentence, model_name=car, remove_list=remove_list,
                                                       other_tags=other_tags)
                    sentence_counter += 1
                    [patterns.append(cleaned_sentence.replace(brand, '').replace(brand.casefold(), '')) for
                     cleaned_sentence in cleaned_sentences]
            if sentence_counter == 0:
                sub_counter = 0
                break_counter = (len(sentences) / 100) * 10
                for sentence in sentences:
                    if sub_counter >= break_counter:
                        break
                    else:
                        patterns.append(sentence.replace(brand, '').replace(brand.casefold(), ''))
        if len(patterns) > 0:
            if intent_cars_only and manual_car_intents is None:
                pass
            else:
                patterns = sorted(list(set(patterns)))
                car_data['patterns'] = patterns
                training_data.append(car_data)
    intents['intents'] = training_data
    with open(file_folder.joinpath('models').joinpath("{}_intents.json".format(brand)), "w") as outfile:
        json.dump(intents, outfile)
    return intents


def train(train_x, train_y, model_name, words, classes, n_epoch=1000, batch_size=16, activation='softmax'):
    os.chdir(file_folder.joinpath('models'))
    # reset underlying graph data
    tf.reset_default_graph()
    # Build neural network
    net = tflearn.input_data(shape=[None, len(train_x[0])])
    net = tflearn.fully_connected(net, 8)
    net = tflearn.fully_connected(net, 8)
    net = tflearn.fully_connected(net, len(train_y[0]), activation)
    net = tflearn.regression(net)

    # Define model and setup tensorboard
    model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
    # Start training (apply gradient descent algorithm)
    model.fit(train_x, train_y, n_epoch=n_epoch, batch_size=batch_size, show_metric=True, run_id=model_name)
    tflearn_model = Path.cwd().joinpath('{}_model.tflearn'.format(model_name))
    tf_training_data = Path.cwd().joinpath("{}_tf_training_data".format(model_name))
    delete_file(file=tflearn_model)
    delete_file(file=tf_training_data)
    model.save(tflearn_model.name)
    pickle.dump({'words': words, 'classes': classes, 'train_x': train_x, 'train_y': train_y},
                open(tf_training_data, "wb"))


def clean_up_sentence(sentence):
    # tokenize the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [word.casefold() for word in sentence_words]
    return sentence_words


def hasNumbers(inputString) -> bool:
    return any(char.isdigit() for char in inputString)


def check_sentence(sentence, model_name, remove_list: [] = None, other_tags: [] = None) -> []:
    whitelist = ['model', 'type', 'typ', 'generation']
    sentence_words = nltk.word_tokenize(sentence)
    model_name_words = nltk.word_tokenize(model_name)
    model_name_words_lower = [word.casefold() for word in model_name_words]

    if remove_list != None:
        for element in remove_list:
            # Remove model name words from element
            for word in model_name_words:
                element.replace(word, '').strip()
            for word in model_name_words:
                element.replace(word.casefold(), '').strip()
        for element in remove_list:
            if element in sentence_words:
                sentence_words.remove(element)
            elif element.casefold() in sentence_words:
                sentence_words.remove(element.casefold())

    if other_tags != None:
        for word in model_name_words:
            for other_tag in other_tags:
                if word == other_tag or word.casefold() == other_tag.casefold():
                    other_tags.remove(other_tag)
                if other_tag == model_name or other_tag.casefold() == model_name.casefold():
                    other_tags.remove(other_tag)
        for other_tag in other_tags:
            if other_tag in sentence_words:
                sentence_words.remove(other_tag)
            elif other_tag.casefold() in sentence_words:
                sentence_words.remove(other_tag.casefold())

    sentence_lower_words = [word.casefold() for word in sentence_words]
    for word in model_name_words:
        if word in sentence_words or word in sentence_lower_words:
            return ["".join(sentence_words), "".join(sentence_lower_words)]
    for word in model_name_words_lower:
        if word in sentence_words or word in sentence_lower_words:
            return ["".join(sentence_words), "".join(sentence_lower_words)]
    for word in whitelist:
        if word in sentence_words or word in sentence_lower_words:
            return ["".join(sentence_words), "".join(sentence_lower_words)]
    if hasNumbers(inputString=sentence):
        return ["".join(sentence_words), "".join(sentence_lower_words)]
    return []


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=False):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)

    return (np.array(bag))


def load_wordlist(text_file) -> dict():
    with open(text_file, 'r') as tf:
        lines = dict()
        read_lines = tf.readlines()
        for line in read_lines:
            line = line.rstrip('\n').strip().casefold()
            lines[line] = ""
        return lines


def check_wordlist(word, wordlist) -> bool:
    word_lower = word.casefold().strip()
    if word in wordlist:
        return True
    elif word_lower in wordlist:
        return True
    else:
        return False


class ManufacturerANNModel(object):

    # https://machinelearnings.co/text-classification-using-neural-networks-f5cd7b8765c6
    # TODO add a check where the amount of classes is compared with the synapses file. If different it will be recalculated.
    def __init__(self, manufacturer: str = None, class_limit: int = None, old_intents: PosixPath = None,
                 old_training_data: PosixPath = None, max_sentence: int = None, remove_list: [] = None,
                 manual_intents: bool = True, wiki_pages: bool = True, intent_cars_only: bool = False):
        self.brand = manufacturer
        self.manual_intents = manual_intents
        self.class_limit = class_limit
        self.intents = None
        self.intents_size = 0
        self.max_sentence = max_sentence
        self.classes_size = None
        self._wordlist_en: {} = None
        self._wordlist_de: {} = None
        self.manufacturer_cars: {}
        self.wiki_pages = wiki_pages
        self.manufacturer_cars: {} = Wikipedia().get_wikicar_page_texts(filter_brand=self.brand, ordered=True)
        self.training_data = None
        self.train_x = []
        self.train_y = []
        self.words = []
        self.classes = []
        self.documents = []
        self.ignore_words = ['?']
        self.training = list()
        self.output = []
        self.intent_cars_only = intent_cars_only

        self.remove_list = remove_list
        self.old_intents = old_intents
        self.old_training_data = old_training_data
        self.old_model = None
        self.tflearn_model: DNN = None
        self.net = None
        self.old_intents_size = None

    def load_old_data(self):
        if self.old_intents == None or self.old_training_data == None:
            print("No old training data")
            pass
        else:
            oi: PosixPath = self.old_intents
            otd: PosixPath = self.old_training_data
            try:
                if type(oi) == PosixPath:
                    oi: dict = json.load(open(oi.absolute(), 'r'))
            except FileNotFoundError as err:
                print(err)
            try:
                if type(otd) == PosixPath:
                    otd: dict = pickle.load(open(otd.absolute(), "rb"))
            except FileNotFoundError as err:
                print(err)
            try:
                self.words = otd['words']
                self.classes = otd['classes']
                self.train_x = otd['train_x']
                self.train_y = otd['train_y']
                self.intents: list = oi['intents']
                self.intents_size = len(self.intents)
                self.old_intents_size = len(oi['intents'])
            except KeyError as err:
                print(err)
            self.load_tflearn_model()
            return self

    def load_tflearn_model(self, activation='softmax'):
        # reset underlying graph data
        if self.tflearn_model != None:
            pass
        else:
            try:
                tf.reset_default_graph()
                net = tflearn.input_data(shape=[None, len(self.train_x[0])])
                net = tflearn.fully_connected(net, 8)
                net = tflearn.fully_connected(net, 8)
                net = tflearn.fully_connected(net, len(self.train_y[0]), activation)
                net = tflearn.regression(net)
                self.tflearn_model: DNN = tflearn.DNN(net)
                tflearn_model_path = file_folder.joinpath('models')
                os.chdir(tflearn_model_path)
                self.tflearn_model.load('{}_model.tflearn'.format(self.brand))
            except Exception as err:
                print("Couldn't load tflearn model")
                print(err)

    def check_data_actuality(self) -> bool:
        if self.old_intents_size is not None and self.tflearn_model is not None and self.intents is not None and self.old_intents_size == self.intents_size:
            self.manufacturer_cars.clear()
            return True
        else:
            return False

    def train_model(self, advanced_remove_list: bool = False):
        start_time = time.time()
        self.wordlist_en: dict = load_wordlist(word_list_en_path)
        self.wordlist_de: dict = load_wordlist(word_list_de_path)
        # TODO Is this still necessary?
        if advanced_remove_list:
            self.remove_list += preprocess_remove_list(remove_list=self.manufacturer_cars, manufacturer=self.brand)
        self.training_data = preprocess_training_data(brand=self.brand, class_limit=self.class_limit,
                                                      manufacturer_cars=self.manufacturer_cars,
                                                      max_sentence=self.max_sentence, remove_list=self.remove_list,
                                                      manual_intents_marker=self.manual_intents,
                                                      wiki_pages=self.wiki_pages,
                                                      intent_cars_only=self.intent_cars_only)
        self.organize_data()
        if self.check_data_actuality():
            self.manufacturer_cars.clear()
            print("Model is up to date!")
            pass
        elif len(self.manufacturer_cars) == 0 or len(self.training_data['intents']) <= 0:
            print("No training data in database skip model for", self.brand)
            pass
        else:
            train(train_x=self.train_x, train_y=self.train_y, model_name=self.brand, words=self.words,
                  classes=self.classes)
            elapsed_time = time.time() - start_time
            print("processing time:", elapsed_time, "seconds")

    def classify(self, car_name, ERROR_THRESHOLD: float = 0.25) -> []:
        if self.tflearn_model == None:
            print("tflearn model not loaded!")
            pass
        else:
            # generate probabilities from the model
            results = self.tflearn_model.predict([bow(car_name, self.words)])[0]
            # filter out predictions below a threshold
            results = [[i, r] for i, r in enumerate(results) if r > ERROR_THRESHOLD]
            # sort by strength of probability
            results.sort(key=lambda x: x[1], reverse=True)
            return_list = []
            for r in results:
                return_list.append((self.classes[r[0]], r[1]))
            # return tuple of intent and probability
            return return_list

    def organize_data(self):
        if len(self.training_data['intents']) > 0:
            for intent in self.training_data['intents']:
                tag_name = intent['tag']
                for pattern in intent['patterns']:
                    # tokenize each word in the sentence
                    words = nltk.word_tokenize(pattern)
                    # Delete most common words
                    # add to our words list
                    self.words.extend(words)
                    # add to documents in our corpus
                    self.documents.append((words, intent['tag']))
                    # add to our classes list
                    if intent['tag'] not in self.classes:
                        self.classes.append(intent['tag'])
            self.words = [w.casefold() for w in self.words if
                          w not in self.ignore_words or w.casefold() not in self.ignore_words]
            self.words = sorted(list(set(self.words)))
            # remove duplicates
            self.classes = sorted(list(set(self.classes)))
            # create our training data
            # create an empty array for our output
            output_empty = [0] * len(self.classes)

            # training set, bag of words for each sentence
            for doc in self.documents:
                # initialize our bag of words
                bag = []
                # list of tokenized words for the pattern
                pattern_words = doc[0]
                # stem each word
                pattern_words = [word.casefold() for word in pattern_words]
                # create our bag of words array
                for word in self.words:
                    bag.append(1) if word in pattern_words else bag.append(0)

                # output is a '0' for each tag and '1' for current tag
                output_row = list(output_empty)
                output_row[self.classes.index(doc[1])] = 1
                self.training.append([bag, output_row])
            print('\nStatistics for manufacturer', self.brand)
            print(len(self.training_data['intents']), "Manufacturer Cars")
            print(len(self.documents), "documents")
            print(len(self.classes), "classes")
            print(len(self.words), "unique stemmed words")
            # shuffle our features and turn into np.array
            random.shuffle(self.training)
            self.training = np.array(self.training)
            self.train_x = list(self.training[:, 0])
            self.train_y = list(self.training[:, 1])

    def clear(self):
        self.words = None
        self.train_x = None
        self.train_y = None
        self._wordlist_en = None
        self._wordlist_de = None
        self.manufacturer_cars = None
        self.training_data = None
        self.tflearn_model: DNN = None
        self.net = None


class ManufacturerANNModelCollection(object):
    def __init__(self):
        self.loaded_models = dict()
        self._models = dict()
        self._models['intents'] = dict()
        self._models['training_data'] = dict()

    def initialize_models(self, model_names: [] = None):
        if model_names != None and len(model_names) > 0:
            for model_name in model_names:
                if model_name in self._models['intents']:
                    if model_name in self._models['training_data']:
                        self.loaded_models[model_name] = ManufacturerANNModel(manufacturer=model_name,
                                                                              old_intents=self._models['intents'][
                                                                                  model_name],
                                                                              old_training_data=
                                                                              self._models['training_data'][
                                                                                  model_name]).load_old_data()

    def load_models(self, model_name: str = None):
        model_path: Path = file_folder.joinpath('models')
        training_files = list(model_path.glob('*_tf_training_data'))
        intents_files = list(model_path.glob('*_intents.json'))
        if model_name == None:
            for file in training_files:
                model_name = file.name[:-len('_tf_training_data')]
                self._models['training_data'][model_name] = file.absolute()
            for file in intents_files:
                model_name = file.name[:-len('_intents.json')]
                self._models['intents'][model_name] = file.absolute()
        else:
            for file in training_files:
                if model_name in file.name:
                    self._models['training_data'][model_name] = file.absolute()
            for file in intents_files:
                if model_name in file.name:
                    self._models['intents'][model_name] = file.absolute()
        return self

    def create_models(self, class_limit: int = None, manufacturers: list = None, max_sentence=None,
                      manual_intents: bool = True, wiki_pages: bool = True, intent_cars_only: bool = False):
        if len(manufacturers) > 0:
            models_to_train = []
            for i in range(0, len(manufacturers)):
                manufacturer = manufacturers[i]
                remove_list = [x for x in manufacturers if
                               x != manufacturer and x.casefold() != manufacturer.casefold()]

                test_model = False
                if manufacturer in self._models['intents'] and manufacturer in self._models['training_data']:
                    try:
                        model: ManufacturerANNModel = ManufacturerANNModel(manufacturer=manufacturer,
                                                                           old_intents=self._models['intents'][
                                                                               manufacturer],
                                                                           old_training_data=
                                                                           self._models['training_data'][
                                                                               manufacturer]).load_old_data()
                        test_model = model.check_data_actuality()
                        model.clear()
                    except Exception as err:
                        print(err)
                        pass
                if test_model:
                    pass
                else:
                    models_to_train.append(ManufacturerANNModel(manufacturer=manufacturer,
                                                                class_limit=class_limit,
                                                                max_sentence=max_sentence,
                                                                remove_list=remove_list,
                                                                manual_intents=manual_intents,
                                                                wiki_pages=wiki_pages,
                                                                intent_cars_only=intent_cars_only))
            if len(models_to_train) > 0:
                print("New models to train:", len(models_to_train))
                pool = ThreadPool(cpu)
                for _ in tqdm(pool.map(model_trainer, models_to_train), total=len(models_to_train),
                              unit=' Training Models MultiThreaded'):
                    pass
                pool.close()
                pool.join()

    def classify(self, manufacturer: str = None, car_name: str = None):
        if manufacturer in self.loaded_models:
            result = dict()
            model: ManufacturerANNModel = self.loaded_models[manufacturer]
            result[manufacturer] = model.classify(car_name=car_name)
            return result
        elif manufacturer is not None and manufacturer not in self.loaded_models:
            return []
        elif len(self.loaded_models) <= 0:
            return []
        else:
            result = dict()
            for manufacturer in self.loaded_models:
                model: ManufacturerANNModel = self.loaded_models[manufacturer]
                result[manufacturer] = model.classify(car_name=car_name)
            return result


def model_trainer(model: ManufacturerANNModel):
    model.train_model()

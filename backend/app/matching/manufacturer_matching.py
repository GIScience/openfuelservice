import asyncio
import logging
import pickle
from pathlib import Path
from typing import Dict, List

import nltk
import numpy as np
import tensorflow as tf
import tflearn

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    nltk.download("punkt")
except Exception:
    logger.warning(
        "Couldn't download nltk Punkt package. If the matching module is not used just ignore."
    )


def clean_up_sentence(sentence: str) -> List:
    # tokenize the pattern
    sentence_words: List = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [word.casefold() for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence: str, words: List, show_details: bool = False) -> np.ndarray:
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    logger.debug("found in bag: %s" % w)

    return np.array(bag)


class ManufacturerAnnModel:
    # https://machinelearnings.co/text-classification-using-neural-networks-f5cd7b8765c6
    def __init__(
        self,
        model_name: str,
        old_intents: Path,
        old_training_data: Path,
    ):
        self.model_name = model_name
        self._words: List[str] = []
        self._classes: List[str] = []
        self._old_intents: Path = old_intents
        self._old_training_data: Path = old_training_data
        self._tflearn_model: tflearn.DNN

    async def initialize_model(self) -> None:
        if not self._old_intents or not self._old_training_data:
            logger.warning(f"No training data found for modle {self.model_name}.")
            return
        if not isinstance(self._old_intents, Path) or not isinstance(
            self._old_training_data, Path
        ):
            logger.warning("Initialized training data initialized but not found.")
            return
        try:
            old_training_data: Dict = pickle.load(
                open(self._old_training_data.absolute(), "rb")
            )
        except FileNotFoundError as err:
            logger.warning(
                "Initialized training data initialized but couldn't be opened."
            )
            raise err
        try:
            self._words = old_training_data["words"]
            self._classes = old_training_data["classes"]
            train_x = old_training_data["train_x"]
            train_y = old_training_data["train_y"]
            tf.compat.v1.reset_default_graph()
            net = tflearn.input_data(shape=[None, len(train_x[0])])
            net = tflearn.fully_connected(net, 8)
            net = tflearn.fully_connected(net, 8)
            net = tflearn.fully_connected(net, len(train_y[0]), "softmax")
            net = tflearn.regression(net)
            self._tflearn_model = tflearn.DNN(net)
            self._tflearn_model.load(
                f"{settings.UNCOMPRESSED_MATCHING_DATA}/{self.model_name}_model.tflearn"
            )
        except KeyError as err:
            logger.error(
                f"Error loading the tensorflow files for model: {self.model_name}"
            )
            raise err

    async def classify(
        self, car_name: str, error_threshold: float = 0.25
    ) -> List[tuple]:
        if not isinstance(self._tflearn_model, tflearn.DNN):
            logger.info("Model not correctly loaded.")
            await self.initialize_model()
        # generate probabilities from the model
        results: List = self._tflearn_model.predict([bow(car_name, self._words)])[0]
        # filter out predictions below a threshold
        results = [[i, r] for i, r in enumerate(results) if r > error_threshold]
        # sort by strength of probability
        results.sort(key=lambda x: x[1], reverse=True)
        return_list: List[tuple] = []
        for r in results:
            return_list.append((self._classes[r[0]], r[1]))
        # return tuple of intent and probability
        return return_list


class ManufacturerAnnCollection:
    def __init__(self, models_path: str):
        self._models_path: Path = Path(models_path)
        self._loaded_models: Dict = {}
        self._models_intents: Dict[str, Path] = {}
        self._models_training_data: Dict[str, Path] = {}
        self._load_models()

    async def _initialize_models(self, model_names: List) -> None:
        logger.info(f"Initializing matching models for model names: {model_names}.")
        if model_names is None or not len(model_names):
            logger.warning("Can't initialize matching models. No models found.")
            return
        model_names = [
            model_name
            for model_name in model_names
            if model_name is not None and len(model_name)
        ]
        model_names = [
            model_name
            for model_name in model_names
            if self._models_intents.get(model_name)
            and self._models_training_data.get(model_name)
        ]
        models: List[ManufacturerAnnModel] = [
            ManufacturerAnnModel(
                model_name=model_name,
                old_intents=self._models_intents[model_name],
                old_training_data=self._models_training_data[model_name],
            )
            for model_name in model_names
        ]

        tasks = [
            asyncio.ensure_future(
                model.initialize_model()
            )  # creating task starts coroutine
            for model in models
        ]
        await asyncio.gather(*tasks)
        model: ManufacturerAnnModel
        for model in models:
            self._loaded_models[model.model_name] = model

    def _load_models(self) -> None:
        training_files: List = list(self._models_path.glob("*_tf_training_data"))
        intents_files: List = list(self._models_path.glob("*_intents.json"))
        for file in training_files:
            model_name = file.name[: -len("_tf_training_data")]
            self._models_training_data[model_name] = file.absolute()
        for file in intents_files:
            model_name = file.name[: -len("_intents.json")]
            self._models_intents[model_name] = file.absolute()

    async def classify(
        self,
        model_name: str = None,
        car_name: str = None,
        error_threshold: float = 0.25,
    ) -> List[tuple]:
        if not model_name or not car_name or not len(model_name) or not len(car_name):
            return []
        elif model_name not in self._loaded_models:
            await self._initialize_models([model_name])
        if model_name not in self._loaded_models:
            return []
        model: ManufacturerAnnModel = self._loaded_models[model_name]
        # TODO this will make more sense once multiple models need to be searched!
        result: List[tuple] = await model.classify(
            car_name=car_name, error_threshold=error_threshold
        )
        return result

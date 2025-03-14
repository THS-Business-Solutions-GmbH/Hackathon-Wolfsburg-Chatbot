from typing import List
import json
import os
import logging
import re

import chromadb
from flask import Flask, request, jsonify
from flask_cors import cross_origin
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.llms import ChatMessage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.mistralai import MistralAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from tokens import get_token_count

logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)

app = Flask(__name__)

vectordb = chromadb.PersistentClient(path="./chroma_db")

Settings.embed_model = HuggingFaceEmbedding(model_name="danielheinz/e5-base-sts-en-de", cache_folder="cache")
Settings.text_splitter = SentenceSplitter()


TOKEN_LIMIT = 32768


def extract_json(input_string):
    match = re.search(r'\{.*\}', input_string, re.DOTALL)
    return match.group(0) if match else None


class Client:
    def __init__(self):
        self.client = MistralAI(
            model="mistral-small-latest",
            max_tokens=1024,
        )

        self.history = [
            ChatMessage(role="system",
                        content="Du bist eine künstliche Intelligenz, die Bürger der Stadt Wolfsburg bei ihren Anliegen unterstützt."),
        ]

        self.database_02()

        self.retriever = self.vectordb.as_retriever(similarity_top_k=20)

    def load_json(file):
        with open(file, 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data

    def database_01(self):
        self.collection = vectordb.get_or_create_collection("wolfsburg")

        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=vector_store)

        if self.collection.count() == 0:
            # Create the database
            print("Loading documents")
            self._ingest("output.json")
        else:
            self.vectordb = VectorStoreIndex.from_vector_store(vector_store, storage_context=self.storage_context)

    def database_02(self):
        print("Creating database 02")
        self.collection = vectordb.get_or_create_collection("wolfsburg02")

        print("Loading vector store 02")
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("done")

        if self.collection.count() == 0:
            # Create the database
            print("Loading documents")
            self.full_documents = self._ingest_scraping()
        else:
            print("collection loaded")
            self.vectordb = VectorStoreIndex.from_vector_store(vector_store, storage_context=self.storage_context)

            with open("cache/full_index.json", "r", encoding="utf-8") as file:
                self.full_documents = json.load(file)
                print(
                    f"loaded full documents: {len(self.full_documents['files'].keys())} files and {len(self.full_documents['chunks'].keys())} chunks")

    def _ingest_scraping(self):
        documents = []
        full_documents = {"files": {}, "chunks": {}}
        index = 0;
        for filename in os.listdir("./scrape/wolfsburg.de/json"):
            print(f"processing {filename}")
            if not filename.endswith("json"):
                continue

            try:
                with open(os.path.join("./scrape/wolfsburg.de/json", filename), 'r', encoding="utf-8") as file:
                    data = json.load(file)
            except Exception as e:
                print(f"garbage in {filename}")
                print(e)
                continue

            for index, block in enumerate(data["blocks"]):
                content = block["content"]

                metadata = {
                    "index": str(index)
                }

                if "breadcrumbs" in block:
                    metadata["breadcrumbs"] = " ".join(block["breadcrumbs"])

                doc = Document(
                    text=content,
                    metadata=metadata
                )

                documents.append(doc)
                full_documents["chunks"][str(index)] = filename
                if filename not in full_documents["files"]:
                    full_documents["files"][filename] = data

        self.vectordb = VectorStoreIndex.from_documents(documents, storage_context=self.storage_context)

        with open("cache/full_index.json", "w", encoding="utf-8") as file:
            json.dump(full_documents, file)

        return full_documents

    def _ingest(self, fname):
        with open(fname, "r") as f:
            data = json.load(f)

        documents = []

        for path, text in data.items():
            documents.append(Document(text=text, metadata={"path": path}))

        self.vectordb = VectorStoreIndex.from_documents(documents, storage_context=self.storage_context)

    def generate_augment(self, filename):
        data = self.full_documents["files"][filename]

        headers = ""
        if "headers" in data:
            headers = f"Überschrift: {' '.join(data['headers'])}"

        keywords = ""
        if "keywords" in data:
            headers = f"Schlüsselwörter: {', '.join(data['keywords'])}"

        blocks = ""
        if "blocks" in data:
            blocks = "\n".join([b["content"] for b in data["blocks"]])

        links = ""
        if "links" in data:
            links = "\n".join([
                f"Quelle dieser Seite mit Sprache '{k}': {v}" for k, v in data["links"].items()
            ])

        augment = f"""
{headers}
{keywords}
{blocks}

{links}
        """

        _logger.info(f"Using {len(augment)} chars from document {filename}")

        return augment

    def documents_to_context(self, documents: List[Document], k: int):
        doc_count = {}
        for d in documents:
            index = str(d.node.metadata["index"])
            filename = self.full_documents["chunks"][str(index)]
            if filename in doc_count:
                doc_count[filename] += 1
            else:
                doc_count[filename] = 1

        top_k_keys = sorted(doc_count, key=doc_count.get, reverse=True)[:k]

        return "\n\n".join([self.generate_augment(filename) for filename in top_k_keys])

    def chat(self, message: str, language: str) -> dict:
        documents = self.retriever.retrieve(message)
        _logger.info(f"{len(documents)=}")

        context = self.documents_to_context(documents, 3)

        _logger.info(f"{len(context)=}")

        attempts = 0
        while attempts < 3:
            prompt = f"""Hier sind relevante Dokumente des Bürgerservices der Stadt Wolfsburg:

{context}

Nutze nur die Informationen aus diesen Dokumenten, um die folgende Anfrage zu beantworten. Gib dabei Kontextinformationen an und verweise auf die relevante Seite in der Sprache der Anfrage sofern vorhanden:

Anfrage:

{message}

Bitte gib deine Antwort im JSON-Format zurück, mit dem Key "content" für den vollständigen und in sich abgeschlossenen Antworttext.
Falls nötig dem optionalen Key "href" für einen Link und dem optionalen Key "address" für eine Adresse bestehend aus Straße, Hausnummer und Stadt (zB. "Schillerstraße 10, Wolfsburg"), als einzelner String. Rathaus ist keine Straße.

Bitte gib die Antwort in folgender Sprache aus: {language}"""

            self.history.append(ChatMessage(role="user", content=prompt))

            token_count = get_token_count(self.history)
            if token_count < TOKEN_LIMIT:
                break

            attempts += 1
            # Heuristic to reduce size of prompt in relation to how far we are above the limit
            reduce = max(100, int((len(context) - len(context) * TOKEN_LIMIT / token_count) + 100))

            _logger.warning(f"Prompt too big ({len(context)} chars, {token_count} tokens). Reducing by {reduce} chars.")
            context = context[reduce:]

            del self.history[-1]

        response = self.client.chat(self.history)

        text_result = response.message.content

        try:
            json_result = json.loads(extract_json(text_result))
        except Exception as e:
            _logger.error(f"Error parsing JSON response: {text_result}")
            raise e

        if "content" not in json_result:
            _logger.error(f"No content tag in JSON response: {text_result}")
            raise e

        # Replace last message without documents to shorten context
        self.history[-1] = ChatMessage(role="user", content=message)

        self.history.append(ChatMessage(role="assistant", content=json_result["content"]))

        return json_result

    def summarize_notes(self, message: str, language: str) -> str:

        prompt = f"""Hier ist ein Chatverlauf zwischen einem Nutzer und dir:

        {message}

        Bitte fasse alle relevanten Informationen in einem Notiztext für den Nutzer zusammen.

        Bitte gib die Antwort in folgender Sprache aus: {language}"""

        prompt_msgs = [
            ChatMessage(role="system",
                        content="Du bist eine künstliche Intelligenz, die Bürger der Stadt Wolfsburg bei ihren Anliegen unterstützt."),
            ChatMessage(role="user", content=prompt),
        ]

        response = self.client.chat(prompt_msgs)

        return response.message.content


client = Client()
ATTEMPTS = 3


@app.route('/', methods=['POST'])
@cross_origin()
def ai_response():
    data = request.json
    if data:
        _logger.info(f"Request: {data}")
        input_string = data['text']
        language = data['language']

        attempt = 0
        response = False
        while attempt < ATTEMPTS:
            try:
                response = client.chat(input_string, language)
                _logger.info(f"Response: {response}")
                break
            except Exception as e:
                _logger.warning(f"Request failed (Attempt {attempt}/{ATTEMPTS}): {e}")
                attempt += 1
                continue

        if not response:
            return jsonify({"error": "Error getting AI response"}), 500

        return jsonify(response)
    else:
        return jsonify({"error": "No input_string provided"}), 400


@app.route('/summarize_notes', methods=['POST'])
@cross_origin()
def ai_summarize_notes():
    data = request.json
    if data:
        _logger.info(f"Request Summarize Notes: {data}")
        input_history = data["history"]
        language = data['language']

        response = client.summarize_notes(input_history, language)

        _logger.info(f"Response: {response}")
        return jsonify(response)
    else:
        return jsonify({"error": "No input_string provided"}), 400


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()

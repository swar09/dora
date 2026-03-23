"""Sentence Transformers operator for dora-rs dataflow.

This operator uses the Sentence Transformers library to index and search
Python code files within a directory. It allows for semantic search over
the codebase by encoding files and queries into a vector space.
"""

import os
import sys

import pyarrow as pa
import torch
from dora import DoraStatus
from sentence_transformers import SentenceTransformer, util

SHOULD_BE_INCLUDED = [
    "webcam.py",
    "object_detection.py",
    "plot.py",
]


## Get all python files path in given directory
def get_all_functions(path):
    """
    Recursively discover and read specific Python files under a directory.
    
    Searches `path` for `.py` files, keeps only filenames listed in `SHOULD_BE_INCLUDED`, appends each file's directory to sys.path, reads the file contents as UTF-8, and returns the collected contents and their file paths.
    
    Parameters:
        path (str): Root directory to search.
    
    Returns:
        tuple: (raw, paths) where `raw` is a list of file contents (str) and `paths` is the corresponding list of full file paths (str).
    """
    raw = []
    paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                if file not in SHOULD_BE_INCLUDED:
                    continue
                path = os.path.join(root, file)
                with open(path, encoding="utf8") as f:
                    ## add file folder to system path
                    sys.path.append(root)
                    ## import module from path
                    raw.append(f.read())
                    paths.append(path)

    return raw, paths


def search(query_embedding, corpus_embeddings, paths, raw, k=5, file_extension=None):
    """
    Finds the top-k corpus documents most similar to a query embedding using cosine similarity.
    
    Parameters:
        query_embedding (Tensor): Embedding vector for the query.
        corpus_embeddings (Tensor): Embedding matrix for the corpus, aligned with `paths` and `raw`.
        paths (List[str]): File paths corresponding to each corpus embedding.
        raw (List[str]): Raw file contents corresponding to each corpus embedding.
        k (int): Maximum number of matches to return.
        file_extension (str, optional): Accepted for API compatibility but not used.
    
    Returns:
        List: Flattened list of matches in descending similarity; each match contributes
        `[content, path, score]`. The list length is 3 * number_of_matches_returned.
    """
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = torch.topk(cos_scores, k=min(k, len(cos_scores)), sorted=True)
    out = []
    for score, idx in zip(top_results[0], top_results[1]):
        out.extend([raw[idx], paths[idx], score])
    return out


class Operator:
    """Dora operator for semantic search over Python files."""

    def __init__(self):
        ## TODO: Add a initialisation step
        """
        Initialize operator state by loading the sentence transformer, discovering eligible Python files in the operator directory, and encoding their contents into embeddings.
        
        Stores discovered file contents in `self.raw`, their file paths in `self.path`, and the corresponding embeddings in `self.encoding`.
        """
        self.model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        self.encoding = []
        # file directory
        path = os.path.dirname(os.path.abspath(__file__))

        self.raw, self.path = get_all_functions(path)
        # Encode all files
        self.encoding = self.model.encode(self.raw)

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        """
        Handle incoming Dora events to run semantic queries or update indexed file contents.
        
        When `dora_event["type"] == "INPUT"` and `dora_event["id"] == "query"`, encodes the provided query strings, performs a cosine-similarity search against the stored corpus embeddings, and emits a single `"raw_file"` output record containing the matched file's raw content (`raw`), file path (`path`), and the original user query as `user_message`. For other `"INPUT"` events, treats the first element of `dora_event["value"]` as an updated file record, replaces the corresponding entry in the in-memory corpus (`self.raw`) and re-encodes that single document into `self.encoding`.
        
        Parameters:
            dora_event (dict): Dora event payload; expected shapes:
                - Query input: id == "query", value is an Arrow list of query strings, metadata forwarded to outputs.
                - Update input: value is an Arrow list where the first element is a dict with keys `"path"` and `"raw"`.
            send_output (Callable): Callback used to emit outputs in the form send_output(channel, arrow_array, metadata).
        
        Returns:
            DoraStatus: `DoraStatus.CONTINUE` to indicate the operator should continue running.
        """
        if dora_event["type"] == "INPUT":
            if dora_event["id"] == "query":
                values = dora_event["value"].to_pylist()

                query_embeddings = self.model.encode(values)
                output = search(
                    query_embeddings,
                    self.encoding,
                    self.path,
                    self.raw,
                )
                [raw, path, score] = output[0:3]
                send_output(
                    "raw_file",
                    pa.array([{"raw": raw, "path": path, "user_message": values[0]}]),
                    dora_event["metadata"],
                )
            else:
                input = dora_event["value"][0].as_py()
                index = self.path.index(input["path"])
                self.raw[index] = input["raw"]
                self.encoding[index] = self.model.encode([input["raw"]])[0]

        return DoraStatus.CONTINUE


if __name__ == "__main__":
    operator = Operator()

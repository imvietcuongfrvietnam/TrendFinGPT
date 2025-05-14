# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
import math

app = Flask(__name__)
CORS(app)

es = Elasticsearch("http://localhost:9200")

@app.route("/", methods=["GET"])
def list_docs():
    """
    GET /?page=1&size=20
    Returns all documents, paginated.
    """
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    start = (page - 1) * size

    body = {
      "query": {"match_all": {}},
      "from":  start,
      "size":  size
    }

    res   = es.search(index="vietnamnet", body=body)
    hits  = res["hits"]["hits"]
    total = (
      res["hits"]["total"]["value"]
      if isinstance(res["hits"]["total"], dict)
      else res["hits"]["total"]
    )

    docs = [{"id": hit["_id"], **hit["_source"]} for hit in hits]

    return jsonify({
      "page":      page,
      "size":      size,
      "total":     total,
      "pages":     math.ceil(total / size),
      "documents": docs
    })


@app.route("/search", methods=["GET"])
def search_docs():
    """
    GET /search?q=gold&page=1&size=20
    Returns only documents matching the query, paginated.
    """
    q     = request.args.get("q", "").strip()
    page  = int(request.args.get("page", 1))
    size  = int(request.args.get("size", 20))

    # If no query provided, return empty result set
    if not q:
        return jsonify({
          "query":     q,
          "page":      page,
          "size":      size,
          "total":     0,
          "pages":     0,
          "documents": []
        })

    start = (page - 1) * size
    body = {
      "query": {
        "multi_match": {
          "query":  q,
          "fields": ["title^2", "summary^1.5", "content"]
        }
      },
      "from": start,
      "size": size
    }

    res   = es.search(index="vietnamnet", body=body)
    hits  = res["hits"]["hits"]
    total = (
      res["hits"]["total"]["value"]
      if isinstance(res["hits"]["total"], dict)
      else res["hits"]["total"]
    )

    docs = [{"id": hit["_id"], **hit["_source"]} for hit in hits]

    return jsonify({
      "query":     q,
      "page":      page,
      "size":      size,
      "total":     total,
      "pages":     math.ceil(total / size),
      "documents": docs
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=2811)

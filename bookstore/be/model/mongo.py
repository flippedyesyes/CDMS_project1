import os
from typing import Optional, Tuple

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

_DEFAULT_URI = "mongodb://localhost:27017"
_DEFAULT_DB = "bookstore"
_DEFAULT_COLLECTION = "book"

_client: Optional[MongoClient] = None
_collection: Optional[Collection] = None
_indexes_ready: bool = False


def _get_mongo_config() -> Tuple[str, str, str]:
    uri = os.getenv("BOOKSTORE_MONGO_URI", _DEFAULT_URI)
    db_name = os.getenv("BOOKSTORE_MONGO_DB", _DEFAULT_DB)
    collection_name = os.getenv("BOOKSTORE_MONGO_COLLECTION", _DEFAULT_COLLECTION)
    return uri, db_name, collection_name


def _ensure_indexes(collection: Collection) -> None:
    global _indexes_ready
    if _indexes_ready:
        return

    collection.create_index(
        [("doc_type", ASCENDING), ("user_id", ASCENDING)],
        name="uniq_user_id",
        unique=True,
        partialFilterExpression={"doc_type": "user"},
    )
    collection.create_index(
        [("doc_type", ASCENDING), ("store_id", ASCENDING)],
        name="uniq_store_id",
        unique=True,
        partialFilterExpression={"doc_type": "store"},
    )
    collection.create_index(
        [("doc_type", ASCENDING), ("store_id", ASCENDING), ("book_id", ASCENDING)],
        name="uniq_inventory",
        unique=True,
        partialFilterExpression={"doc_type": "inventory"},
    )
    collection.create_index(
        [("doc_type", ASCENDING), ("order_id", ASCENDING)],
        name="uniq_order_id",
        unique=True,
        partialFilterExpression={"doc_type": "order"},
    )
    _indexes_ready = True


def get_book_collection() -> Collection:
    """
    Return (and cache) the MongoDB collection handle.
    BOOKSTORE_MONGO_* environment variables can override the defaults.
    """
    global _client, _collection
    if _collection is not None:
        return _collection

    uri, db_name, collection_name = _get_mongo_config()
    _client = MongoClient(uri)
    _collection = _client[db_name][collection_name]
    _ensure_indexes(_collection)
    return _collection


def ensure_indexes() -> None:
    """Expose an explicit hook to initialize indexes during app start."""
    get_book_collection()

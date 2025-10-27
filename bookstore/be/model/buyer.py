import json
import logging
import uuid
from datetime import datetime
from typing import List, Tuple

from pymongo.errors import PyMongoError

from be.model import db_conn
from be.model import error


class Buyer(db_conn.DBConn):
    def __init__(self):
        super().__init__()

    def __rollback_inventory(self, store_id: str, updates: List[Tuple[str, int]]):
        for book_id, count in updates:
            self.collection.update_one(
                {
                    "doc_type": "inventory",
                    "store_id": store_id,
                    "book_id": book_id,
                },
                {
                    "$inc": {"stock_level": count},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

    def new_order(
        self, user_id: str, store_id: str, id_and_count: List[Tuple[str, int]]
    ) -> Tuple[int, str, str]:
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            order_id = f"{user_id}_{store_id}_{uuid.uuid1()}"
            order_items = []
            for book_id, count in id_and_count:
                inventory = self.collection.find_one(
                    {
                        "doc_type": "inventory",
                        "store_id": store_id,
                        "book_id": book_id,
                    },
                    {"book_info": 1, "stock_level": 1, "_id": 0},
                )
                if inventory is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                stock_level = inventory.get("stock_level", 0)
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                book_info = inventory.get("book_info", "{}")
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")
                order_items.append(
                    {"book_id": book_id, "count": count, "price": price}
                )

            updated_inventory = []
            for item in order_items:
                result = self.collection.update_one(
                    {
                        "doc_type": "inventory",
                        "store_id": store_id,
                        "book_id": item["book_id"],
                        "stock_level": {"$gte": item["count"]},
                    },
                    {
                        "$inc": {"stock_level": -item["count"]},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )
                if result.modified_count == 0:
                    self.__rollback_inventory(store_id, updated_inventory)
                    return error.error_stock_level_low(item["book_id"]) + (order_id,)
                updated_inventory.append((item["book_id"], item["count"]))

            order_doc = {
                "doc_type": "order",
                "order_id": order_id,
                "user_id": user_id,
                "store_id": store_id,
                "items": order_items,
                "created_at": datetime.utcnow(),
            }
            self.collection.insert_one(order_doc)
            return 200, "ok", order_id
        except PyMongoError as e:
            logging.info("528, %s", str(e))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, %s", str(e))
            return 530, "{}".format(str(e)), ""

    def payment(self, user_id: str, password: str, order_id: str) -> Tuple[int, str]:
        try:
            order = self.collection.find_one(
                {"doc_type": "order", "order_id": order_id},
                {"_id": 0},
            )
            if order is None:
                return error.error_invalid_order_id(order_id)
            buyer_id = order.get("user_id")
            store_id = order.get("store_id")
            if buyer_id != user_id:
                return error.error_authorization_fail()

            buyer_doc = self.collection.find_one(
                {"doc_type": "user", "user_id": buyer_id},
                {"password": 1, "balance": 1, "_id": 0},
            )
            if buyer_doc is None:
                return error.error_non_exist_user_id(buyer_id)
            if buyer_doc.get("password") != password:
                return error.error_authorization_fail()

            store_doc = self.collection.find_one(
                {"doc_type": "store", "store_id": store_id},
                {"user_id": 1, "_id": 0},
            )
            if store_doc is None:
                return error.error_non_exist_store_id(store_id)
            seller_id = store_doc.get("user_id")
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            total_price = 0
            for item in order.get("items", []):
                count = item.get("count", 0)
                price = item.get("price", 0)
                total_price = total_price + price * count

            result = self.collection.update_one(
                {
                    "doc_type": "user",
                    "user_id": buyer_id,
                    "balance": {"$gte": total_price},
                },
                {
                    "$inc": {"balance": -total_price},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            if result.modified_count == 0:
                return error.error_not_sufficient_funds(order_id)

            result = self.collection.update_one(
                {"doc_type": "user", "user_id": seller_id},
                {
                    "$inc": {"balance": total_price},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            if result.modified_count == 0:
                return error.error_non_exist_user_id(seller_id)

            delete_result = self.collection.delete_one(
                {"doc_type": "order", "order_id": order_id}
            )
            if delete_result.deleted_count == 0:
                return error.error_invalid_order_id(order_id)

            return 200, "ok"
        except PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

    def add_funds(self, user_id, password, add_value) -> Tuple[int, str]:
        try:
            user_doc = self.collection.find_one(
                {"doc_type": "user", "user_id": user_id},
                {"password": 1, "_id": 0},
            )
            if user_doc is None:
                return error.error_authorization_fail()
            if user_doc.get("password") != password:
                return error.error_authorization_fail()

            result = self.collection.update_one(
                {"doc_type": "user", "user_id": user_id},
                {
                    "$inc": {"balance": int(add_value)},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            if result.matched_count == 0:
                return error.error_non_exist_user_id(user_id)

            return 200, "ok"
        except PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

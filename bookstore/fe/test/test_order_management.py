import time
import uuid
from datetime import datetime, timedelta

import pytest

from be.model.buyer import Buyer as BuyerModel
from be.model.mongo import get_book_collection
from fe import conf
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller


class TestOrderManagement:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.seller_id = f"seller_order_mgmt_{uuid.uuid4()}"
        self.store_id = f"store_order_mgmt_{uuid.uuid4()}"
        self.password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.password)
        assert self.seller.create_store(self.store_id) == 200

        self.buyer_id = f"buyer_order_mgmt_{uuid.uuid4()}"
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        book = self._make_book()
        assert self.seller.add_book(self.store_id, 5, book) == 200
        self.book_id = book.id
        yield

    def _make_book(self):
        from fe.access.book import Book

        book = Book()
        book.id = f"book_order_mgmt_{uuid.uuid4()}"
        book.title = "Order Mgmt Title"
        book.author = "Author"
        book.book_intro = "Simple intro"
        book.content = "Content details"
        book.tags = ["order", "test"]
        return book

    def _create_order(self, quantity=1):
        code, order_id = self.buyer.new_order(
            self.store_id, [(self.book_id, quantity)]
        )
        assert code == 200
        return order_id

    def test_cancel_order_restores_stock(self):
        order_id = self._create_order()
        status, payload = self.buyer.cancel_order(order_id, self.buyer.password)
        assert status == 200, payload

        status, data = self.buyer.list_orders()
        assert status == 200
        orders = data.get("orders", [])
        assert any(o["order_id"] == order_id and o["status"] == "cancelled" for o in orders)

        # Inventory restored -> can create another identical order
        code, new_order_id = self.buyer.new_order(self.store_id, [(self.book_id, 5)])
        assert code == 200
        assert new_order_id

    def test_list_orders_returns_entries(self):
        order_id = self._create_order()
        status, data = self.buyer.list_orders()
        assert status == 200
        orders = data.get("orders", [])
        assert any(o["order_id"] == order_id for o in orders)

    def test_auto_cancel_expired_orders(self):
        original_timeout = BuyerModel.pending_timeout if hasattr(BuyerModel, "pending_timeout") else 1800
        BuyerModel.pending_timeout = 1
        try:
            order_id = self._create_order()
            collection = get_book_collection()
            collection.update_one(
                {"doc_type": "order", "order_id": order_id},
                {
                    "$set": {
                        "created_at": datetime.utcnow() - timedelta(seconds=10),
                        "updated_at": datetime.utcnow() - timedelta(seconds=10),
                    }
                },
            )
            time.sleep(1.5)
            status, data = self.buyer.list_orders()
            assert status == 200
            orders = data.get("orders", [])
            assert any(
                o["order_id"] == order_id and o["status"] == "cancelled_timeout"
                for o in orders
            )
            # After auto cancel inventory should be available
            code, second_order_id = self.buyer.new_order(
                self.store_id, [(self.book_id, 5)]
            )
            assert code == 200
            assert second_order_id
        finally:
            BuyerModel.pending_timeout = original_timeout

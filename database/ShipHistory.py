from database.dbFunctions import *


class ShipHistory:

    def __init__(self, transactions: list = None):
        if transactions is None:
            self.transactions = []
        else:
            self.transactions = transactions
        self.transaction_groups = []
        self.make_transaction_groups()

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.make_transaction_groups()

    def get_profits(self, transaction_group=None):
        transaction_list = self.transactions
        if transaction_group is not None:
            transaction_list = transaction_group
        profit = 0
        for t in transaction_list:
            profit += t["Credits"]
        return profit

    def make_transaction_groups(self):
        self.transaction_groups = []

        inventory_good = ""
        inventory_quantity = 0

        current_trade_group = []
        maintenance_group = []

        for t in self.transactions:
            if t["ShipPurchase"] or t["Repair"]:
                maintenance_group.append(t)
            else:
                if t["Refuel"]:
                    current_trade_group.append(t)
                    if inventory_good == "FUEL" and t["TradeGood"] == "FUEL":
                        inventory_quantity += t["Quantity"]
                elif t["TradeGood"] == inventory_good:
                    current_trade_group.append(t)
                    inventory_quantity += t["Quantity"]
                else:
                    if len(current_trade_group) > 0:
                        self.transaction_groups.append(current_trade_group)
                    current_trade_group = [t]
                    inventory_quantity = t["Quantity"]
                    inventory_good = t["TradeGood"]

        if len(current_trade_group) > 0:
            self.transaction_groups.append(current_trade_group)

        if len(maintenance_group) > 0:
            self.transaction_groups.insert(0, maintenance_group)

    def get_transaction_groups(self):
        return self.transaction_groups


if __name__ == '__main__':
    transaction_list = access_get_transactions()
    ship_transactions = {}
    for t in transaction_list:
        if t["Ship"] in ship_transactions.keys():
            ship_transactions[t["Ship"]].append(t)
        else:
            ship_transactions[t["Ship"]] = [t]



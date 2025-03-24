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
        profit = transaction_list_profits(transaction_list)
        return profit

    def make_transaction_groups(self):
        trade_lists = []

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
                        trade_lists.append(current_trade_group)
                    current_trade_group = [t]
                    inventory_quantity = t["Quantity"]
                    inventory_good = t["TradeGood"]

        if len(current_trade_group) > 0:
            trade_lists.append(current_trade_group)

        if len(maintenance_group) > 0:
            trade_lists.insert(0, maintenance_group)

        self.transaction_groups = []
        for tl in trade_lists:
            tg = TransactionGroup(tl)
            self.transaction_groups.append(tg)



    def get_transaction_groups(self, inventory_good: str = None):
        if inventory_good is None:
            return self.transaction_groups
        else:
            good_transaction_groups = []
            for tg in self.transaction_groups:
                if tg.get_inventory_good() == inventory_good:
                    good_transaction_groups.append(tg)
            return good_transaction_groups


def transaction_list_profits(transaction_list):
    profits = 0
    for t in transaction_list:
        profits += t["Credits"]
    return profits


class TransactionGroup:

    def __init__(self, transaction_list=None):
        self.inventory_good = None
        self.transactions = []
        self.purchases = []
        self.refuels = []
        self.sales = []
        self.maintenance = []
        self.other = []
        if transaction_list is not None:
            for t in transaction_list:
                self.add_transaction(t)


    def add_transaction(self, transaction):
        self.transactions.append(transaction)

        transaction_good = transaction["TradeGood"]
        if transaction["Refuel"]:
            self.refuels.append(transaction)
            return
        if transaction["Repair"] or transaction["ShipPurchase"]:
            self.maintenance.append(transaction)
            return
        if transaction["Quantity"] == 0:
            print("Unhandled case:")
            print(transaction)
            self.other.append(transaction)

        if transaction_good is not None:
            if self.inventory_good is None:
                self.inventory_good = transaction_good
            elif self.inventory_good != transaction_good:
                raise KeyError("Transaction group is set to " + self.inventory_good + " but transaction uses good " + transaction_good)

        if transaction["Quantity"] > 0:
            self.purchases.append(transaction)
        elif transaction["Quantity"] < 0:
            self.sales.append(transaction)

    def get_inventory_good(self):
        return self.inventory_good

    def get_good_costs(self):
        return transaction_list_profits(self.purchases)

    def get_refuel_costs(self):
        return transaction_list_profits(self.refuels)

    def get_sale_profits(self):
        return transaction_list_profits(self.sales)

    def get_net_profits(self, exclude_refuels=False):
        if exclude_refuels:
            return self.get_sale_profits() + self.get_good_costs()
        else:
            return transaction_list_profits(self.transactions)

    def is_complete(self):
        quantity = 0
        for p in self.purchases:
            quantity += p["Quantity"]
        for s in self.sales:
            quantity += s["Quantity"]
        if quantity == 0:
            return True
        else:
            return False




if __name__ == '__main__':
    transaction_list = access_get_transactions()
    ship_transactions = {}
    for t in transaction_list:
        if t["Ship"] in ship_transactions.keys():
            ship_transactions[t["Ship"]].append(t)
        else:
            ship_transactions[t["Ship"]] = [t]



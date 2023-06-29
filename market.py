from new_exceptions import *
import csv
import os
from itertools import combinations


class Order:
    def __init__(self, side, idn, owner_id, price, amount, market):
        self.side = side
        self.owner_id = owner_id
        self.idn = idn
        self.init_amount = amount
        self.market = market
        self.price = price
        self.amount = amount
        self.completed = False

    def __str__(self):
        return f'order #{self.idn}: {self.side}s {self.amount} for {self.price}'

    def process(self, amount):
        if amount > self.amount:
            raise ValueError('Order cannot be completed: amount too big')

        if self.side == 'buy':
            self.market.bank.give(self.owner_id, self.market.currency_b, amount)

        elif self.side == 'sell':
            self.market.bank.give(self.owner_id, self.market.currency_a, amount * self.price)

        self.amount -= amount
        if self.amount == 0:
            self.completed = True


class Market:
    def __init__(self, currency_a, currency_b, bank, db_name, allow_existing=True, lot_size=0.5):
        # tables:
        # buy_glass: user_id, price, amount
        # sell_glass: user_id, price, amount
        self.bank = bank
        self.buy_glass = []
        self.sell_glass = []
        self.lot_size = lot_size
        self.currency_a = currency_a
        self.currency_b = currency_b
        self.last_trade_price = None
        self.max_buy_price = None
        self.min_sell_price = None
        self.total_sell = 0
        self.total_buy = 0
        self.last_order_id = 0
        self.db_name = db_name

        if allow_existing and os.path.isfile(db_name):
            with open(db_name, 'r', newline='', encoding='utf-8') as db_file:
                rdr = csv.DictReader(db_file)
                for item in rdr:
                    if item['side'] == 'buy':
                        self.buy_glass.append(Order('buy', int(item['id']), int(item['owner_id']), float(item['price']), float(item['amount']), self))
                    elif item['side'] == 'sell':
                        self.sell_glass.append(Order('sell', int(item['id']), int(item['owner_id']), float(item['price']), float(item['amount']), self))
                if len(self.buy_glass + self.sell_glass) > 0:
                    self.last_order_id = max(self.buy_glass + self.sell_glass, key=lambda order: order.idn).idn + 1
            self.buy_glass.sort(key=lambda order: order.price, reverse=True)
            self.sell_glass.sort(key=lambda order: order.price)

            self.update_variables()

        else:
            self.create_file()

    def __str__(self):
        x = str(f''' === MARKET ===
Trades {self.currency_a} to {self.currency_b}
Last price: {self.last_trade_price}

Maximum bid: {self.max_buy_price}
Minimum ask: {self.min_sell_price}

Total buy volume: {self.total_buy}
Total sell volume: {self.total_sell}

-- GLASS --
''' + '\n'.join([str(x) for x in sorted(self.sell_glass, key=lambda y: y.price, reverse=True)]) + '''
-----------
''' + '\n'.join([str(x) for x in self.buy_glass]))
        return x

    def valid_amount(self, amount):
        if (type(amount) in (int, float)) and (0 < amount) and (amount // self.lot_size * self.lot_size == amount):
            return True
        return False

    def place_limit_order(self, trader_idn, init_price, amount, side):
        if not self.bank.account_exists(trader_idn):
            raise IdNotFoundError(f'Failed to place order: Account with ID {trader_idn} does not exist')
        if not self.valid_amount(amount):
            raise ValueError('Failed to place order: invalid amount')

        price = round(init_price, self.bank.digits_dict[self.currency_a])

        if init_price != price:
            print(f"Order price was rounded to {price} {self.currency_a}")

        if price <= 0:
            raise ValueError('Price should be higher than zero')

        if side == 'buy':
            if self.min_sell_price is not None:
                if price >= self.min_sell_price:
                    raise ValueError('Failed to place order: limit order buy price higher than minimum sell price')

            if self.bank.check_balance(trader_idn, self.currency_a) < price * amount:
                raise NotEnoughMoney(f"Money required: {price * amount} {self.currency_a}, trader with id {trader_idn} only has {self.bank.check_balance(trader_idn, self.currency_a)}")

            self.bank.give(trader_idn, self.currency_a, -price * amount)
            self.buy_glass.append(Order('buy', self.last_order_id, trader_idn, price, amount, self))

            # updating main market variables
            self.update_variables()
            self.last_order_id += 1
            # sorting glass from highest to lowest price
            self.buy_glass.sort(key=lambda order: order.price, reverse=True)

        elif side == 'sell':
            if self.max_buy_price is not None:
                if price <= self.max_buy_price:
                    raise ValueError('Failed to place order: limit order sell price lower than maximum buy price')

            if self.bank.check_balance(trader_idn, self.currency_b) < amount:
                raise NotEnoughMoney(f"Money required: {amount} {self.currency_b}, trader with id {trader_idn} only has {self.bank.check_balance(trader_idn, self.currency_)}")

            self.bank.give(trader_idn, self.currency_b, -amount)
            self.sell_glass.append(Order('sell', self.last_order_id, trader_idn, price, amount, self))

            # updating main market variables
            self.update_variables()
            self.last_order_id += 1
            # sorting glass from lowest to highest price
            self.sell_glass.sort(key=lambda order: order.price)

        self.save_to_file()

    def market_buy_requires(self, amount):
        left_amount = amount
        required = 0
        # counting required currency_a
        for order in self.sell_glass:
            if left_amount >= order.amount:
                left_amount -= order.amount
                required += order.price * order.amount
            else:
                required += order.price * left_amount
                break
        return required

    def market_sell_returns(self, amount):
        left_amount = amount
        result = 0
        # counting required currency_a
        for order in self.buy_glass:
            if left_amount >= order.amount:
                left_amount -= order.amount
                result += order.price * order.amount
            else:
                result += order.price * left_amount
                break
        return result

    def place_market_order(self, trader_idn, amount, side):
        if not self.bank.account_exists(trader_idn):
            raise IdNotFoundError(f'Failed to place order: Account with ID {trader_idn} does not exist')
        if not self.valid_amount(amount):
            raise ValueError('Failed to place order: invalid amount')

        if side == 'buy':
            if amount > self.total_sell:
                raise ValueError(f'Cannot buy {amount} {self.currency_b}: only {self.total_sell} is being sold')

            a_required = self.market_buy_requires(amount)

            if self.bank.check_balance(trader_idn, self.currency_a) < a_required:
                raise NotEnoughMoney(f"Money required: {a_required}, trader with id {trader_idn} only has {self.bank.check_balance(trader_idn, self.currency_a)}")
            self.bank.give(trader_idn, self.currency_a, -a_required)

            left_amount = amount
            for order in self.sell_glass:
                # sell glass is already sorted when any limit order is created
                if left_amount == 0:
                    break
                if left_amount >= order.amount:
                    left_amount -= order.amount
                    order.process(order.amount)
                else:
                    order.process(left_amount)
                self.last_trade_price = order.price

            self.bank.give(trader_idn, self.currency_b, amount)
            self.update_variables()

            self.save_to_file()
            return a_required

        if side == 'sell':
            if amount > self.total_buy:
                raise ValueError(f'Cannot sell {amount} {self.currency_b}: only {self.total_buy} is being bought')

            if self.bank.check_balance(trader_idn, self.currency_b) < amount:
                raise NotEnoughMoney(f"Money required: {amount}, trader with id {trader_idn} only has {self.bank.check_balance(trader_idn, self.currency_b)}")
            self.bank.give(trader_idn, self.currency_b, -amount)

            left_amount = amount
            a_returns = self.market_sell_returns(amount)
            for order in self.buy_glass:
                # buy glass is already sorted when any limit order is created
                if left_amount == 0:
                    break
                if left_amount >= order.amount:
                    left_amount -= order.amount
                    order.process(order.amount)
                else:
                    order.process(left_amount)
                self.last_trade_price = order.price

            self.bank.give(trader_idn, self.currency_a, a_returns)
            self.update_variables()

            self.save_to_file()
            return a_returns

    def show_orders(self, trader_id):
        res = []
        for order in self.sell_glass:
            if order.owner_id == trader_id:
                res.append(order)
        for order in self.buy_glass:
            if order.owner_id == trader_id:
                res.append(order)
        return res

    def cancel_order(self, order_id):
        for i in range(len(self.sell_glass)):
            if self.sell_glass[i].idn == order_id:
                self.bank.give(self.sell_glass[i].owner_id, self.currency_b, self.sell_glass[i].amount)
                self.sell_glass.pop(i)
                self.update_variables()
                self.save_to_file()
                return
        for i in range(len(self.buy_glass)):
            if self.buy_glass[i].idn == order_id:
                self.bank.give(self.buy_glass[i].owner_id, self.currency_a, (self.buy_glass[i].amount * self.buy_glass[i].price))
                self.buy_glass.pop(i)
                self.update_variables()
                self.save_to_file()
                return

        raise IdNotFoundError(f'Order with ID {order_id} does not exist')

    def update_variables(self):
        # deleting empty orders
        for order in self.buy_glass:
            if order.completed or order.amount == 0:
                self.buy_glass.pop(self.buy_glass.index(order))
        for order in self.sell_glass:
            if order.completed or order.amount == 0:
                self.sell_glass.pop(self.sell_glass.index(order))

        self.total_buy = sum(order.amount for order in self.buy_glass)
        if self.total_buy:
            self.max_buy_price = max(self.buy_glass, key=lambda order: order.price).price
        else:
            self.max_buy_price = None
        self.total_sell = sum(order.amount for order in self.sell_glass)
        if self.total_sell:
            self.min_sell_price = min(self.sell_glass, key=lambda order: order.price).price
        else:
            self.min_sell_price = None

        self.sell_glass.sort(key=lambda x: x.price)
        self.buy_glass.sort(key=lambda x: x.price, reverse=True)

        self.save_to_file()

    def save_to_file(self):
        with open(self.db_name, 'w', newline='', encoding='utf-8') as db_file:
            wr = csv.writer(db_file)
            wr.writerow(['id', 'side', 'owner_id', 'price', 'amount'])
            for item in self.buy_glass:
                wr.writerow([item.idn, item.side, item.owner_id, item.price, item.amount])
            for item in self.sell_glass:
                wr.writerow([item.idn, item.side, item.owner_id, item.price, item.amount])

    def create_file(self):
        with open(self.db_name, 'w', newline='', encoding='utf-8') as db_file:
            print('Market database created successfully')
            wr = csv.writer(db_file)
            wr.writerow(['id', 'side', 'owner_id', 'price', 'amount'])


class Exchange:
    def __init__(self, currencies, bank):
        self.bank = bank
        self.markets = []
        m = list(combinations(currencies, 2))
        for comb in m:
            self.markets.append(Market(comb[0], comb[1], self.bank, db_name=str(f'{comb[0]}{comb[1]}.market')))

    def get_market(self, currency_a, currency_b):
        for market in self.markets:
            if market.currency_a in (currency_a, currency_b) and market.currency_b in (currency_a, currency_b):
                return market
        return False



from accountant import Accountant
from market import *
import csv
from new_exceptions import *
import messages


class Naebank:
    def __init__(self):
        self.acc = Accountant("naebank.acc", "", 1, ["rub", "usd", "wmz"])
        self.markets = [Market('rub', 'usd', self.acc, 'usdrub.market'), Market('rub', 'wmz', self.acc, 'wmzrub.market'), Market('usd', 'wmz', self.acc, 'wmzusd.market')]
        self.users_list = []
        self.users_db = {}
        self.init_users()

    def init_users(self):
        db_name = "users.db"
        if os.path.isfile(db_name):
            with open(db_name, 'r', newline='', encoding='utf-8') as db_file:
                for line in csv.DictReader(db_file):
                    self.users_list.append(line['name'])
                    self.users_db[line['name']] = [line['password'], line['id']]


naebank = Naebank()


class UserSession:
    def __init__(self, telegram_user_id):
        self.username = None
        self.id = None
        self.telegram_user_id = telegram_user_id
        self.logged_in = False
        self.tries_to_log_in = None
        self.bank = naebank
        self.send_destination = None
        self.send_currency = None
        self.send_amount = None
        print(self.bank.users_db)

    def try_to_log_in(self, login):
        if login in self.bank.users_list:
            self.tries_to_log_in = login
            return True
        return False

    def try_password(self, password):
        if password == self.bank.users_db[self.tries_to_log_in][0]:
            self.username = self.tries_to_log_in
            self.tries_to_log_in = None
            self.logged_in = True
            self.id = int(self.bank.users_db[self.username][1])
            return self.username
        return False

    def get_balance(self):
        res = ["=== ВАШ БАЛАНС ==="]
        print(self.bank.acc.currencies_list)
        for currency in self.bank.acc.currencies_list:
            res.append(f"{self.bank.acc.check_balance(self.id, currency):.2f} {currency}")
        return "\n".join(res)

    def transfer(self):
        self.bank.acc.transfer(int(self.id), int(self.bank.users_db[self.send_destination][1]), self.send_currency, float(self.send_amount), allow_negative=True)

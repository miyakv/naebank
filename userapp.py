from accountant import Accountant
from market import *
import csv
import passwords
from new_exceptions import *
import messages


class Naebank:
    def __init__(self):
        self.acc = Accountant("naebank.acc", "", 1, ["rub", "usd", "wmz"])
        self.markets = [Market('rub', 'usd', self.acc, 'usdrub.market'), Market('rub', 'wmz', self.acc, 'wmzrub.market'), Market('usd', 'wmz', self.acc, 'wmzusd.market')]
        self.users_list = []
        self.users_db = {}
        self.users_db_name = "users.db"
        self.init_users()

    def init_users(self):
        if os.path.isfile(self.users_db_name):
            with open(self.users_db_name, 'r', newline='', encoding='utf-8') as db_file:
                for line in csv.DictReader(db_file):
                    self.users_list.append(line['name'])
                    self.users_db[line['name']] = [line['password'], line['id']]

    def update_user_data(self, bank_id, new_telegram_id=None, new_password=None):
        if new_password is None and new_telegram_id is None:
            return False
        with open(self.users_db_name, 'r', newline='', encoding='utf-8') as db_file, open("udummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            print(rdr.fieldnames)
            wrt.writerow(rdr.fieldnames)
            found = False

            for line in rdr:
                if (int(line['id']) != bank_id) or found:
                    wrt.writerow(line.values())
                else:
                    found = True
                    new = line
                    if new_telegram_id is not None:
                        new['telegram_user_id'] = new_telegram_id
                    if new_password is not None:
                        new['password'] = new_password
                    print(new)
                    wrt.writerow(new.values())

        os.remove(self.users_db_name)
        os.rename("udummy.csv", self.users_db_name)


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

    def auto_log_in(self, username, idn):
        self.username = username
        self.id = int(idn)
        self.logged_in = True

    def try_to_log_in(self, login):
        if login in self.bank.users_list:
            self.tries_to_log_in = login
            return True
        return False

    def try_password(self, password):
        if passwords.check_password(password, self.bank.users_db[self.tries_to_log_in][0]):
            self.username = self.tries_to_log_in
            self.tries_to_log_in = None
            self.logged_in = True
            self.id = int(self.bank.users_db[self.username][1])
            self.bank.update_user_data(self.id, new_telegram_id=self.telegram_user_id)
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

    def check_password(self, to_try):
        print("Ща будем посмотреть")
        if passwords.check_password(to_try, self.bank.users_db[self.username][0]):
            print("Верный пароль")
            return True
        print("Неверный пароль")
        return False

    def change_password(self, new_password):
        if not passwords.validate_password(new_password):
            return False
        hashed_password = passwords.encode(new_password)
        self.bank.update_user_data(self.id, new_password=hashed_password)
        return True



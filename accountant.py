# csv with Accounts (id, name, sum)
# Operations:
# init_db()
# create_account(name, init_sum)
# delete_account(whom)
# give_money(whom_to, sum)
# transfer_money(from, to, sum)

# give_all(currency, sum)
# transfer_from_all_to_one(whom_to, currency, sum)
import csv
import os
# import sqlite3 as sl
from new_exceptions import *
from pretty import pretty_file


class Accountant:
    def __init__(self, db_name: str, name_prefix: str, players: int, currencies_list: list, base_digits=2, log_db_name="operations.log", allow_existing=True):
        self.last_id = players
        self.name_prefix = name_prefix
        self.currencies_list = currencies_list
        self.digits_dict = dict(zip(currencies_list, [base_digits] * len(currencies_list)))
        print(self.digits_dict)
        self.db_name = db_name
        self.number_of_players = players
        # making all currencies' names lower
        currencies_list = list(map(lambda x: x.lower(), currencies_list))
        self.header = list(["id", "name"] + currencies_list)
        # if allow_existing and db exists - stop function
        if allow_existing and os.path.isfile(db_name):
            with open(db_name, 'r', newline='', encoding='utf-8') as db_file:
                rdr = csv.reader(db_file)
                self.currencies_list = list(rdr)[0][2:]
            return

        # creating/rewriting db
        with open(db_name, 'w', newline='', encoding='utf-8') as db_file:
            wr = csv.writer(db_file)
            wr.writerow(self.header)
            for i in range(players):
                wr.writerow([i + 1, f"{name_prefix} {i + 1}"] + [0] * len(currencies_list))
        self.__str__()

    def rewrite_db(self, new_db_name):
        os.remove(self.db_name)
        os.rename(new_db_name, self.db_name)
        return True

    def create_account(self, name=None):
        if name is None:
            name = f"{self.name_prefix} {self.last_id + 1}"
        with open(self.db_name, 'a', newline='', encoding='utf-8') as db_file:
            wrt = csv.writer(db_file)
            wrt.writerow([self.last_id + 1, name] + [0] * len(self.currencies_list))
        self.last_id += 1
        self.number_of_players += 1
        return self.last_id

    def delete_account(self, idn: int):
        deleted = False
        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file, open("dummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            wrt.writerow(self.header)
            for line in rdr:
                if int(line['id']) != idn:
                    wrt.writerow(line.values())
                else:
                    deleted = True
        if deleted:
            self.rewrite_db("dummy.csv")
            self.number_of_players -= 1
        else:
            os.remove("dummy.csv")
            raise IdNotFoundError(f"Cannot delete account with id {idn}: Account does not exist")

    def transfer(self, from_idn: int, to_idn: int, currency: str, init_amount: float, allow_negative=False):
        currency_name = currency.lower()
        if currency not in self.currencies_list:
            raise CurrencyError(f"Currency {currency} does not exist")
        currency_index = self.currencies_list.index(currency)

        amount = round(init_amount, self.digits_dict[currency_name])
        if init_amount != amount:
            print(f"Amount of {currency} was rounded to {amount}")

        if amount < 0:
            raise ValueError("You cannot transfer negative amount")
        if amount == 0:
            raise ValueError("You cannot transfer nothing")
        if from_idn == to_idn:
            raise ValueError("Sender and receiver should be different accounts")

        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file, open("dummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            wrt.writerow(self.header)
            found_from = False
            found_to = False
            for line in rdr:
                if int(line['id']) == from_idn:
                    found_from = True
                    if not allow_negative:
                        if float(line[currency]) - amount < 0:
                            dummy_file.close()
                            os.remove("dummy.csv")
                            raise NotEnoughMoney(f"Cannot transfer {amount} {currency} from id {from_idn} to id {to_idn}: id {from_idn} has only {float(line[currency])} {currency}, negative not allowed")
                    new = line
                    new[currency] = float(new[currency]) - amount
                    wrt.writerow(new.values())

                elif int(line['id']) == to_idn:
                    found_to = True
                    new = line
                    new[currency] = float(new[currency]) + amount
                    wrt.writerow(new.values())
                else:
                    wrt.writerow(line.values())

        if not found_from:
            return IdNotFoundError(f"Cannot transfer from account with id {from_idn}: Account does not exist")
        if not found_to:
            return IdNotFoundError(f"Cannot transfer to account with id {to_idn}: Account does not exist")

        self.rewrite_db("dummy.csv")

    def give(self, to_idn: int, currency: str, init_amount: float, allow_negative=False):
        currency = currency.lower()
        if currency not in self.currencies_list:
            raise CurrencyError(f"Currency {currency} does not exist")
        found = False

        amount = round(init_amount, self.digits_dict[currency])
        if init_amount != amount:
            print(f"Amount of {currency} was rounded to {amount}")

        if amount == 0:
            raise ValueError("You cannot give/take nothing")

        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file, open("dummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            wrt.writerow(self.header)
            for line in rdr:
                if int(line['id']) != to_idn:
                    wrt.writerow(line.values())
                else:
                    found = True
                    if amount < 0 and not allow_negative:
                        if float(line[currency]) + amount < 0:
                            # handling not enough money case
                            dummy_file.close()
                            os.remove("dummy.csv")
                            raise NotEnoughMoney(f"Cannot take {-amount} {currency} from id {to_idn}: id {to_idn} has only {float(line[currency])} {currency}, negative not allowed")
                    new = line
                    new[currency] = round(float(new[currency]) + amount, self.digits_dict[currency])
                    wrt.writerow(new.values())

        if not found:
            raise IdNotFoundError(f"Cannot give to account with id {to_idn}: Account does not exist")

        self.rewrite_db("dummy.csv")

    def give_all(self, currency: str, init_amount: float, allow_negative=False, skip_errors=False):
        currency = currency.lower()
        if currency not in self.currencies_list:
            raise CurrencyError(f"Currency {currency} does not exist")

        amount = round(init_amount, self.digits_dict[currency])
        if init_amount != amount:
            print(f"Amount of {currency} was rounded to {amount}")

        if amount == 0:
            raise ValueError("You cannot give/take nothing")

        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file, open("dummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            wrt.writerow(self.header)
            for line in rdr:
                if (amount < 0 and not allow_negative) and (float(line[currency]) + amount < 0):
                    if not skip_errors:
                        # handling not enough money case
                        dummy_file.close()
                        os.remove("dummy.csv")
                        raise NotEnoughMoney(f"Cannot take {-amount} {currency} from id {line['id']}: id {line['id']} has only {float(line[currency])} {currency}, negative not allowed")
                else:
                    new = line
                    new[currency] = round(float(new[currency]) + amount, self.digits_dict[currency])
                    wrt.writerow(new.values())

        self.rewrite_db("dummy.csv")

    def __str__(self):
        return pretty_file(self.db_name)

    def check_balance(self, idn, currency):
        if currency.lower() not in self.currencies_list:
            return CurrencyError("Currency does not exist")
        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file:
            rdr = csv.DictReader(db_file)
            for line in rdr:
                if int(line['id']) == idn:
                    return float(line[currency])
        return IdNotFoundError(f"Cannot check balance of an account with id {idn}: Account does not exist")

    def create_currency(self, currency_name: str, init_amount=0):
        if currency_name.lower() in self.currencies_list:
            raise CurrencyError(f"Currency {currency_name} already exists")

        self.currencies_list.append(currency_name)
        self.header.append(currency_name)

        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file, open("dummy.csv", 'w', newline='', encoding='utf-8') as dummy_file:
            rdr = csv.DictReader(db_file)
            wrt = csv.writer(dummy_file)
            wrt.writerow(self.header)
            for line in rdr:
                newline = list(line.values()) + [init_amount]
                wrt.writerow(newline)

        self.rewrite_db("dummy.csv")

    def account_exists(self, idn: int):
        with open(self.db_name, 'r', newline='', encoding='utf-8') as db_file:
            for line in csv.DictReader(db_file):
                if int(line['id']) == idn:
                    return True
        return False

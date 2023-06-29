class init:
    welcome = """=== NAEBANK v.0.0.1 ===
    Welcome to the floor economy!
    To view available commands, print /help."""


class restart:
    warning = "Are you sure you want to restart Floor? Y/N >>> "
    aborted = "Restart aborted."
    success = "Floor restarted."


class create:
    name_input = "Input name: "
    success = "Account named {} with ID {} created successfully."
    empty_name = "Name cannot be empty!"


class delete:
    id_input = "Input ID of an account to be deleted >>> "
    success = "Account with ID {} deleted successfully."


class finish:
    warning = "Are you sure you want to exit Floor? Y/N >>> "


class misc:
    command_not_found = "Command {} does not exist!"
    ask_continue = "Do you want to proceed? Y/N >>> "
    id_not_exists = "ID does not exist"
    id_int_error = "ID must be an integer!"
    empty_name = "Name cannot be empty!"


class transfer:
    from_input = "Input sender ID >>> "
    to_input = "Input receiver ID >>> "
    currency_input = "Available currencies: {}\nInput currency >>> "
    amount = "Input amount >>> "
    currency_not_exist = "Currency {} does not exist!"
    success = "{} {} transfered from ID {} to ID {} successfully."


class create_currency:
    create = "Input new currency name: >>> "
    already_exists = "Currency {} already exists!"


class amount:
    float_error = "Amount should be a number"
    zero_error = "Amount should not be zero"
    negative_error = "Amount should be a positive number"


class login:
    id = "Input ID to login: >>> "
    required = "You need to log in for this operation"


class market:
    to_buy = "Input currency to buy: >>> "
    to_sell = "Input currency to sell: >>> "
    order_type = '''Select order type:
    1) Limit
    2) Market
    >>> '''
    price = 'Input price (how many {} for {}): >>> '
    amount = 'Input amount of {} to {} >>> '
    pair_does_not_exist = 'No market associated with selected currencies'
    type_error = 'type should be either 1 or 2'
    lot_info = 'Amount of {} must be divisible by {}. Otherwise, it will be rounded down.'
    limit_success = 'Successfully placed an order to {} {} {} with price of {} {} for 1 {}'
    market_success = 'Successfully {} {} {} for {} {}. Average price: {} {} for 1 {}'
    all_orders = 'Orders of ID {}:'
    select = 'Select market: >>> '
    select_cancel_order = 'Select order id to cancel: >>> '


class help:
    message = '''=== COMMANDS ===
    addacc - add a new account
    delete - delete an account
    create - create new currency

    transfer - transfer assets between accounts
    give - give or take money from account to bank
    giveall - give or take money to/from all accounts

    login - log into stock exchange account
    order - place a stock exchange order 
    market - show all stocks information
    myorders - show all the order of the logged in account
    cancel - cancel a stock exchange order 

    restart - delete current and start new simulation
    finish - save and exit'''

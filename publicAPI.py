import os
import traceback

from public import public
from dotenv import load_dotenv

from helperAPI import Brokerage, maskString, printAndDiscord, printHoldings, stockOrder


def public_init(PUBLIC_EXTERNAL=None):
    # Initialize .env file
    load_dotenv()
    # Import Public account
    public_obj = Brokerage("Public")
    if not os.getenv("PUBLIC") and PUBLIC_EXTERNAL is None:
        print("Public not found, skipping...")
        return None
    PUBLIC = (
        os.environ["PUBLIC"].strip().split(",")
        if PUBLIC_EXTERNAL is None
        else PUBLIC_EXTERNAL.strip().split(",")
    )
    # Log in to Public account
    print("Logging in to Public...")
    for index, account in enumerate(PUBLIC):
        name = f"Public {index + 1}"
        try:
            account = account.split(":")
            pb = public.Public(filename=f"public{index + 1}.pkl")
            pb.login(
                username=account[0],
                password=account[1]
            )
            # Public only has one account
            public_obj.set_logged_in_object(name, pb)
            an = pb.get_account_number()
            public_obj.set_account_number(name, an)
            print(f"Found account {maskString(an)}")
            atype = pb.get_account_type()
            public_obj.set_account_type(name, an, atype)
            cash = pb.get_account_cash()
            public_obj.set_account_totals(name, an, cash)
        except Exception as e:
            print(f"Error logging in to Public: {e}")
            print(traceback.format_exc())
            continue
    print("Logged in to Public!")
    return public_obj


def public_holdings(pbo: Brokerage, loop=None):
    for key in pbo.get_account_numbers():
        for account in pbo.get_account_numbers(key):
            obj: public.Public = pbo.get_logged_in_objects(key)
            try:
                # Get account holdings
                positions = obj.get_positions()
                if positions != []:
                    for holding in positions:
                        # Get symbol, quantity, and total value
                        sym = holding["instrument"]["symbol"]
                        qty = float(holding["quantity"])
                        current_price = obj.get_symbol_price(sym)
                        if current_price is None:
                            current_price = "N/A"
                        pbo.set_holdings(key, account, sym, qty, current_price)
            except Exception as e:
                printAndDiscord(f"{key}: Error getting account holdings: {e}", loop)
                traceback.format_exc()
                continue
        printHoldings(pbo, loop)

def public_transaction(pbo: Brokerage, orderObj: stockOrder, loop=None):
    print()
    print("==============================")
    print("Public")
    print("==============================")
    print()
    for s in orderObj.get_stocks():
        for key in pbo.get_account_numbers():
            printAndDiscord(
                f"{key}: {orderObj.get_action()}ing {orderObj.get_amount()} of {s}",
                loop,
            )
            for account in pbo.get_account_numbers(key):
                obj: public.Public = pbo.get_logged_in_objects(key)
                print_account = maskString(account)
                try:
                    order = obj.place_order(
                        symbol=s,
                        quantity=orderObj.get_amount(),
                        side=orderObj.get_action(),
                        order_type="market",
                        time_in_force="day",
                    )
                    print(f"{print_account}: {order}")
                except Exception as e:
                    printAndDiscord(f"{print_account}: Error placing order: {e}", loop)
                    traceback.print_exc()
                    continue
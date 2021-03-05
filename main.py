import wallet_api
import settings
import random
import math

# get total balance + pending
def get_balance(account):
    response = wallet_api.get_balance(account)
    acct_bal = response.json()
    balance = int(acct_bal.get('balance'))
    pending = int(acct_bal.get('pending'))
    return raw_to_banano(balance + pending)

# convert from raw form
def raw_to_banano(raw_amt):
    return raw_amt / (10 ** 29)

# convert ban to raw form
def banano_to_raw(ban_amt):
    expanded = ban_amt * 100
    return int(expanded) * (10 ** 27)

def get_valid_entries(address, balance):
    valid_entries = 0
    receive_amt = 0
    response = wallet_api.get_transactions(address, -1)
    account = response.json()
    for tx in account.get('history'):
        if(tx.get('type') == "receive" and tx.get('account') != settings.donation_account):
            amt = raw_to_banano(int(tx.get('amount')))
            receive_amt = receive_amt + amt
            if(receive_amt >= balance):
                valid_entries = valid_entries + math.floor(amt)
                break
            if(amt >= 0):
                valid_entries = valid_entries + math.floor(amt)
    return valid_entries    

# get lotto entries
def get_entries(address,target, valid_target):
    receive_amount = 0
    response = wallet_api.get_transactions(address, -1)
    account = response.json()
    entries = []
    for tx in account.get('history'):
        if(tx.get('type') == "receive"):
            amt = raw_to_banano(int(tx.get('amount')))
            receive_amount = receive_amount + math.floor(amt)
            sender = tx.get('account')
            d = {"entrant": sender, "entries": amt}
            # less than 1 BAN considered donation
            if(amt >= 1):
                entries.append(d)
                target = target - amt
                valid_target = valid_target - amt
                if(target <= 0 and valid_target <= 0):
                    break # stop when deposit count matches balance
    return entries

# shuffle entrants
def shuffle_entries(entries):
    return random.shuffle(entries)

def pick_winner(entries, ticket):
    for entrant in entries:
        amt = entrant.get('entries')
        ticket = ticket - amt
        if(ticket <= 0):
            return entrant.get('entrant')

def send_payout(address, amount):
    try:
        print('attempt ban send to' + address)
        response = wallet_api.send_banano(address, amount)
        response = response.json()
        if(response.get('block')):
            print("ban sent to: " + address)
            print("block: " + response.get('block'))
        else:
            print('Error sending payment')
    except Exception as e:
        print(e)
        print('Error sending payment to ' + word)

def main():
    winners = []
    wallet_api.receive_pending(settings.ban_account)
    balance = get_balance(settings.ban_account)
    print('Beginning Balance: ' + str(balance))
    bal = int(math.floor(balance))
    valid_balance = get_valid_entries(settings.ban_account, bal)
    print('Valid Entry Balance: ' + str(valid_balance))
    entries = get_entries(settings.ban_account,bal, valid_balance)
    random.shuffle(entries) # shuffle the entries
    first = random.randint(1,valid_balance)
    second = first
    while second == first: # prevents redrawing same ticket
        second = random.randint(1,valid_balance)
    third = second
    while third == second or third == first: #prevents drawing same ticket
        third = random.randint(1,valid_balance)
    winners.append(pick_winner(entries, first)) # first place
    winners.append(pick_winner(entries, second)) #second place
    winners.append(pick_winner(entries, third)) # third place
    
    first_prize = int(math.floor(bal * 0.85))
    second_prize = int(math.floor(bal * 0.1))
    third_prize = int(math.floor(bal * 0.05))
    donation = float(balance) - float(first_prize) - float(second_prize) - float(third_prize)
        
    print("First Place: ticket: "+ str(first)+ " winner: " + winners[0] + " prize: " + str(first_prize))
    print("Second Place: " + str(second) +" winner: " + winners[1] + " prize: " + str(second_prize))
    print("Third Place: " +str(third)+ " winner: "+ winners[2] + " prize: " + str(third_prize))
    print("Code Monkey Tax: " + str(round(donation,10)))
    send_payout(settings.donation_address, banano_to_raw(round(donation,10)))
    send_payout(winners[2], banano_to_raw(third_prize))
    send_payout(winners[1], banano_to_raw(second_prize))
    send_payout(winners[0], banano_to_raw(first_prize))

if __name__ == '__main__':
    main()

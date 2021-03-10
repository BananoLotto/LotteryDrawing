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

# get number of valid entries in the drawing
def get_valid_entries(address, balance):
    valid_entries = 0
    running_balance = 0
	
    # get transaction history
    response = wallet_api.get_transactions(address, -1)
    account = response.json()
	
    # check each transaction
    for tx in account.get('history'):
	# ignore sends
        if(tx.get('type') == "receive"):
            # convert raw banano amount to normal form and add to running balance
            amt = raw_to_banano(int(tx.get('amount')))
            running_balance = running_balance + amt
			
	    # check for valid entry (invalid if < 1 or coming from donation_account)
            if(amt >= 0 and tx.get('account') != settings.donation_account):
                valid_entries = valid_entries + math.floor(amt)
			
	    # stop when we hit the current balance
            if(running_balance >= balance):
                break
				
    return valid_entries

# get the list of entrants in the drawing
def get_entries(address, valid_entries):
    entry_count = 0
    response = wallet_api.get_transactions(address, -1)
    account = response.json()
    entries = []
	
    for tx in account.get('history'):	
        if(tx.get('type') == "receive"):		
            amt = raw_to_banano(int(tx.get('amount'))) # transaction amount						
            sender = tx.get('account') # transaction sender		
			
            # less than 1 BAN considered donation
	    # if transaction is >=1 and Donation Account is not the sender, create an entry	
            if(amt >= 1 and sender != settings.donation_account):
                d = {"entrant": sender, "entries": math.floor(amt)} # create entry for transaction
                entries.append(d)
                entry_count = entry_count + math.floor(amt)
				
            if(entry_count == valid_entries):
                break # stop when good
    print(f'{entry_count} = {valid_entries}')
    return entries
	
	
# shuffle entrants
def shuffle_entries(entries):
    return random.shuffle(entries)

# get entrant based on ticket number
def pick_winner(entries, ticket):
    for entrant in entries:
        amt = entrant.get('entries')
        ticket = ticket - amt
        if(ticket <= 0):
            return entrant

# send payout of amount to address
def send_payout(address, amount):
    try:
        response = wallet_api.send_banano(address, amount)
        response = response.json()
        if(response.get('block')):
            print("Prize sent to: " + address)
        else:
            print('Error sending payment to ' + address)
    except Exception as e:
        print('Error sending payment to ' + address)

def main():
    winners = []
	
    # receive all pending transactions on start
    wallet_api.receive_pending(settings.ban_account)
    # get the account balance and print
    balance = get_balance(settings.ban_account)
    print('Beginning Balance: ' + str(balance))
	
    # get the number of tickets
    ticket_count = get_valid_entries(settings.ban_account, balance)	
    print('Valid Entry Balance: ' + str(ticket_count))
	
    # get list of entrants and shuffle them
    entries = get_entries(settings.ban_account, ticket_count)
    random.shuffle(entries)
	
    # Generate First Prize Winner
    first = random.randint(1, ticket_count)
    
    # Generate Second Prize Winner
    second = first	
    while second == first: # prevents redrawing same ticket
        second = random.randint(1, ticket_count)
		
    # Generate Third Prize Winner	
    third = second
    while third == second or third == first: #prevents drawing same ticket
        third = random.randint(1, ticket_count)
		
    # Insert winning ticket entrant into winner list	
    winners.append(pick_winner(entries, first))
    winners.append(pick_winner(entries, second))
    winners.append(pick_winner(entries, third))
	
    # Prize Pool Cuts - floor percentages is for the code monkey
    first_prize = int(math.floor(balance * 0.85))
    second_prize = int(math.floor(balance * 0.1))
    third_prize = int(math.floor(balance * 0.05))
    donation = float(balance) - float(first_prize) - float(second_prize) - float(third_prize)

    print ("\n{:>14}  {:>15} {:>15} {:<30}\n".format('Prize','Ticket Number','Num. Entries','Winner'))
    print ("{:>10} BAN  {:>15} {:>15} {:<30}".format(first_prize, first, winners[0].get('entries'),winners[0].get('entrant')))
    print ("{:>10} BAN  {:>15} {:>15} {:<30}".format(second_prize, second, winners[1].get('entries'),winners[1].get('entrant')))
    print ("{:>10} BAN  {:>15} {:>15} {:<30}\n".format(third_prize, third, winners[2].get('entries'),winners[2].get('entrant')))

    send_payout(settings.donation_account, banano_to_raw(round(donation,10)))
    send_payout(winners[2].get('entrant'), banano_to_raw(third_prize))
    send_payout(winners[1].get('entrant'), banano_to_raw(second_prize))
    send_payout(winners[0].get('entrant'), banano_to_raw(first_prize))

if __name__ == '__main__':
    main()

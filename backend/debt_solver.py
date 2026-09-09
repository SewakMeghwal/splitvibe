"""
Debt Solver Module
Implements greedy graph debt simplification to minimize the total number of transactions
required to settle debts across a group.
"""

from typing import List, Dict, Any, Tuple

def simplify_debts(net_balances: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Given a map of {person_id: net_balance}, returns a list of minimal transactions:
    [{ "from": person_a, "to": person_b, "amount": round(val, 2) }]
    
    Positive net_balance = person is owed money (creditor).
    Negative net_balance = person owes money (debtor).
    """
    # Round to cents to prevent floating point inaccuracies
    balances = {person: round(amount, 2) for person, amount in net_balances.items() if round(amount, 2) != 0}
    
    debtors = []   # List of [person, amount_they_owe (>0)]
    creditors = [] # List of [person, amount_they_are_owed (>0)]
    
    for person, amount in balances.items():
        if amount < 0:
            debtors.append([person, -amount])
        elif amount > 0:
            creditors.append([person, amount])
            
    # Sort descending by magnitude to settle largest debts first
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)
    
    transactions = []
    
    i = 0
    j = 0
    
    while i < len(debtors) and j < len(creditors):
        debtor_name, owe_amt = debtors[i]
        creditor_name, receive_amt = creditors[j]
        
        settle_amt = min(owe_amt, receive_amt)
        settle_amt = round(settle_amt, 2)
        
        if settle_amt > 0.009:
            transactions.append({
                "from_user": debtor_name,
                "to_user": creditor_name,
                "amount": settle_amt
            })
            
        debtors[i][1] = round(owe_amt - settle_amt, 2)
        creditors[j][1] = round(receive_amt - settle_amt, 2)
        
        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1
            
    return transactions

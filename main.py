import random
import json
from itertools import combinations
from collections import Counter

#so I'll write it here and not in cards.json, cause it take time. It will be here.
RANK_MAP = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
    '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

#emoji
SUIT_EMOJIS = {
    'hearts': '♥', 
    'diamonds': '♦', 
    'clubs': '♣', 
    'spades': '♠'
}

#hand ranks
HAND_NAMES = [
    "High Card", "One Pair", "Two Pair", "Three of a Kind", 
    "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"
]

#returns a str like "A♠"
def get_card_label(card):
    return f"{card['rank']}{SUIT_EMOJIS[card['suit']]}"

#5 cards => tuple: (hand_rank, kicker1, kicker2, ex)
def evaluate_five_cards(cards):
    #converting ranks into numbers cause that's what we need
    ranks = sorted([RANK_MAP[c['rank']] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]
    
    #if flush every suit will be same, so we can check directly
    is_flush = len(set(suits)) == 1
    
    #straight check. if the difference between max and min is 4 - it can be straight, but we also need to make sure there are no duplicates
    is_straight = (max(ranks) - min(ranks) == 4) and len(set(ranks)) == 5

    #check for a lower straight
    if ranks == [14, 5, 4, 3, 2]:
        is_straight = True
        ranks = [5, 4, 3, 2, 1]

    #Check amount of frequancy of each rank and sort
    counts = Counter(ranks).most_common()
    counts.sort(key=lambda x: (x[1], x[0]), reverse=True)

    sorted_ranks_by_freq = [item[0] for item in counts]
    frequencies = [item[1] for item in counts]

    #Writing which combination did we get
    #Straight Flush
    if is_straight and is_flush:
        return (8, sorted_ranks_by_freq[0])

    #Four of a Kind
    if frequencies[0] == 4:
        return (7, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1])

    #Full House
    if frequencies[0] == 3 and frequencies[1] == 2:
        return (6, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1])

    #Flush
    if is_flush:
        return (5, ranks)

    #Straight
    if is_straight:
        return (4, sorted_ranks_by_freq[0])

    #Three of a Kind
    if frequencies[0] == 3:
        return (3, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1], sorted_ranks_by_freq[2])

    #Two Pair
    if frequencies[0] == 2 and frequencies[1] == 2:
        return (2, sorted_ranks_by_freq[0], sorted_ranks_by_freq[1], sorted_ranks_by_freq[2])

    #One Pair
    if frequencies[0] == 2:
        return (1, sorted_ranks_by_freq[0], ranks)

    #High Card
    return (0, ranks)
    

def get_best_combination(seven_cards):
    #check all possible combination with 5 cards out of 7
    all_possible_five = list(combinations(seven_cards, 5))
    
    #take the best
    return max(all_possible_five, key=evaluate_five_cards)
    

def start_game(player_names):
    #json load
    with open('cards.json', 'r') as file:
        deck = json.load(file)

    random.shuffle(deck)

    #2 cards for each player
    players = []
    for name in player_names:
        hand = [deck.pop(), deck.pop()]
        players.append({
            'name': name,
            'hand': hand
        })

    #show 5 cards on the table (just for now)
    table = [deck.pop() for _ in range(5)]

    #table cards
    print(f"\ntable: {' '.join(get_card_label(c) for c in table)}")
    print("-" * 40)

    #check each player
    for p in players:
        #write all 7 cards (2 in hand + 5 on table) and find the best combination of 5 cards
        all_cards = p['hand'] + table
        best_five = get_best_combination(all_cards)
        
        #save the best combination and the score for later use
        p['best_five'] = best_five
        p['score'] = evaluate_five_cards(best_five)
        
        #write the hand, best combination and its name
        hand_name = HAND_NAMES[p['score'][0]]
        hand_str = ' '.join(get_card_label(c) for c in p['hand'])
        best_str = ' '.join(get_card_label(c) for c in best_five)
        
        print(f"{p['name']:8} | Hand: {hand_str} | Best: {best_str} ({hand_name} or {p['score']})")

    #find the winner(or winners)
    highest_score = max(p['score'] for p in players)
    winners = [p['name'] for p in players if p['score'] == highest_score]

    print("-" * 40)
    if len(winners) > 1:
        print(f"split: {', '.join(winners)}")
    else:
        print(f"winner: {winners[0]}")
        
        
#the game
if __name__ == "__main__":
    players = ["Fedor", "Adam", "Indy", "Roman"]
    start_game(players)
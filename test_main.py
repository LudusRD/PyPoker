import unittest
from unittest.mock import patch
import main

class TestPokerGame(unittest.TestCase):

    def test_card_str(self):
        card = {'rank': 'A', 'suit': 'spades'}
        self.assertEqual(main.card_str(card), 'A\u2660')
        card = {'rank': '10', 'suit': 'hearts'}
        self.assertEqual(main.card_str(card), '10\u2665')

    def test_evaluate_high_card(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'K', 'suit': 'diamonds'},
            {'rank': 'Q', 'suit': 'clubs'},
            {'rank': 'J', 'suit': 'spades'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (0, 14, 13, 12, 11, 9))

    def test_evaluate_one_pair(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'A', 'suit': 'diamonds'},
            {'rank': 'Q', 'suit': 'clubs'},
            {'rank': 'J', 'suit': 'spades'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (1, 14, 12, 11, 9))

    def test_evaluate_two_pair(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'A', 'suit': 'diamonds'},
            {'rank': 'Q', 'suit': 'clubs'},
            {'rank': 'Q', 'suit': 'spades'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (2, 14, 12, 9))

    def test_evaluate_three_of_a_kind(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'A', 'suit': 'diamonds'},
            {'rank': 'A', 'suit': 'clubs'},
            {'rank': 'Q', 'suit': 'spades'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (3, 14, 12, 9))

    def test_evaluate_straight(self):
        cards = [
            {'rank': '10', 'suit': 'hearts'},
            {'rank': '9', 'suit': 'diamonds'},
            {'rank': '8', 'suit': 'clubs'},
            {'rank': '7', 'suit': 'spades'},
            {'rank': '6', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (4, 10))

    def test_evaluate_flush(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'K', 'suit': 'hearts'},
            {'rank': 'Q', 'suit': 'hearts'},
            {'rank': 'J', 'suit': 'hearts'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (5, 14, 13, 12, 11, 9))

    def test_evaluate_full_house(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'A', 'suit': 'diamonds'},
            {'rank': 'A', 'suit': 'clubs'},
            {'rank': 'K', 'suit': 'spades'},
            {'rank': 'K', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (6, 14, 13))

    def test_evaluate_four_of_a_kind(self):
        cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'A', 'suit': 'diamonds'},
            {'rank': 'A', 'suit': 'clubs'},
            {'rank': 'A', 'suit': 'spades'},
            {'rank': 'K', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (7, 14, 13))

    def test_evaluate_straight_flush(self):
        cards = [
            {'rank': 'K', 'suit': 'hearts'},
            {'rank': 'Q', 'suit': 'hearts'},
            {'rank': 'J', 'suit': 'hearts'},
            {'rank': '10', 'suit': 'hearts'},
            {'rank': '9', 'suit': 'hearts'}
        ]
        self.assertEqual(main.evaluate(cards), (8, 13))

    def test_best_hand(self):
        seven_cards = [
            {'rank': 'A', 'suit': 'hearts'},
            {'rank': 'K', 'suit': 'hearts'},
            {'rank': 'Q', 'suit': 'hearts'},
            {'rank': 'J', 'suit': 'hearts'},
            {'rank': '10', 'suit': 'hearts'},
            {'rank': '9', 'suit': 'hearts'},
            {'rank': '8', 'suit': 'hearts'}
        ]
        best = main.best_hand(seven_cards)
        self.assertEqual(len(best), 5)
        # The best hand is a royal flush, which is a straight flush with high card Ace (14)
        self.assertEqual(main.evaluate(best), (8, 14))

if __name__ == '__main__':
    unittest.main()

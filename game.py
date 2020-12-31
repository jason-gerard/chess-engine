import chess
from chess import *

from engine import Engine


class Game:

    def __init__(self, board: Board) -> None:
        self.board = board
        self.engine = Engine(board, 2)

    def play_random_moves(self):
        while not self.board.is_game_over(claim_draw=True):
            if self.board.turn:
                move = self.engine.select_move()
                print(f"AI moves to -> {move}")
                self.board.push(move)
            else:
                move = self.engine.get_random_move()
                print(f"You move to -> {move}")
                self.board.push(move)

            print(self.board)

        print(self.board.result(claim_draw=True))

    def play_person(self):
        while not self.board.is_game_over(claim_draw=True):
            if self.board.turn:
                move = self.engine.select_move()
                print(f"AI moves to -> {move}")
                self.board.push(move)
            else:
                next_move = input("Enter your move: ")
                move = chess.Move.from_uci(next_move)

                print(f"You move to -> {move}")
                self.board.push(move)

            print(self.board)

        print(self.board.result(claim_draw=True))

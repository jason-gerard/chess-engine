import chess
from game import Game


def main():
    board = chess.Board()
    game = Game(board)
    game.play_person()


if __name__ == "__main__":
    main()

import random
import chess
import chess.polyglot
from chess import *


class Engine:

    def __init__(self, board: Board, depth: int) -> None:
        self.board: Board = board
        self.move_history: List[Move] = []
        self.board_value: int = 0
        self.depth: int = depth

    def evaluate_board(self) -> int:
        if self.board.is_checkmate():
            if self.board.turn:
                return -9999
            else:
                return 9999
        if self.board.is_stalemate():
            return 0
        if self.board.is_insufficient_material():
            return 0

        wp = len(self.board.pieces(chess.PAWN, chess.WHITE))
        bp = len(self.board.pieces(chess.PAWN, chess.BLACK))
        wn = len(self.board.pieces(chess.KNIGHT, chess.WHITE))
        bn = len(self.board.pieces(chess.KNIGHT, chess.BLACK))
        wb = len(self.board.pieces(chess.BISHOP, chess.WHITE))
        bb = len(self.board.pieces(chess.BISHOP, chess.BLACK))
        wr = len(self.board.pieces(chess.ROOK, chess.WHITE))
        br = len(self.board.pieces(chess.ROOK, chess.BLACK))
        wq = len(self.board.pieces(chess.QUEEN, chess.WHITE))
        bq = len(self.board.pieces(chess.QUEEN, chess.BLACK))

        material = 100 * (wp - bp) + 320 * (wn - bn) + 330 * (wb - bb) + 500 * (wr - br) + 900 * (wq - bq)

        pawnsq = sum([pawntable[i] for i in self.board.pieces(chess.PAWN, chess.WHITE)])
        pawnsq = pawnsq + sum([-pawntable[chess.square_mirror(i)]
                               for i in self.board.pieces(chess.PAWN, chess.BLACK)])
        knightsq = sum([knightstable[i] for i in self.board.pieces(chess.KNIGHT, chess.WHITE)])
        knightsq = knightsq + sum([-knightstable[chess.square_mirror(i)]
                                   for i in self.board.pieces(chess.KNIGHT, chess.BLACK)])
        bishopsq = sum([bishopstable[i] for i in self.board.pieces(chess.BISHOP, chess.WHITE)])
        bishopsq = bishopsq + sum([-bishopstable[chess.square_mirror(i)]
                                   for i in self.board.pieces(chess.BISHOP, chess.BLACK)])
        rooksq = sum([rookstable[i] for i in self.board.pieces(chess.ROOK, chess.WHITE)])
        rooksq = rooksq + sum([-rookstable[chess.square_mirror(i)]
                               for i in self.board.pieces(chess.ROOK, chess.BLACK)])
        queensq = sum([queenstable[i] for i in self.board.pieces(chess.QUEEN, chess.WHITE)])
        queensq = queensq + sum([-queenstable[chess.square_mirror(i)]
                                 for i in self.board.pieces(chess.QUEEN, chess.BLACK)])

        local_kings_table = kingstable if self.get_piece_count() <= 5 else kingsendgametable

        kingsq = sum([local_kings_table[i] for i in self.board.pieces(chess.KING, chess.WHITE)])
        kingsq = kingsq + sum([-local_kings_table[chess.square_mirror(i)]
                               for i in self.board.pieces(chess.KING, chess.BLACK)])

        self.board_value = material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq

        if self.board.turn:
            return self.board_value
        else:
            return -self.board_value

    def update_eval(self, mov: Move, side: bool) -> None:
        # update piecequares
        movingpiece = self.board.piece_type_at(mov.from_square)
        if side:
            # update castling
            if (mov.from_square == chess.E1) and (mov.to_square == chess.G1):
                self.board_value -= rookstable[chess.H1]
                self.board_value += rookstable[chess.F1]
            elif (mov.from_square == chess.E1) and (mov.to_square == chess.C1):
                self.board_value -= rookstable[chess.A1]
                self.board_value += rookstable[chess.D1]
        else:
            # update castling
            if (mov.from_square == chess.E8) and (mov.to_square == chess.G8):
                self.board_value += rookstable[chess.H8]
                self.board_value -= rookstable[chess.F8]
            elif (mov.from_square == chess.E8) and (mov.to_square == chess.C8):
                self.board_value -= rookstable[chess.D8]
                self.board_value += rookstable[chess.A8]

        if movingpiece is not None:
            self.board_value = (self.board_value + self.get_tables()[movingpiece - 1][mov.to_square]) if side else (self.board_value - self.get_tables()[movingpiece - 1][mov.to_square])
            self.board_value = (self.board_value - self.get_tables()[movingpiece - 1][mov.from_square]) if side else (self.board_value + self.get_tables()[movingpiece - 1][mov.from_square])

        # update material
        if mov.drop is not None:
            if side:
                self.board_value += piecevalues[mov.drop - 1]
            else:
                self.board_value -= piecevalues[mov.drop - 1]

        # update promotion
        if mov.promotion is not None and movingpiece is not None:
            if side:
                self.board_value += (piecevalues[mov.promotion - 1] - piecevalues[movingpiece - 1])
                self.board_value -= (self.get_tables()[movingpiece - 1][mov.to_square]
                                     + self.get_tables()[mov.promotion - 1][mov.to_square])
            else:
                self.board_value -= (piecevalues[mov.promotion - 1] + piecevalues[movingpiece - 1])
                self.board_value += (self.get_tables()[movingpiece - 1][mov.to_square]
                                     - self.get_tables()[mov.promotion - 1][mov.to_square])

    def make_move(self, mov) -> None:
        self.update_eval(mov, self.board.turn)
        self.board.push(mov)

    def unmake_move(self) -> None:
        mov = self.board.pop()
        self.update_eval(mov, not self.board.turn)

    def quiesce(self, alpha: int, beta: int) -> int:
        stand_pat = self.evaluate_board()
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                self.make_move(move)
                score = -(self.quiesce(-beta, -alpha))
                self.unmake_move()

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
        return alpha

    def alphabeta(self, alpha: int, beta: int, depthleft: int) -> int:
        bestscore = -9999
        if depthleft == 0:
            return self.quiesce(alpha, beta)
        for move in self.board.legal_moves:
            self.make_move(move)
            score = -(self.alphabeta(-beta, -alpha, depthleft - 1))
            self.unmake_move()

            if score >= beta:
                return score
            if score > bestscore:
                bestscore = score
            if score > alpha:
                alpha = score
        return bestscore

    def select_move(self) -> Move:
        try:
            move = chess.polyglot.MemoryMappedReader("Perfect2017.bin").weighted_choice(self.board).move
            self.move_history.append(move)
            return move
        except:
            best_move = chess.Move.null()
            best_move_value = -99999
            alpha = -100000
            beta = 100000

            for move in self.board.legal_moves:
                self.make_move(move)
                current_board_value = -(self.alphabeta(-beta, -alpha, self.depth - 1))

                if current_board_value > best_move_value:
                    best_move_value = current_board_value
                    best_move = move

                if current_board_value > alpha:
                    alpha = current_board_value

                self.unmake_move()

            self.move_history.append(best_move)

            return best_move

    def get_random_move(self) -> Move:
        moves = self.board.legal_moves.__iter__()
        number_of_moves = self.board.legal_moves.count()
        next_move_index = random.randint(1, number_of_moves)

        for _ in range(next_move_index - 1):
            next(moves)

        return next(moves)

    def get_piece_count(self) -> int:
        wp = len(self.board.pieces(chess.PAWN, chess.WHITE))
        bp = len(self.board.pieces(chess.PAWN, chess.BLACK))
        wn = len(self.board.pieces(chess.KNIGHT, chess.WHITE))
        bn = len(self.board.pieces(chess.KNIGHT, chess.BLACK))
        wb = len(self.board.pieces(chess.BISHOP, chess.WHITE))
        bb = len(self.board.pieces(chess.BISHOP, chess.BLACK))
        wr = len(self.board.pieces(chess.ROOK, chess.WHITE))
        br = len(self.board.pieces(chess.ROOK, chess.BLACK))
        wq = len(self.board.pieces(chess.QUEEN, chess.WHITE))
        bq = len(self.board.pieces(chess.QUEEN, chess.BLACK))

        return sum([wp, bp, wn, bn, wb, bb, wr, br, wq, bq])

    def get_tables(self) -> List[List[int]]:
        return [pawntable, knightstable, bishopstable, rookstable, queenstable,
                kingstable if self.get_piece_count() <= 5 else kingsendgametable]


pawntable = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0
]

knightstable = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

bishopstable = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

rookstable = [
    0, 0, 0, 5, 5, 0, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]

queenstable = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 0, -10,
    0, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

kingstable = [
    20, 30, 10, 0, 0, 10, 30, 20,
    20, 20, 0, 0, 0, 0, 20, 20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30
]

kingsendgametable = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

piecetypes = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
piecevalues = [100, 320, 330, 500, 900]

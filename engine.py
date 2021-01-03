import random
import chess
from tables import Tables


class Engine:

    def __init__(self, board: chess.Board, depth: int) -> None:
        self.board: chess.Board = board
        self.move_history: chess.List[chess.Move] = []
        self.board_value: int = 0
        self.depth: int = depth
        self.tables = Tables()
        self.color = chess.WHITE
        self.opponent_color = chess.BLACK

        self.piece_values = [100, 320, 330, 500, 900]

    def evaluate_board(self) -> int:
        if self.board.is_checkmate():
            return -9999 if self.board.turn else 9999

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

        pawnsq = self.get_piece_table_sum_for_ai(chess.PAWN) + self.get_piece_table_sum_for_opponent(chess.PAWN)
        knightsq = self.get_piece_table_sum_for_ai(chess.KNIGHT) + self.get_piece_table_sum_for_opponent(chess.KNIGHT)
        bishopsq = self.get_piece_table_sum_for_ai(chess.BISHOP) + self.get_piece_table_sum_for_opponent(chess.BISHOP)
        rooksq = self.get_piece_table_sum_for_ai(chess.ROOK) + self.get_piece_table_sum_for_opponent(chess.ROOK)
        queensq = self.get_piece_table_sum_for_ai(chess.QUEEN) + self.get_piece_table_sum_for_opponent(chess.QUEEN)
        kingsq = self.get_piece_table_sum_for_ai(chess.KING) + self.get_piece_table_sum_for_opponent(chess.KING)

        self.board_value = material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq

        return self.board_value if self.board.turn else -self.board_value

    def update_eval(self, mov: chess.Move, side: bool) -> None:
        # update piecequares
        movingpiece = self.board.piece_type_at(mov.from_square)
        if side:
            # update castling
            if (mov.from_square == chess.E1) and (mov.to_square == chess.G1):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.H1]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.F1]
            elif (mov.from_square == chess.E1) and (mov.to_square == chess.C1):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.A1]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.D1]
        else:
            # update castling
            if (mov.from_square == chess.E8) and (mov.to_square == chess.G8):
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.H8]
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.F8]
            elif (mov.from_square == chess.E8) and (mov.to_square == chess.C8):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.D8]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.is_end_game())[chess.A8]

        if movingpiece is not None:
            self.board_value = (self.board_value + self.get_tables_for_ai()[movingpiece - 1][mov.to_square]) if side else (self.board_value - self.get_tables_for_ai()[movingpiece - 1][mov.to_square])
            self.board_value = (self.board_value - self.get_tables_for_ai()[movingpiece - 1][mov.from_square]) if side else (self.board_value + self.get_tables_for_ai()[movingpiece - 1][mov.from_square])

        # update material
        if mov.drop is not None:
            if side:
                self.board_value += self.piece_values[mov.drop - 1]
            else:
                self.board_value -= self.piece_values[mov.drop - 1]

        # update promotion
        if mov.promotion is not None and movingpiece is not None:
            if side:
                self.board_value += (self.piece_values[mov.promotion - 1] - self.piece_values[movingpiece - 1])
                self.board_value -= (self.get_tables_for_ai()[movingpiece - 1][mov.to_square]
                                     + self.get_tables_for_ai()[mov.promotion - 1][mov.to_square])
            else:
                self.board_value -= (self.piece_values[mov.promotion - 1] + self.piece_values[movingpiece - 1])
                self.board_value += (self.get_tables_for_ai()[movingpiece - 1][mov.to_square]
                                     - self.get_tables_for_ai()[mov.promotion - 1][mov.to_square])

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

    def select_move(self) -> chess.Move:
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

    def get_random_move(self) -> chess.Move:
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

    def is_end_game(self) -> bool:
        return self.get_piece_count() <= 5

    def get_piece_table_sum(self, piece: chess.PIECE_TYPES, color: chess.COLORS) -> int:
        table = self.tables.get_table_by_piece_and_color(piece, color, self.is_end_game())

        return sum([table[i] for i in self.board.pieces(piece, color)])

    def get_piece_table_sum_for_ai(self, piece: chess.PIECE_TYPES) -> int:
        return self.get_piece_table_sum(piece, self.color)

    def get_piece_table_sum_for_opponent(self, piece: chess.PIECE_TYPES) -> int:
        return -self.get_piece_table_sum(piece, self.opponent_color)

    def get_tables_for_ai(self):
        return self.tables.get_tables_by_color(self.color, self.is_end_game())

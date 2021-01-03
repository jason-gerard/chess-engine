import random
import chess
import chess.polyglot
from tables import Tables


class Engine:

    def __init__(self, board: chess.Board, depth: int) -> None:
        self.board: chess.Board = board
        self.board_value: int = 0
        self.depth: int = depth
        self.tables = Tables()
        self.color = chess.WHITE
        self.opponent_color = chess.BLACK

        self.piece_values = [100, 320, 330, 500, 900]

    def next_move(self) -> chess.Move:
        try:
            return self.get_next_move_from_opening_book()
        except IndexError:
            return self.calculate_next_move()

    def get_random_move(self) -> chess.Move:
        moves = self.board.legal_moves.__iter__()
        number_of_moves = self.board.legal_moves.count()
        next_move_index = random.randint(1, number_of_moves)

        for _ in range(next_move_index - 1):
            next(moves)

        return next(moves)

    def get_next_move_from_opening_book(self) -> chess.Move:
        return chess.polyglot.MemoryMappedReader("Perfect2017.bin").weighted_choice(self.board).move

    def calculate_next_move(self) -> chess.Move:
        best_move = chess.Move.null()
        best_move_value = -99999
        alpha = -100000
        beta = 100000

        for move in self.board.legal_moves:
            self.__make_move(move)
            current_board_value = -(self.dfs_with_alpha_beta_pruning(-beta, -alpha, self.depth - 1))

            if current_board_value > best_move_value:
                best_move_value = current_board_value
                best_move = move

            if current_board_value > alpha:
                alpha = current_board_value

            self.__unmake_move()

        return best_move

    def evaluate_board(self) -> int:
        if self.board.is_checkmate():
            return -9999 if self.board.turn else 9999

        if self.board.is_stalemate() or self.board.is_insufficient_material():
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

        pawnsq = self.__get_piece_table_sum_for_ai(chess.PAWN) + self.__get_piece_table_sum_for_opponent(chess.PAWN)
        knightsq = self.__get_piece_table_sum_for_ai(chess.KNIGHT) + self.__get_piece_table_sum_for_opponent(chess.KNIGHT)
        bishopsq = self.__get_piece_table_sum_for_ai(chess.BISHOP) + self.__get_piece_table_sum_for_opponent(chess.BISHOP)
        rooksq = self.__get_piece_table_sum_for_ai(chess.ROOK) + self.__get_piece_table_sum_for_opponent(chess.ROOK)
        queensq = self.__get_piece_table_sum_for_ai(chess.QUEEN) + self.__get_piece_table_sum_for_opponent(chess.QUEEN)
        kingsq = self.__get_piece_table_sum_for_ai(chess.KING) + self.__get_piece_table_sum_for_opponent(chess.KING)

        board_value = material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq

        return board_value if self.board.turn else -board_value

    def update_board_value(self, mov: chess.Move, side: bool) -> None:
        if side:
            # update castling
            if (mov.from_square == chess.E1) and (mov.to_square == chess.G1):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.H1]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.F1]
            elif (mov.from_square == chess.E1) and (mov.to_square == chess.C1):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.A1]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.D1]
        else:
            # update castling
            if (mov.from_square == chess.E8) and (mov.to_square == chess.G8):
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.H8]
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.F8]
            elif (mov.from_square == chess.E8) and (mov.to_square == chess.C8):
                self.board_value -= self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.D8]
                self.board_value += self.tables.get_table_by_piece_and_color(chess.ROOK, self.color, self.__is_end_game())[chess.A8]

        movingpiece = self.board.piece_type_at(mov.from_square)
        if movingpiece is not None:
            self.board_value = (self.board_value + self.__get_tables_for_ai()[movingpiece - 1][mov.to_square]) if side else (self.board_value - self.__get_tables_for_ai()[movingpiece - 1][mov.to_square])
            self.board_value = (self.board_value - self.__get_tables_for_ai()[movingpiece - 1][mov.from_square]) if side else (self.board_value + self.__get_tables_for_ai()[movingpiece - 1][mov.from_square])

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
                self.board_value -= (self.__get_tables_for_ai()[movingpiece - 1][mov.to_square]
                                     + self.__get_tables_for_ai()[mov.promotion - 1][mov.to_square])
            else:
                self.board_value -= (self.piece_values[mov.promotion - 1] + self.piece_values[movingpiece - 1])
                self.board_value += (self.__get_tables_for_ai()[movingpiece - 1][mov.to_square]
                                     - self.__get_tables_for_ai()[mov.promotion - 1][mov.to_square])

    def dfs_with_alpha_beta_pruning(self, alpha: int, beta: int, depthleft: int) -> int:
        bestscore = -9999
        if depthleft == 0:
            return self.quiescence_search(alpha, beta)
        for move in self.board.legal_moves:
            self.__make_move(move)
            score = -(self.dfs_with_alpha_beta_pruning(-beta, -alpha, depthleft - 1))
            self.__unmake_move()

            if score >= beta:
                return score
            if score > bestscore:
                bestscore = score
            if score > alpha:
                alpha = score
        return bestscore

    def quiescence_search(self, alpha: int, beta: int) -> int:
        self.board_value = self.evaluate_board()
        if self.board_value >= beta:
            return beta

        if alpha < self.board_value:
            alpha = self.board_value

        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                self.__make_move(move)
                score = -(self.quiescence_search(-beta, -alpha))
                self.__unmake_move()

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
        return alpha

    def __get_piece_count(self) -> int:
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

    def __get_piece_table_sum(self, piece, color) -> int:
        table = self.tables.get_table_by_piece_and_color(piece, color, self.__is_end_game())

        return sum([table[i] for i in self.board.pieces(piece, color)])

    def __get_piece_table_sum_for_ai(self, piece) -> int:
        return self.__get_piece_table_sum(piece, self.color)

    def __get_piece_table_sum_for_opponent(self, piece) -> int:
        return -self.__get_piece_table_sum(piece, self.opponent_color)

    def __get_tables_for_ai(self):
        return self.tables.get_tables_by_color(self.color, self.__is_end_game())

    def __make_move(self, mov) -> None:
        self.update_board_value(mov, self.board.turn)
        self.board.push(mov)

    def __unmake_move(self) -> None:
        mov = self.board.pop()
        self.update_board_value(mov, not self.board.turn)

    def __is_end_game(self) -> bool:
        return self.__get_piece_count() <= 5

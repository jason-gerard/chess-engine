# chess-engine

This is a chess engine / AI built with advanced game algorithms in order to decide and find the best move.

## Setup
```
python3 -m venv venv
python3 -m pip install -r requirements.txt
```
Now that all the requirements are setup you can run a game

## Running
In the main.py file by default it will run the AI against a random move generator. Switch the method `play_random_moves` to `play_person` to be able to input your own moves

## Algorithm
The AI uses minimax search algorithm with alpha-beta prunning to find the next best move. The evaulaton function will take into account pieces left on the board, their position, how dangerious a move is, and some other parameters to decide what is a good and bad move.

The AI will start the game by looking through a opening moves book.

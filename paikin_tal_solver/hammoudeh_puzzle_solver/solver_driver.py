from hammoudeh_puzzle_solver.puzzle_importer import Puzzle
from paikin_tal_solver.paikin_tal_solver import PaikinTalSolver


def paikin_tal_driver(images):
    """
    Runs the Paikin and Tal image solver.

    Args:
        images ([str]): An array of one or more image file path(s).
    """

    numb_puzzles = len(images) # Extract the number of puzzles
    puzzles = []  # Stores all of the puzzles.
    combined_pieces = []  # Merge all the pieces together
    for i in range(0, numb_puzzles):
        puzzles.append(Puzzle(i, images[i]))
        # Build a list of all pieces.
        combined_pieces.append(puzzles[i].pieces)

    # Create the Paikin Tal Solver
    paikin_tal_solver = PaikinTalSolver(numb_puzzles, combined_pieces)

    # Run the solver
    paikin_tal_solver.run()


if __name__ == "__main__":
    images = ["muffins_300x200.jpg"]
    paikin_tal_driver(images)

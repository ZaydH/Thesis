from puzzle_piece import PuzzlePiece, PieceRotation, PieceSide
from puzzle import Puzzle, PickleHelper
# noinspection PyUnresolvedReferences
from random import shuffle
import pickle

def perform_bottom_up_search(puzzle):
    """
    Starting from a single randomly selected piece, the solver tries to recreate the puzzle piece by piece.

    Args:
        puzzle (Puzzle): Input puzzle object.  Will reconstruct it from scratch.

    Returns (Puzzle): Puzzle built piece by piece a part of the solution.

    """
    # Get the piece breakdown information
    x_count = puzzle.x_piece_count
    y_count = puzzle.y_piece_count
    max_xy_piece_count = max(puzzle.x_piece_count, puzzle.y_piece_count)

    # Build an array that is larger than the puzzle as it may build in any direction around the board
    # noinspection PyUnusedLocal
    solution_grid = [[None for y in range(0, 2 * max_xy_piece_count + 1)] for x in range(0, 2 * max_xy_piece_count + 1)]
    # Initialize the board information
    upper_left = bottom_right = center = (max_xy_piece_count, max_xy_piece_count)

    # Get the puzzle's pieces and transfer them to the unexplored set.
    pieces = puzzle.pieces
    unexplored_set = [pieces[x][y] for y in range(0, y_count) for x in range(0, x_count) ]
    # shuffle(unexplored_set)

    # Select the first piece of the puzzle.
    mid_piece = (x_count // 2) + (y_count // 2) * x_count
    first_piece = unexplored_set.pop(mid_piece)  # Take a piece from the middle of the unexplored set.
    first_piece.assigned_location = center
    frontier_set = {center: first_piece}  # Add the first piece to the frontier set.
    solution_grid[center[0]][center[1]] = first_piece

    # Iterate until all pieces have been explored.
    while len(unexplored_set) > 0:

        if len(unexplored_set) <= 12:
            x = 1

        # Get the next piece to assign.
        next_piece = select_next_piece(solution_grid, unexplored_set, frontier_set, upper_left, bottom_right,
                                       x_count, y_count)

        # Remove the piece from the unexplored set and place it in the board
        unexplored_set.remove(next_piece)
        next_piece_coord = next_piece.assigned_location
        solution_grid[next_piece_coord[0]][next_piece_coord[1]] = next_piece

        # Assume piece is in the frontier. Checked below.
        frontier_set[next_piece_coord] = next_piece

        # Update the board edge coordinates.
        upper_left = (min(next_piece_coord[0], upper_left[0]), min(next_piece_coord[1], upper_left[1]))
        bottom_right = (max(next_piece_coord[0], bottom_right[0]), max(next_piece_coord[1], bottom_right[1]))

        # Check the pieces neighbors and see if they can be removed from the frontier set.
        # If they are and have no available neighbors, then remove the piece from the frontier.
        neighbor_coords = [next_piece_coord,
                           (next_piece_coord[0] - 1, next_piece_coord[1]),  # Left Neighbor
                           (next_piece_coord[0] + 1, next_piece_coord[1]),  # Right Neighbor
                           (next_piece_coord[0], next_piece_coord[1] - 1),  # Top neighbor
                           (next_piece_coord[0], next_piece_coord[1] + 1)]  # Bottom Neighbor
        for coord in neighbor_coords:
            neighbor = frontier_set.get(coord)
            if neighbor is not None:
                available_neighbors = determine_available_neighbors(neighbor, solution_grid,
                                                                    upper_left, bottom_right, x_count, y_count)
                # If it has no neighbors delete from the frontier
                if len(available_neighbors) == 0:
                    frontier_set.pop(coord)

    # Make the puzzle_solution
    return make_puzzle_solution(puzzle, solution_grid, upper_left, bottom_right, x_count, y_count)


def determine_available_neighbors(piece, solution_grid, upper_left, bottom_right, x_count, y_count):
    """

    Args:
        piece (PuzzlePiece):
        solution_grid ([PuzzlePiece]):
        upper_left ([int, int]):
        bottom_right ([int, int]):
        x_count (int):
        y_count (int):

    Returns ([PieceSide]): The sides of the specified Puzzle Piece where new pieces could be
                           placed.

    """
    # Verify the piece is assigned.
    assert piece.assigned_location is not None

    # Get the current board height
    board_width = bottom_right[0] - upper_left[0] + 1
    board_height = bottom_right[1] - upper_left[1] + 1
    # Get the longer and shorter sides of the puzzle
    min_xy_count = min(x_count, y_count)
    max_xy_count = max(x_count, y_count)

    # Determine whether it is valid to expand the board in either direction.
    width_expandable = height_expandable = False
    if board_width < min_xy_count or (min_xy_count < board_width < max_xy_count) \
            or (board_width == min_xy_count and board_height <= min_xy_count and board_width < max_xy_count):
        width_expandable = True

    if board_height < min_xy_count or (min_xy_count < board_height < max_xy_count) \
            or (board_height == min_xy_count and board_width <= min_xy_count and board_height < max_xy_count):
        height_expandable = True

    # Get all of the possible sides of a piece.
    all_sides = PieceSide.get_all_sides()
    available_neighbors = []
    for side in all_sides:
        # Get the coordinate of the neighbor piece
        neighbor_coord = piece.get_neighbor_coordinate(side)

        # If the location is already filled, definitely not an available neighbor
        if solution_grid[neighbor_coord[0]][neighbor_coord[1]] is not None:
            continue

        # If the piece is within the existing range, then only check if coordinate is open
        if upper_left[0] <= neighbor_coord[0] <= bottom_right[0] \
                and upper_left[1] <= neighbor_coord[1] <= bottom_right[1]:
            available_neighbors.append(side)
            continue

        # If the board is not expand and not within the existing board side, go to the next side
        if (side == PieceSide.left_side or side == PieceSide.right_side) and not width_expandable \
                or (side == PieceSide.bottom_side or side == PieceSide.top_side) and not height_expandable:
            continue
        # Otherwise, add the piece.
        else:
            available_neighbors.append(side)
            continue

    # Return the set of available neighbors.
    return available_neighbors

def select_next_piece(solution_grid, unexplored_set, frontier_set, upper_left, bottom_right, x_count, y_count):
    min_distance = None
    best_piece = None
    best_piece_coord = None
    best_piece_rotation = None

    for frontier_coord in frontier_set.keys():
        # Get the piece associated with the coordinate
        frontier_piece = frontier_set.get(frontier_coord)
        # Get the available neighbors of the frontier piece
        available_neighbors = determine_available_neighbors(frontier_piece, solution_grid, upper_left, bottom_right,
                                                            x_count, y_count)
        # in some rare cases (e.g. edge of board reached, a frontier piece may have no neighbors. If so continue.
        if len(available_neighbors) == 0:
            continue

        # Iterate through the unexplored pieces.
        for new_piece in unexplored_set:
            for rotation in PieceRotation.get_all_rotations():
                # Set the rotation of the piece.
                new_piece.rotation = rotation

                # Go through all available edges for the frontier pin.
                for frontier_edge in available_neighbors:
                    # Calculate the inter-piece distance.
                    piece_distance = PuzzlePiece.calculate_pieces_edge_distance(frontier_piece, frontier_edge,
                                                                                new_piece)
                    if best_piece is None or piece_distance < min_distance:
                        best_piece = new_piece
                        best_piece_coord = frontier_piece.get_neighbor_coordinate(frontier_edge)
                        best_piece_rotation = rotation
                        min_distance = piece_distance

    # Set the best piece's assigned location and rotation
    best_piece.assigned_location = best_piece_coord
    best_piece.rotation = best_piece_rotation
    # Return the best piece
    return best_piece


def make_puzzle_solution(puzzle, solution_grid, upper_left, bottom_right, x_count, y_count):
    # Build the output_grid
    # noinspection PyUnusedLocal
    puzzle._pieces = [[None for y in range(0, y_count)] for x in range(0, x_count)]
    for x in range(0, x_count):
        for y in range(0, y_count):
                if bottom_right[0] - upper_left[0] + 1 == x_count:
                    puzzle._pieces[x][y] = solution_grid[upper_left[0] + x][upper_left[1] + y]
                # Board is rotated
                # Need to swap x and y axis in solution since rotation
                else:
                    puzzle._pieces[x][y] = solution_grid[bottom_right[0] - y][upper_left[1] + x]
                    # Special mode to force a rotation
                    puzzle._pieces[x][y]._force_enable_rotate = True
                    puzzle._pieces[x][y].rotate_90_degrees()
                    # Disable special rotation mode
                    puzzle._pieces[x][y]._force_enable_rotate = False
                puzzle._pieces[x][y].assigned_location = (x, y)

    # Return a puzzle built from the individual pieces.
    return puzzle


if __name__ == '__main__':

    # tmp_puzzle = PickleHelper.importer("test_puzzle.pk")
    # tmp_puzzle.export_puzzle(Puzzle.DEFAULT_IMAGE_PATH + "puzzle_" + "test_puzzle.jpg")
    # tmp_solution_grid = PickleHelper.importer("solution_grid.pk")
    # tmp_upper_left = PickleHelper.importer("upper_left.pk")
    # tmp_bottom_right = PickleHelper.importer("bottom_right.pk")
    # tmp_x_count = PickleHelper.importer("x_count.pk")
    # tmp_y_count = PickleHelper.importer("y_count.pk")
    # tmp_puzzle = make_puzzle_solution(tmp_puzzle, tmp_solution_grid, tmp_upper_left,
    #                                   tmp_bottom_right, tmp_x_count, tmp_y_count)
    # tmp_puzzle.export_puzzle("images\pickle_solve.jpg")

    # puzzles = [("boat_100x100.jpg", (2, 2)), ("che_100x100.gif", (2, 2)),
    #            ("muffins_300x200.jpg", (6, 4)), ("duck.bmp", (10, 10)),
    #            ("two_faced_cat.jpg", (20, 10))]
    puzzles = [("muffins_300x200.jpg", (6, 4)), ("duck.bmp", (10, 10)),
               ("two_faced_cat.jpg", (20, 10))]
    for puzzle_info in puzzles:
        # Extract the information on the images
        img_filename = puzzle_info[0]
        (img_x_count, img_y_count) = puzzle_info[1]
        # Build a test puzzle
        test_puzzle = Puzzle(Puzzle.DEFAULT_IMAGE_PATH + img_filename)
        # test_puzzle.set_puzzle_image(Puzzle.DEFAULT_IMAGE_PATH + file )
        # test_puzzle.open_image()
        test_puzzle.convert_to_pieces(img_x_count, img_y_count)
        test_puzzle.export_puzzle(Puzzle.DEFAULT_IMAGE_PATH + "pre_" + img_filename)
        solved_puzzle = perform_bottom_up_search(test_puzzle)
        solved_puzzle.export_puzzle(Puzzle.DEFAULT_IMAGE_PATH + "solved_" + img_filename)

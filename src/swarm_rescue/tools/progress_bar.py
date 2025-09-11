import sys


def print_progress_bar(index: float, total: float, label: str):
    """
    Displays a progress bar in the console.

    The function calculates the progress percentage based on the current index and total,
    and then prints a progress bar with the corresponding percentage and label.

    Example Usage
        print_progress_bar(3, 10, "Processing")  # [====      ] 30%  Processing

    Args:
        index (float): The current index or position in the progress.
        total (float): The total number of items or steps in the progress.
        label (str): The label or description of the progress.

    Raises:
        ValueError: If index is less than zero.
        TypeError: If label is not a string.
    """

    if index > total:
        index = total

    if index < 0:
        raise ValueError("Invalid index value. "
                         "Index cannot be less than zero.")

    if not isinstance(label, str):
        raise TypeError("Label must be a string.")

    n_bar = 50  # Progress bar width
    progress = index / total
    percentage = int(100 * progress)
    sys.stdout.write('\r')
    sys.stdout.write("[{:<{}}] {:3.0f}%     {}".
                     format("=" * int(n_bar * progress), n_bar,
                            percentage, label))
    sys.stdout.flush()
import sys


def print_progress_bar(index: float, total: float, label: str):
    n_bar = 50  # Progress bar width
    progress = index / total
    percentage = int(100 * progress)
    sys.stdout.write('\r')
    sys.stdout.write("[{:<{}}] {:3.0f}%     {}".format("=" * int(n_bar * progress), n_bar, percentage, label))
    sys.stdout.flush()

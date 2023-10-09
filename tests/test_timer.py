import time

from spg_overlay.utils.timer import Timer


def test_start_timer():
    """Tests that the timer starts and the elapsed time is greater than 0.9"""
    timer = Timer()
    timer.start()
    time.sleep(0.2)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.19


def test_pause_and_resume_timer():
    """Tests that the timer can be paused and resumed and the elapsed time is correct"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    timer.pause_on()
    time.sleep(0.3)  # Simulate more processing time during pause
    timer.pause_off()
    time.sleep(0.1)  # Simulate more processing time after pause
    elapsed_time = timer.get_elapsed_time()
    assert abs(elapsed_time - 0.2) < 0.1


def test_stop_timer():
    """Tests that the timer can be stopped and the elapsed time is correct"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    timer.stop()
    time.sleep(0.2)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    assert abs(elapsed_time - 0.1) < 0.05


def test_restart_timer():
    """Tests that the timer can be restarted and the elapsed time is reset"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    timer.restart()
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time < 0.05


def test_get_elapsed_time_in_milliseconds():
    """Tests that the elapsed time can be obtained in milliseconds"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    elapsed_time_ms = timer.get_elapsed_time_in_milliseconds()
    assert abs(elapsed_time_ms - 100.0) < 50


def test_get_timer_state_as_string():
    """Tests that the timer state can be obtained as a string"""
    timer = Timer()
    assert timer.get_state_str() == "stopped"
    timer.start()
    assert timer.get_state_str() == "running"
    timer.pause_on()
    assert timer.get_state_str() == "pause"
    timer.pause_off()
    assert timer.get_state_str() == "running"
    timer.stop()
    assert timer.get_state_str() == "stopped"


def test_start_timer_multiple_times():
    """Tests that the timer can be started multiple times and the elapsed time is correct"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.09
    assert elapsed_time < 0.11

    timer.stop()
    timer.start()
    time.sleep(0.2)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.19
    assert elapsed_time < 0.21

    timer.stop()
    timer.start()
    time.sleep(0.3)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.29
    assert elapsed_time < 0.31


def test_pause_timer_multiple_times():
    """Tests that the timer can be paused multiple times and the elapsed time is correct"""
    timer = Timer()
    timer.start()
    time.sleep(0.1)  # Simulate some processing time
    timer.pause_on()
    time.sleep(0.2)  # Simulate some processing time
    timer.pause_off()
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.09
    assert elapsed_time < 0.11

    timer.pause_on()
    time.sleep(0.3)  # Simulate some processing time
    timer.pause_off()
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.09
    assert elapsed_time < 0.11

    timer.pause_on()
    time.sleep(0.4)  # Simulate some processing time
    timer.pause_off()
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0.09
    assert elapsed_time < 0.11

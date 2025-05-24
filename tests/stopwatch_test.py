import pytest
import time
from src.stw import Stopwatch

@pytest.fixture
def stopwatch():
    """Provides a fresh stopwatch instance for each test"""
    return Stopwatch()

# Basic functionality tests
def test_init():
    """Test both initialization modes of the stopwatch"""
    # Default initialization should not start the watch
    sw = Stopwatch()
    assert not sw.is_running
    
    # Auto-start initialization should start the watch
    sw = Stopwatch(start=True)
    assert sw.is_running

def test_properties(stopwatch):
    """Test accessing internal properties"""
    assert hasattr(stopwatch, '_start_time')
    assert hasattr(stopwatch, '_end_time')
    assert hasattr(stopwatch, '_laps')
    assert len(stopwatch._laps) == 0
    assert not stopwatch.is_running

def test_start_stop(stopwatch):
    stopwatch.start()
    assert stopwatch.is_running
    time.sleep(0.1)
    elapsed = stopwatch.stop()
    assert not stopwatch.is_running
    assert elapsed >= 0.1

def test_elapsed_time(stopwatch):
    stopwatch.start()
    time.sleep(0.1)
    running_time = stopwatch.elapsed_time()
    assert running_time >= 0.1
    stopwatch.stop()
    final_time = stopwatch.elapsed_time()
    assert final_time >= 0.1

def test_lap_timing(stopwatch):
    stopwatch.start()
    time.sleep(0.1)
    lap_time, total_time = stopwatch.lap("first")
    assert lap_time >= 0.1
    assert total_time >= 0.1
    
    time.sleep(0.1)
    lap_time, total_time = stopwatch.lap("second")
    assert lap_time >= 0.1
    assert total_time >= 0.2

def test_get_lap(stopwatch):
    stopwatch.start()
    time.sleep(0.1)
    stopwatch.lap("test_lap")
    lap_time, total_time = stopwatch.get_lap(name="test_lap")
    assert lap_time >= 0.1
    assert total_time >= 0.1

    with pytest.raises(ValueError):
        stopwatch.get_lap(index=0, name="test_lap")

def test_context_manager():
    with Stopwatch() as sw:
        assert sw.is_running
        time.sleep(0.1)
    assert not sw.is_running
    assert sw.elapsed_time() >= 0.1

def test_time_function(stopwatch):
    def slow_function():
        time.sleep(0.1)
        return 42

    elapsed, result = stopwatch.time_function(slow_function)
    assert elapsed >= 0.1
    assert result == 42

def test_multiple_stops(stopwatch):
    stopwatch.start()
    time.sleep(0.1)
    stopwatch.stop()
    with pytest.raises(RuntimeError):
        stopwatch.stop()

def test_lap_without_start(stopwatch):
    with pytest.raises(RuntimeError):
        stopwatch.lap()

def test_multiple_laps(stopwatch):
    """Test recording multiple laps with various timing patterns"""
    stopwatch.start()
    
    # First lap
    time.sleep(0.1)
    lap1_time, total1 = stopwatch.lap("first")
    assert lap1_time >= 0.1
    assert total1 >= 0.1
    
    # Quick second lap
    time.sleep(0.05)
    lap2_time, total2 = stopwatch.lap("second")
    assert lap2_time >= 0.05
    assert total2 >= 0.15
    
    # Longer third lap
    time.sleep(0.2)
    lap3_time, total3 = stopwatch.lap()  # Test auto-naming
    assert lap3_time >= 0.2
    assert total3 >= 0.35
    assert stopwatch._laps[-1][0] == "lap 3"  # Check auto-naming

def test_lap_retrieval(stopwatch):
    """Test various ways of retrieving lap information"""
    stopwatch.start()
    
    # Record some laps
    time.sleep(0.1)
    stopwatch.lap("first")
    time.sleep(0.1)
    stopwatch.lap("second")
    
    # Test retrieval by index
    lap_time, total = stopwatch.get_lap(index=0)
    assert lap_time >= 0.1
    
    # Test retrieval by name
    lap_time, total = stopwatch.get_lap(name="second")
    assert lap_time >= 0.1
    
    # Test invalid lap name
    with pytest.raises(ValueError):
        stopwatch.get_lap(name="nonexistent")

def test_edge_cases(stopwatch):
    """Test various edge cases and error conditions"""
    # Can't stop before starting
    with pytest.raises(RuntimeError):
        stopwatch.stop()
    
    # Can't lap before starting
    with pytest.raises(RuntimeError):
        stopwatch.lap()
    
    # Start and immediate stop
    stopwatch.start()
    time.sleep(0.001)  # Minimal delay
    elapsed = stopwatch.stop()
    assert elapsed > 0
    
    # Can't lap after stopping
    with pytest.raises(RuntimeError):
        stopwatch.lap()

def test_nested_timing():
    """Test nested stopwatch usage with context managers"""
    with Stopwatch() as outer:
        time.sleep(0.1)
        with Stopwatch() as inner:
            time.sleep(0.1)
        assert inner.elapsed_time() >= 0.1
    assert outer.elapsed_time() >= 0.2

def test_function_timing_with_args(stopwatch):
    """Test timing functions with various argument patterns"""
    def complex_function(x, y, *, multiplier=1):
        time.sleep(0.1)
        return (x + y) * multiplier
    
    # Test with positional args
    elapsed, result = stopwatch.time_function(complex_function, 2, 3)
    assert elapsed >= 0.1
    assert result == 5
    
    # Test with keyword args
    elapsed, result = stopwatch.time_function(
        complex_function, 2, 3, multiplier=2
    )
    assert elapsed >= 0.1
    assert result == 10

def test_lap_naming_sequence(stopwatch):
    """Test automatic lap naming sequence"""
    stopwatch.start()
    
    # Check auto-incrementing lap names
    for i in range(3):
        time.sleep(0.01)
        _, _ = stopwatch.lap()
        assert stopwatch._laps[i][0] == f"lap {i+1}"

def test_elapsed_since_lap(stopwatch):
    """Test elapsed time since specific laps"""
    stopwatch.start()
    
    # Test elapsed since last lap with no laps
    with pytest.raises(ValueError):
        stopwatch.elapsed_since_lap()
    
    # First lap
    time.sleep(0.1)
    stopwatch.lap("first")
    time.sleep(0.05)
    elapsed = stopwatch.elapsed_since_lap()
    assert elapsed >= 0.05
    
    # Second lap
    time.sleep(0.1)
    stopwatch.lap("second")
    
    # Test elapsed since named lap
    time.sleep(0.05)
    elapsed = stopwatch.elapsed_since_lap("first")
    assert elapsed >= 0.15  # 0.1 + 0.05
    
    # Test invalid lap name
    with pytest.raises(ValueError):
        stopwatch.elapsed_since_lap("nonexistent")

def test_string_representations(stopwatch):
    """Test string representation methods"""
    # Test initial state
    assert str(stopwatch) == "Stopwatch(running=False)"
    assert repr(stopwatch) == "Stopwatch(running=False)"
    
    # Test running state
    stopwatch.start()
    time.sleep(0.1)
    s = str(stopwatch)
    assert s.startswith("Stopwatch(running=True, elapsed_time=")
    assert "elapsed_since_lap" not in s
    
    # Test with laps
    stopwatch.lap("test")
    time.sleep(0.1)
    s = str(stopwatch)
    assert s.startswith("Stopwatch(running=True, elapsed_time=")
    assert "elapsed_since_lap=" in s
    
    # Test stopped state
    stopwatch.stop()
    s = str(stopwatch)
    assert s.startswith("Stopwatch(running=False, elapsed_time=")
    assert "elapsed_since_lap=" in s

def test_elapsed_time_edge_cases(stopwatch):
    """Test edge cases for elapsed_time method"""
    # Test without starting
    with pytest.raises(ValueError):
        stopwatch.elapsed_time()
    
    # Test multiple start-stops
    stopwatch.start()
    time.sleep(0.1)
    first_time = stopwatch.stop()
    
    # Should still return the same time after stopping
    assert abs(stopwatch.elapsed_time() - first_time) < 0.001
    
    # Start again should reset timing
    stopwatch.start()
    time.sleep(0.2)
    second_time = stopwatch.stop()
    assert second_time >= 0.2
    assert second_time != first_time

def test_get_lap_edge_cases(stopwatch):
    """Test edge cases for get_lap method"""
    stopwatch.start()
    stopwatch.lap("test")
    
    # Test negative index
    with pytest.raises(ValueError):
        stopwatch.get_lap(index=-1)
    
    # Test out of bounds index
    with pytest.raises(ValueError):
        stopwatch.get_lap(index=1)
    
    # Test empty args
    with pytest.raises(ValueError):
        stopwatch.get_lap()
    
    # Test both args
    with pytest.raises(ValueError):
        stopwatch.get_lap(index=0, name="test")

def test_lap_naming_duplicates(stopwatch):
    """Test behavior with duplicate lap names"""
    stopwatch.start()
    
    # Create two laps with the same name
    time.sleep(0.1)
    first_lap = stopwatch.lap("duplicate")
    time.sleep(0.1)
    second_lap = stopwatch.lap("duplicate")
    
    # get_lap should return the first occurrence
    retrieved_lap = stopwatch.get_lap(name="duplicate")
    assert retrieved_lap == first_lap

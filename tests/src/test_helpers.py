import logging
from unittest.mock import patch, MagicMock
from src.helpers import check_dir, create_logger, CustomThread

@patch('os.makedirs')
def test_check_dir(mock_makedirs):
    # Test case where directory does not exist
    check_dir("test_dir")
    mock_makedirs.assert_called_once_with("test_dir")


def test_create_logger():
    logger = create_logger("test_logger", "/logs/test_log.txt")
    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG

def test_CustomThread():
    def dummy_function():
        return "Thread finished"

    thread = CustomThread(target=dummy_function)
    thread.start()
    result = thread.join()
    assert result == "Thread finished"
    assert thread.is_alive() is False
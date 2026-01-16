"""日志系统测试 - TDD 第一步：编写失败的测试。"""

import logging

from src.core.logger import setup_logger


class TestLogger:
    """日志系统测试类。"""

    def test_setup_logger_returns_logger_instance(self):
        """测试 setup_logger 返回 Logger 实例。"""
        # Act
        logger = setup_logger(__name__)

        # Assert
        assert isinstance(logger, logging.Logger)
        assert logger.name == __name__

    def test_logger_has_console_handler(self):
        """测试日志器有控制台处理器。"""
        # Act
        logger = setup_logger("test_logger")

        # Assert
        assert len(logger.handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_logger_can_log_messages(self, caplog):
        """测试日志器可以记录消息。"""
        # Arrange
        logger = setup_logger("test_logger")

        # Act
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Assert
        assert "Test info message" in caplog.text
        assert "Test warning message" in caplog.text
        assert "Test error message" in caplog.text

    def test_logger_does_not_add_duplicate_handlers(self):
        """测试多次调用 setup_logger 不会添加重复的处理器。"""
        # Act
        logger1 = setup_logger("test_logger")
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_logger("test_logger")
        handler_count_2 = len(logger2.handlers)

        # Assert
        assert handler_count_1 == handler_count_2

    def test_logger_returns_existing_logger_when_handlers_exist(self):
        """测试当日志器已有处理器时，直接返回而不添加新处理器。"""
        # Arrange
        logger_name = "test_existing_logger"
        logger1 = setup_logger(logger_name)
        initial_handler_count = len(logger1.handlers)

        # Act - 再次调用，应该检测到已有处理器并直接返回
        logger2 = setup_logger(logger_name)

        # Assert
        assert logger1 is logger2  # 应该是同一个实例
        assert len(logger2.handlers) == initial_handler_count  # 处理器数量不变

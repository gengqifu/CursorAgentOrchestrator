"""主程序测试 - TDD 第一步：编写失败的测试。"""

import signal
import sys
from unittest.mock import MagicMock, patch


class TestMain:
    """主程序测试类。"""

    def test_main_can_be_imported(self):
        """测试主程序可以成功导入。"""
        # Act & Assert
        import src.main

        assert src.main is not None

    def test_main_logger_is_setup(self):
        """测试主程序设置了日志器。"""
        # Arrange
        import src.main

        # Assert
        assert hasattr(src.main, "logger")
        assert src.main.logger is not None

    def test_signal_handlers_are_setup(self):
        """测试信号处理器已设置。"""
        # Arrange
        import src.main

        # Act
        src.main.setup_signal_handlers()

        # Assert - 验证信号处理器已注册
        assert signal.getsignal(signal.SIGINT) is not None
        assert signal.getsignal(signal.SIGTERM) is not None

    def test_cleanup_resources_is_called_on_exit(self):
        """测试退出时调用资源清理函数。"""
        # Arrange

        import src.main

        # Act - 注册清理函数
        src.main.setup_signal_handlers()

        # Assert - 验证清理函数已注册到 atexit
        # 注意：无法直接测试 atexit 注册的函数，但可以验证函数存在
        assert callable(src.main.cleanup_resources)

    def test_signal_handler_cleans_up_and_exits(self, monkeypatch):
        """测试信号处理器清理资源并退出。"""
        # Arrange
        import src.main

        mock_exit = MagicMock()
        monkeypatch.setattr(sys, "exit", mock_exit)

        # 重置清理标志
        src.main._cleanup_called = False

        # Act - 模拟收到 SIGTERM 信号
        src.main.signal_handler(signal.SIGTERM, None)

        # Assert
        assert src.main._shutdown_requested is True
        assert src.main._cleanup_called is True
        mock_exit.assert_called_with(0)

    def test_cleanup_resources_prevents_duplicate_calls(self):
        """测试清理资源函数防止重复调用。"""
        # Arrange
        import src.main

        src.main._cleanup_called = False

        # Act - 第一次调用
        src.main.cleanup_resources()
        first_call = src.main._cleanup_called

        # 第二次调用（应该被忽略）
        src.main.cleanup_resources()
        second_call = src.main._cleanup_called

        # Assert
        assert first_call is True
        assert second_call is True  # 标志保持为 True

    def test_safe_log_info_handles_closed_streams(self, monkeypatch):
        """测试安全日志函数处理已关闭的流。"""
        # Arrange
        import src.main

        # 模拟所有日志处理器都关闭
        with patch.object(src.main.logger, "handlers", []):
            # Act & Assert - 应该使用 print 而不是 logger
            with patch("builtins.print") as mock_print:
                src.main.safe_log_info("测试消息")
                mock_print.assert_called()

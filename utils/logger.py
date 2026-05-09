"""轻量日志工具。

项目不引入复杂日志框架，统一通过这个函数获取 logger，避免每个模块重复配置 handler。
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """获取带统一格式的 logger。"""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # 只在第一次创建 logger 时添加控制台 handler，避免重复打印同一条日志。
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

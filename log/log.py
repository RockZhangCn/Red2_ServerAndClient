import logging
import sys

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s @ "%(filename)s":%(lineno)3d|: %(message)s')
formatter = logging.Formatter(
    '%(asctime)s @ "%(filename)s":%(lineno)3d|:- %(levelname)s - %(message)s - File "%(pathname)s", line %(lineno)d ')
formatter = logging.Formatter('%(asctime)s @ "%(pathname)s:%(lineno)d"[%(levelname)s]: %(message)s',
                              "%Y-%m-%d %H:%M:%S")


# StreamHandler


# def setup_logging(file):
#     logger.setLevel(logging.DEBUG)
#     formatter = logging.Formatter('%(asctime)s @ %(filename)s:%(lineno)3d|: %(message)s')
#
#     # StreamHandler
#     stream_handler = logging.StreamHandler(sys.stdout)
#     stream_handler.setLevel(level=logging.DEBUG)
#     stream_handler.setFormatter(formatter)
#     logger.addHandler(stream_handler)

# FileHandler
# file_handler = logging.FileHandler(file)
# file_handler.setLevel(level=logging.INFO)
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)


class ColorHandler000(logging.Handler):
    """彩色日志handler，根据不同级别的日志显示不同颜色"""
    bule = 36
    yellow = 33

    def __init__(self):
        logging.Handler.__init__(self)
        self.formatter_new = logging.Formatter(
            '%(asctime)s - %(name)s - "%(filename)s" - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S")
        # 对控制台日志单独优化显示和跳转，单独对字符串某一部分使用特殊颜色，主要用于第四种模板，以免filehandler和mongohandler中带有\033

    @classmethod
    def _my_align(cls, string, length):
        if len(string) > length * 2:
            return string
        custom_length = 0
        for w in string:
            custom_length += 1 if cls._is_ascii_word(w) else 2
        if custom_length < length:
            place_length = length - custom_length
            string += ' ' * place_length
        return string

    @staticmethod
    def _is_ascii_word(w):
        if ord(w) < 128:
            return True

    def emit(self, record):
        """
        30    40    黑色
        31    41    红色
        32    42    绿色
        33    43    黃色
        34    44    蓝色
        35    45    紫红色
        36    46    青蓝色
        37    47    白色
        :type record:logging.LogRecord
        :return:
        """
        self.__emit(record)  # 其他模板

    def __emit_for_fomatter4_linux(self, record):
        """
        当使用模板4针对linxu上的终端打印优化显示
        :param record:
        :return:
        """
        # noinspection PyBroadException,PyPep8
        try:
            msg = self.format(record)
            file_formatter = ' ' * 10 + '\033[7mFile "%s", line %d\033[0m' % (record.pathname, record.lineno)
            if record.levelno == 10:
                print('\033[0;32m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 20:
                print('\033[0;34m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 30:
                print('\033[0;33m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 40:
                print('\033[0;35m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 50:
                print('\033[0;31m%s' % self._my_align(msg, 150) + file_formatter)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def __emit_for_fomatter4_pycahrm(self, record):
        """
        当使用模板4针对pycahrm的打印优化显示
        :param record:
        :return:
        """
        #              \033[0;93;107mFile "%(pathname)s", line %(lineno)d, in %(funcName)s\033[0m
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            # for_linux_formatter = ' ' * 10 + '\033[7m;File "%s", line %d\033[0m' % (record.pathname, record.lineno)
            file_formatter = ' ' * 10 + '\033[0;93;107mFile "%s", line %d\033[0m' % (record.pathname, record.lineno)
            if record.levelno == 10:
                print('\033[0;32m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 绿色
            elif record.levelno == 20:
                print('\033[0;36m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 青蓝色
            elif record.levelno == 30:
                print('\033[0;92m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 蓝色
            elif record.levelno == 40:
                print('\033[0;35m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 紫红色
            elif record.levelno == 50:
                print('\033[0;31m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 血红色
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # NOQA
            self.handleError(record)

    def __emit(self, record):
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            if record.levelno == 10:
                print('\033[0;32m%s\033[0m' % msg)  # 绿色
            elif record.levelno == 20:
                print('\033[0;%sm%s\033[0m' % (self.bule, msg))  # 青蓝色 36    96
            elif record.levelno == 30:
                print('\033[0;%sm%s\033[0m' % (self.yellow, msg))
            elif record.levelno == 40:
                print('\033[0;35m%s\033[0m' % msg)  # 紫红色
            elif record.levelno == 50:
                print('\033[0;31m%s\033[0m' % msg)  # 血红色
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # NOQA
            self.handleError(record)


stream_handler = logging.StreamHandler(sys.stdout)
stream_handler = ColorHandler000()
stream_handler.setLevel(level=logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# logger.info("zhang")
# logger.debug("zhang")
# logger.warning("zhang")
# logger.error("zhang")
# logger.fatal("zhang")

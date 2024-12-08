import json
import logging.config
import unittest
from typing import final

import yaml
from dotenv import load_dotenv

import langfarm_tracing.core

base_dir = __file__[:-len('/tests/base.py')]
langfarm_tracing.core.env_path = base_dir


def config_log(log_file: str):
    # 读取 yaml 格式的日志配置
    with open(log_file) as f:
        log_config = yaml.full_load(f)
        out_log_file = log_config['handlers']['file_handler']['filename']
        log_config['handlers']['file_handler']['filename'] = f'{base_dir}/{out_log_file}'
        logging.config.dictConfig(log_config)


logger = logging.getLogger(__name__)


class BaseTestCase(unittest.TestCase):

    @classmethod
    @final
    def setUpClass(cls):
        """
        初始化配置: 日志(logging_dev.yaml)；环境变量(.env)。

        子类不要覆盖，使用 _set_up_class() 代替 setUpClass()
        :return:
        """
        # 配置日志

        log_file = f'{base_dir}/logging_dev.yaml'
        config_log(log_file)

        # 打印空行
        print()
        logger.info("配置 log_file = %s", log_file)

        # settings .env path
        logger.info("settings .env path=%s/.env", langfarm_tracing.core.env_path)
        # load .env
        dotenv_file = f'{base_dir}/.env'
        logger.info("配置 .env = %s", dotenv_file)
        load_dotenv(dotenv_file, verbose=True)

        cls._set_up_class()

    @classmethod
    def _set_up_class(cls):
        pass

    @classmethod
    def read_json_file(cls, filename) -> dict:
        """
        从 filename 读取 json
        :param filename: 相对于 tests/mock-data 的文件
        :return: 返回 dict
        """
        with open(f"{base_dir}/tests/mock-data/{filename}") as f:
            return json.load(f)

    @classmethod
    def read_file_to_str(cls, filename) -> str:
        """
        从 filename 读取 json
        :param filename: 相对于 tests/mock-data 的文件
        :return: 返回 dict
        """
        with open(f"{base_dir}/tests/mock-data/{filename}") as f:
            return f.read()

    def setUp(self):
        # 打印空行
        print()


if __name__ == '__main__':
    unittest.main()

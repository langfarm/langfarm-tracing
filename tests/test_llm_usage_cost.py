import json
import logging
import unittest
from decimal import Decimal

from tests.base import BaseTestCase
from langfarm_tracing.crud.langfuse import find_model_by_cache

logger = logging.getLogger(__name__)

class MyTestCase(BaseTestCase):
    def test_llm_usage_cal_cost(self):
        post_data = json.loads(self.read_file_to_str('trace-01-part2.json'))
        project_id = 'cm42wglph0006pmicl9y9o7r8'
        model_name = post_data['batch'][0]['body']['model']
        usage = post_data['batch'][0]['body']['usage']
        input_tokens = usage['input']
        output_tokens = usage['output']
        unit = usage['unit']
        logger.info("model_name = %s, usage = %s", model_name, usage)
        assert model_name
        assert input_tokens
        assert output_tokens
        assert unit

        model = find_model_by_cache(model_name, project_id, unit)
        logger.info("find model = %s",  model.to_dict())
        assert model

        input_cost = input_tokens * model.input_price
        output_cost = output_tokens * model.output_price

        logger.info("input_price = %s, output_price = %s", model.input_price, model.output_price)
        logger.info("input_cost = %s, output_cost = %s", input_cost, output_cost)
        assert input_cost == Decimal("0.0000152")
        assert output_cost == Decimal("0.000064")


if __name__ == '__main__':
    unittest.main()

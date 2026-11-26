import ast
from pathlib import Path
import unittest


class BudgetContractTests(unittest.TestCase):
    def test_single_job_budget_is_bounded_at_two_fifty(self):
        source = Path(__file__).with_name("runner.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "MAX_JOB_BUDGET_USD"
        }
        self.assertEqual(assignments["MAX_JOB_BUDGET_USD"], 2.50)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        conversations = [
            node for node in calls
            if isinstance(node.func, ast.Name) and node.func.id == "Conversation"
        ]
        self.assertEqual(len(conversations), 1)
        keyword = next(k for k in conversations[0].keywords if k.arg == "max_budget_per_run")
        self.assertIsInstance(keyword.value, ast.Name)
        self.assertEqual(keyword.value.id, "MAX_JOB_BUDGET_USD")


if __name__ == "__main__":
    unittest.main()

from gpt_function_decorator import gpt_function


def test_that_at_least_it_doesnt_bug_when_called():

    @gpt_function
    def fibonacci(n):
        """Bla bla bla"""

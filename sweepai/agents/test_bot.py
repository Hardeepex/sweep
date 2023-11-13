import re

from sweepai.agents.modify_bot import strip_backticks
from sweepai.core.chat import ChatGPT
from sweepai.core.entities import Message
from sweepai.utils.github_utils import ClonedRepo
from sweepai.utils.jedi_utils import (
    get_all_defined_functions,
    get_references_from_defined_function,
    setup_jedi_for_file,
)
from sweepai.utils.regex_utils import xml_pattern
from sweepai.utils.unittest_utils import fuse_scripts, split_script

test_prompt = """\
# Code
File path: {file_path}
{changes_made}

{code}

# Instructions
Write unit tests for the above function. Cover every possible edge case using the function's dependencies."""

test_prompt_response_format = """\
<mock_identification>
# Entities to mock #
Identify all return objects from expensive operations entities we need to mock. Copy the code snippets from code_to_test that reflect where this mock is used and accessed.
```
code snippet of the mocked object's usage
```

# Access method #
Identify the access method of the entity we are trying to mock, for example, if we have `return_obj = expensive_operation()`, identify all occurrences of `return_obj.attribute` or `return_obj["key"]`.

Then, for each chain of accesses like return_obj.foo["key"].bar, list the access type at each step of the chain and how they should be mocked, like
- return_obj.foo is an attribute method so return_obj should be mocked like MagicMock.foo
- return_obj.foo["key"] is a dictionary access so return_obj.foo should be mocked like {{"key": MagicMock}}
- return_obj.foo["key"].bar is an attribute method so return_obj.foo["key"] should be mocked like MagicMock.bar

# Mock Code #
Write a mock that perfectly mocks this access method.
</mock_identification>

<code>
Unit test that uses the mocked response in the setUp method (and optionally the tearDown method).
</code>"""

test_system_prompt = f"""\
You're an expert Python QA engineer and your job is to write a unit test for the following. Respond in the following format:

{test_prompt_response_format}"""

test_user_prompt = rf"""<code_to_test>
{{code_to_test}}
</code_to_test>

Write a unit test using the unittest module for the {{method_name}} method. Respond in the following format:

{test_prompt_response_format}"""

test_extension_format = """\
<test_analysis>
Identify all cases that should be unit-tested.
</test_analysis>

<code>
```
The additional unit test that uses the mocks defined in the original unit test. Format it like

class TestNameOfModule(unittest.TestCase):
    ...

    def test_function(self, mocks...):
        ... # the test here
```
</code>"""

test_extension_prompt = rf"""You're an expert Python QA engineer and your job is to write a unit test for the following. Respond in the following format:

{test_extension_format}"""

test_extension_user_prompt = rf"""<code_to_test>
{{code_to_test}}
</code_to_test>

<current_unit_test>
```
{{current_unit_test}}
```
</current_unit_test>

Extend the unit tests using the unittest module for the {{method_name}} method. Respond in the following format:

{test_extension_prompt}"""


# This class should handle appending or creating new tests
class TestBot(ChatGPT):
    def write_test(
        self,
        additional_messages: list[Message] = [],
        snippets_str="",
        file_path: str = "",  # file path of the source file to test
        update_snippets_code: str = "",
        request="",
        changes_made="",
        cloned_repo: ClonedRepo = None,
        **kwargs,
    ):
        # self.model = (
        #     DEFAULT_GPT4_32K_MODEL
        #     if (self.chat_logger and self.chat_logger.is_paying_user())
        #     else DEFAULT_GPT35_MODEL
        # )
        self.messages = [
            Message(
                role="system",
                content=test_system_prompt,
                key="system",
            )
        ]
        self.messages.extend(additional_messages)

        test_extension = ChatGPT.from_system_message_string(
            test_extension_prompt, chat_logger=self.chat_logger
        )
        test_extension.messages.extend(additional_messages)

        script, tree = setup_jedi_for_file(
            project_dir=cloned_repo.repo_dir,
            file_full_path=f"{cloned_repo.repo_dir}/{file_path}",
        )

        all_defined_functions = get_all_defined_functions(script=script, tree=tree)
        generated_code_sections = []
        for fn_def in all_defined_functions:
            if "__init__" in fn_def.name:
                continue
            full_file_code = cloned_repo.get_file_contents(file_path)
            script, tree = setup_jedi_for_file(
                project_dir=cloned_repo.repo_dir,
                file_full_path=f"{cloned_repo.repo_dir}/{file_path}",
            )
            function_and_reference = get_references_from_defined_function(
                fn_def,
                script,
                tree,
                f"{cloned_repo.repo_dir}/{file_path}",
                full_file_code,
            )
            if function_and_reference.function_code.count("\n") < 20:
                continue
            recent_file_contents = cloned_repo.get_file_contents(file_path=file_path)
            code = f"<original_code>\n{recent_file_contents}</original_code>\n"
            code += function_and_reference.serialize(tag="function_to_test")
            extract_response = self.chat(
                test_user_prompt.format(
                    code_to_test=function_and_reference.function_code,
                    method_name=function_and_reference.function_name,
                )
            )
            self.messages = self.messages[:-2]

            code_xml_pattern = xml_pattern("code")

            generated_test = re.search(code_xml_pattern, extract_response, re.DOTALL)
            generated_test = strip_backticks(generated_test.group(1))

            # Check the unit test here and try to fix it
            extension_results = test_extension.chat(
                test_extension_user_prompt.format(
                    code_to_test=function_and_reference.function_code,
                    current_unit_test=generated_test,
                    method_name=function_and_reference.function_name,
                )
            )

            test_extension = re.search(code_xml_pattern, extension_results, re.DOTALL)
            test_extension = strip_backticks(test_extension.group(1))

            decomposed_script = split_script(generated_test)

            definitions = split_script(test_extension).definitions

            new_script = "\n\n".join(
                [
                    decomposed_script.imports,
                    decomposed_script.definitions,
                    "\n".join(definitions.splitlines()[3:]),
                    decomposed_script.main,
                ]
            )

            generated_code_sections.append(new_script)
        return fuse_scripts(generated_code_sections)

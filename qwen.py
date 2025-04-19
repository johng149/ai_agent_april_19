from transformers import AutoModelForCausalLM, AutoTokenizer
import re
import random
import json


class ToolAgent:
    def __init__(self, tools=None, model_name_or_path="Qwen/Qwen2.5-3B-Instruct-GPTQ-Int4", system="You are a helpful assistant. Use the tools at your disposal, if any, to help the user", stop_words=[]):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype="auto",
            device_map="auto",
        )
        self.tools = tools if tools else []
        self.messages = []
        self.system = system
        self.stop_ids = self.tokenizer.convert_tokens_to_ids(stop_words) + [self.tokenizer.eos_token_id]

    def reset(self):
        self.messages = []

    def try_parse_tool_calls(self, content: str):
        """Try parse the tool calls."""
        tool_calls = []
        offset = 0
        for i, m in enumerate(re.finditer(r"<tool_call>\n(.+)?\n</tool_call>", content)):
            if i == 0:
                offset = m.start()
            try:
                func = json.loads(m.group(1))
                tool_calls.append({"type": "function", "function": func})
                if isinstance(func["arguments"], str):
                    func["arguments"] = json.loads(func["arguments"])
            except json.JSONDecodeError as e:
                print(f"Failed to parse tool calls: the content is {m.group(1)} and {e}")
                pass
        if tool_calls:
            if offset > 0 and content[:offset].strip():
                c = content[:offset]
            else: 
                c = ""
            return {"role": "assistant", "content": c, "tool_calls": tool_calls}
        return {"role": "assistant", "content": re.sub(r"<\|im_end\|>$", "", content)}

    def call_tool(self, tool_call):
        function_name = tool_call['function']['name']
        arguments = tool_call['function']['arguments']
        
        # Find the function in the tools list
        for tool in self.tools:
            if tool.__name__ == function_name:
                result = tool(**arguments)
                return {
                    "role": "tool",
                    "name": function_name,
                    "content": result,
                }
        return None

    def generate(self):
        text = self.tokenizer.apply_chat_template(self.messages, tools=self.tools, add_generation_prompt=True, tokenize=False)
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=512, eos_token_id=self.stop_ids)
        output_text = self.tokenizer.batch_decode(outputs)[0][len(text):]
        return output_text

    def start_new_session(self):
        self.messages = [
            {"role": "system", "content": self.system},
        ]

    def run(self, user_message=None, recurse=0, preserve_history=False):
        """
        Run the model with optional user message and history preservation.
        
        Args:
            user_message: Optional message from user. If None, no new user message is added.
            recurse: Number of tool call recursions (-1 for unlimited)
            preserve_history: If True, keeps conversation history from previous runs
        """
        # Initialize or reset messages if not preserving history
        if not preserve_history or not self.messages:
            self.messages = [
                {"role": "system", "content": self.system},
            ]
        
        # Only add user message if provided
        if user_message is not None:
            self.messages.append({"role": "user", "content": user_message})
        
        # Don't generate if no messages (this should rarely happen)
        if not self.messages:
            return {"role": "assistant", "content": "No input provided and no conversation history to continue."}
            
        output_text = self.generate()
        print(f"Output text: {output_text}")
        parsed = self.try_parse_tool_calls(output_text)
        print(f"Parsed output: {parsed}")
        
        # Add the assistant response to history immediately
        self.messages.append(parsed)

        while 'tool_calls' in parsed and (recurse > 0 or recurse == -1):
            results = []
            for tool_call in parsed['tool_calls']:
                result = self.call_tool(tool_call)
                if result:
                    print(f"Tool call result: {result}")
                    results.append(result)

            self.messages.extend(results)
            output_text = self.generate()
            print(f"Output text: {output_text}")
            parsed = self.try_parse_tool_calls(output_text)
            print(f"Parsed output: {parsed}")
            
            # Add each intermediate assistant response to history
            self.messages.append(parsed)

            if recurse > 0:
                recurse -= 1

        # The final parsed message is already added to history
        return parsed

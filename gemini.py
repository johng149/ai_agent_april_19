from google import genai
from google.genai import types

class GeminiAgent:
    def __init__(self, tools, schemas, api_key):
        """
        Initialize the Gemini agent with tools, schemas, and API key.
        
        Args:
            tools: List of tool functions
            schemas: List of tool schemas
            api_key: Gemini API key
        """
        self.tools = tools
        self.schemas = schemas
        self.api_key = api_key
        
        # Check if theory_status function exists in tools
        has_theory_status = any(tool.__name__ == "theory_status" for tool in tools)
        if not has_theory_status:
            raise ValueError("Required tool 'theory_status' is not defined in tools list")
            
        self.client = genai.Client(api_key=self.api_key)
        self.tool_config = types.Tool(function_declarations=self.schemas)
        self.config = types.GenerateContentConfig(tools=[self.tool_config])
        self.contents = []
        self.halt = False
        
    def handle_function_call_helper(self, name, args):
        """Handle the function call by finding and executing the appropriate tool."""
        if name == "theory_status":
            self.halt = True
        for tool in self.tools:
            if tool.__name__ == name:
                return tool(**args)
        return "Function not found"

    def handle_function_call(self, function_call):
        """Process function call and return result as a response part."""
        function_name = function_call.name
        arguments = function_call.args

        result = self.handle_function_call_helper(function_name, arguments)
        return types.Part.from_function_response(
            name=function_name,
            response={"result": result},
        )
    
    def reset(self):
        """Reset the conversation history."""
        self.contents = []
        
    def run(self, prompt, recursion=1):
        """
        Run the agent with specified recursion depth.
        
        Args:
            prompt: Initial prompt to start the conversation
            recursion: Number of tool call cycles to allow (default: 1)
            
        Returns:
            Final response from the model
        """
        # Add user prompt to existing conversation
        if prompt:
            self.contents.append(
                types.Content(role="user", parts=[types.Part(text=prompt)])
            )
            
        response = None
        iterations = 0
        
        while iterations < recursion:
            if self.halt:
                break
            # Generate content
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                config=self.config,
                contents=self.contents
            )
            
            # Check if response contains a function call
            if (response.candidates and 
                response.candidates[0].content.parts and 
                hasattr(response.candidates[0].content.parts[0], 'function_call') and
                response.candidates[0].content.parts[0].function_call):
                
                fn = response.candidates[0].content.parts[0].function_call
                
                # Add model's function call to conversation
                self.contents.append(types.Content(
                    role="model", 
                    parts=[types.Part(function_call=fn)]
                ))
                
                # Process function and add result to conversation
                function_response = self.handle_function_call(fn)
                self.contents.append(types.Content(
                    role="user", 
                    parts=[function_response]
                ))
                
                iterations += 1
            else:
                # No function call, exit the loop
                self.contents.append(
                    types.Content(
                        role="model",
                        parts=[
                            types.Part(text=response.text)
                        ]
                    )
                )
                iterations += 1
                
        return response

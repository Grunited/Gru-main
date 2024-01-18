from openai import OpenAI
import time
import asyncio
import json

STATUS_FAILURE = 2
STATUS_COMPLETED = 1
STATUS_CONTINUE = 0

class Expert:
    # This is an ABSTRACT class -- the `dispatcher` and `validator` methods need to be overridden
    def __init__(self, tools, prompt, name="Assistant", model="gpt-4-1106-preview", assistant_id=None):
        # TODO: Add MARK_COMPLETED() and MARK_FAILURE() as tools
        self.tools = tools
        self.prompt = prompt
        self.model = model
        self.client = OpenAI()
        if assistant_id is None:
            assistant = self.client.beta.assistants.create(
                name=name,
                tools=tools,
                instructions=prompt,
                model=model
            )
            assistant_id = assistant.id
        self.assistant_id = assistant_id
        self.thread_id = self.client.beta.threads.create().id  
    
    def send_message(self, message):
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=message
        )
        
        return message
    
    async def wait_for_assistant_response(self, run, poll_rate=1):
        run = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread_id,
            run_id=run.id
        )
        
        while run.status == 'queued' or run.status == 'in_progress':
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
            )
                        
            await asyncio.sleep(poll_rate)
        
        return run
    
    async def query(self, query):
        print("new query")
        self.send_message(query)
        
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        
        completed = False

        while not completed:
            
            run = await self.wait_for_assistant_response(run)
                        
            # RUN LOOP
            
            while run.status in ("completed", "failed", "expired", "cancelled") or (run.status == "requires_action" and not self.validator(run.required_action.submit_tool_outputs.tool_calls)):
                self.send_message("I can't read this output! Remember to respond with a valid tool call.")

                run = self.client.beta.threads.runs.create(
                    thread_id=self.thread_id,
                    assistant_id=self.assistant_id
                )
                
                run = await self.wait_for_assistant_response(run)
            
            calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs, status = self.dispatcher(calls)
            
            print('got tool outputs')
            
            if status == STATUS_FAILURE:
                self.debug(query)
            elif status == STATUS_COMPLETED:
                completed = True
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread_id,
                    run_id=run.id,
                    tool_outputs = tool_outputs
                )
            else:
                print('submitting tool outputs')
                self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread_id,
                run_id=run.id,
                tool_outputs = tool_outputs
            )
                
            await asyncio.sleep(0.5)
            
            print('done sleeping')
                
        return
            
    def dispatcher(self, calls):
        pass
    
    def validator(self, calls):
        """For now, just check if all calls are valid json. Longer term should validate schema, using JSON of tools."""
        for call in calls:
            try:
                json.loads(call.function.arguments)
            except:
                return False
        
        return True
        
    def debug(self, query):
        pass
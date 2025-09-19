Instead of treating agents as magical black boxes, the 12-Factor Agent methodology advocates for treating them as well-engineered software systems. The key is to leverage LLMs for their strengths in natural language understanding and generation while maintaining control and predictability through solid software engineering practices. The goal is to move away from "prompt-in, agent-out" thinking to a more structured approach.

# Factor 1: Natural Language to Tool Calls

An agentic coding agent should understand **Factor 1: Natural Language to Tool Calls** as a principle that dictates that the agent's primary function is to translate a user's natural language request into a specific, executable action. Think of it as a function that takes a string of human language as input and returns a structured object representing a tool to be used and the arguments to be passed to it.

This approach ensures that the agent's behavior is predictable, debuggable, and testable. By restricting the agent's creative freedom to the interpretation of language into a predefined set of tools, we can avoid the "long tail of unpredictable edge cases" that often plague more open-ended AI systems.

---

### **Model Examples**

* **Simple Request**:  
  * **User Input**: "What's the weather like in New York?"  
  * **Agent Output**: { "tool": "weather.get\_current\_weather", "args": { "location": "New York, NY" } }  
* **Multi-Step Request**:  
  * **User Input**: "Send a message to John saying I'm running 5 minutes late."  
  * **Agent Output**:  
    1. { "tool": "contacts.find\_contact", "args": { "name": "John" } }  
    2. { "tool": "messaging.send\_message", "args": { "recipient": "contact\_id\_123", "body": "I'm running 5 minutes late." } }  
* **Request with Ambiguity**:  
  * **User Input**: "Book a table for 2 at that new Italian place."  
  * **Agent Output**: { "tool": "search.find\_restaurant", "args": { "cuisine": "Italian", "sort\_by": "newest" } }

---

### **Anti-Patterns**

* **Open-Ended Generation**:  
  * **User Input**: "I'm cold."  
  * **Agent Output**: "Here is a poem about winter: ..." (Instead of calling a tool to adjust the thermostat or get the weather)  
* **Assuming Instead of Clarifying**:  
  * **User Input**: "Order me a pizza."  
  * **Agent Output**: { "tool": "food.order", "args": { "item": "pepperoni pizza", "address": "123 Main St" } } (Without confirming the user's preferred toppings or delivery address)  
* **Mixing Tool Use and Conversation**:  
  * **User Input**: "I need to book a flight to London."  
  * **Agent Output**: "I can help with that. When would you like to travel?" (Instead of immediately calling a flight search tool and then asking for more information if needed)

# Factor 2 \- Own Your Prompts

For an agentic coding agent, the core principle of **"Own Your Prompts"** is to treat prompts as a primary and explicit part of your codebase, not as a hidden or abstracted detail. You, the developer, should directly control and manage the prompts sent to the language model.

Think of prompts as the source code for your agent's behavior. Just as you wouldn't let a black-box tool write your application's business logic, you shouldn't let a framework completely control the instructions given to the LLM.

By owning your prompts, you gain:

* **Deterministic Control**: You can precisely define how your agent should behave, leading to more predictable and reliable outcomes.  
* **Enhanced Debugging and Testing**: When a prompt is explicit code, you can version control it, write unit tests for it, and easily iterate on it to improve performance.  
* **Transparency**: You have a clear understanding of what instructions the agent is working with at any given time.  
* **Performance Optimization**: Owning your prompts allows you to apply advanced prompt engineering techniques to optimize for token efficiency, latency, and accuracy.

---

### **Model Examples**

Here are some best practices for owning your prompts:

* **Version Control Prompts**: Store your prompts in a version control system like Git. This allows you to track changes, collaborate with others, and roll back to previous versions if needed.  
* Python

\# prompts/summarizer.py

SUMMARIZE\_ARTICLE\_PROMPT \= """  
Summarize the following article in three sentences.  
Focus on the main arguments and conclusions.

Article: {article\_text}  
"""

*   
*   
* **Use Prompt Templates**: Employ templating engines (like f-strings in Python, or more advanced ones like Jinja2) to dynamically insert data into your prompts. This separates the prompt structure from the data.  
* Python

\# main.py  
from prompts.summarizer import SUMMARIZE\_ARTICLE\_PROMPT

def summarize(article):  
    prompt \= SUMMARIZE\_ARTICLE\_PROMPT.format(article\_text=article)  
    \# ... send prompt to LLM ...

*   
*   
* **A/B Test Prompts**: Just as you would A/B test a user interface, you can test different versions of a prompt to see which one performs better on a given task.  
* **CI/CD for Prompts**: Implement a continuous integration and deployment pipeline for your prompts. This could involve automated testing of prompt changes against a "golden dataset" to ensure that performance doesn't regress.

---

### **Anti-Patterns**

Here are some common mistakes to avoid:

* **Relying on "Magic" Frameworks**: Using high-level frameworks that abstract away the prompt completely. If you can't see and edit the final prompt being sent to the LLM, you don't truly own it.  
* **Hardcoding Prompts in Business Logic**: Scattering prompt strings throughout your application code. This makes them difficult to find, update, and test.  
* Python

\# Bad example: Hardcoded prompt  
def process\_order(order\_details):  
    prompt \= f"Is this order for a VIP customer? Order details: {order\_details}"  
    \# ... more code ...

*   
*   
* **Using a Single, Monolithic Prompt for Complex Tasks**: Trying to cram too much logic and too many instructions into a single prompt. This can confuse the LLM and lead to unreliable results. It's often better to break down a complex task into a chain of smaller, more focused prompts.  
* **Not Monitoring Prompt Performance**: Failing to track key metrics like token usage, latency, and the quality of the LLM's output for each of your prompts. Without this data, it's difficult to know when and how to improve your prompts.

# Factor 3: Own your context window

For an agentic coding agent, the third factor of the 12-Factor Agents methodology, "Own Your Context Window," can be summarized as follows:

You must have **explicit control** over the information that is passed into the model's context window at each step of an operation. Do not blindly dump entire conversation histories, databases, or large documents into the prompt. Instead, you should strategically engineer the context to be as concise and relevant as possible for the immediate task.

This "context engineering" is critical for a few reasons:

* **Efficiency**: It reduces token consumption, which can lead to significant cost savings (30-60% is cited).  
* **Accuracy**: A smaller, more focused context window reduces the chance of the model being distracted by irrelevant information, leading to better and more accurate responses.  
* **Performance**: Smaller context windows lead to faster response times from the model.

Think of the context window as a limited cache. Your job is to manage that cache effectively. This means summarizing long histories, using structured data formats, and only including information that is directly relevant to the current step of the agent's task.

---

### **Model Examples**

Here are some specific examples of how to apply this principle:

* **Summarization**: Instead of feeding the entire chat history back to the model, maintain a running summary of the conversation and provide that summary along with the most recent user query. For long documents, use an embedding-based retriever to find the most relevant chunks of text to include in the context.  
* **Structured Data**: When dealing with structured data, don't just dump the whole JSON or CSV into the prompt. Instead, extract only the relevant fields and present them in a clean, easy-to-parse format.  
* **Stateful Tools**: For tools that maintain state, don't include the entire state in the context. Instead, provide a summary of the current state and any recent changes.

---

### **Anti-Patterns**

Here are some common anti-patterns to avoid:

* **The "Everything and the Kitchen Sink" Approach**: This is where you just dump everything you have into the context window and hope the model figures it out. This is inefficient, expensive, and often leads to poor results.  
* **Relying on Framework Defaults**: Don't blindly trust the default context management of a framework. Understand how it works and customize it to your specific needs.  
* **Ignoring Token Limits**: Failing to track and manage your token usage can lead to unexpected errors when you exceed the model's context window limit.  
* **Context Stuffing with Irrelevant Information**: Adding information to the context that is not directly relevant to the current task can confuse the model and lead to incorrect or nonsensical outputs.

# Factor 4: Tools Are Structured Outputs

For an agentic coding agent, **tools are not actions you directly execute**. Instead, a "tool" is a **structured JSON output** that you, the agent, generate. This JSON acts as a command, signaling to the deterministic, outside code what action to take.

This creates a clean and reliable separation between your "thinking" (the Large Language Model's decision-making process) and the "doing" (the execution of the code). Your core responsibility is to analyze the user's request and the current context, and then to output a JSON object that represents the next logical step. The environment will then parse this JSON and execute the corresponding, pre-written code.

The workflow is as follows:

1. **You (the LLM) decide the next step**: Based on the context, you determine which tool to use and with what parameters.  
2. **You output a structured JSON**: This JSON object represents the tool call.  
3. **Deterministic code executes the tool call**: The agent's backend parses the JSON and runs the corresponding function.  
4. **The result is added to the context**: The output of the tool is fed back to you to inform your next decision.  
5. **Repeat**: This loop continues until the task is complete.

---

### **Model Examples**

Here are some examples of how to correctly implement this principle:

#### **Example 1: Creating a file**

A user asks you to "create a new file called app.py with the content print('hello world')".

* **Your output (structured JSON):**

JSON

{  
  "tool": "create\_file",  
  "parameters": {  
    "filename": "app.py",  
    "content": "print('hello world')"  
  }  
}

* **Deterministic Code (Python example):**

Python

def create\_file(filename, content):  
  with open(filename, "w") as f:  
    f.write(content)  
  return f"Successfully created {filename}"

#### **Example 2: Searching for files**

A user asks, "find all the python files in the current directory".

* **Your output (structured JSON):**

JSON

{  
  "tool": "find\_files",  
  "parameters": {  
    "pattern": "\*.py"  
  }  
}

* **Deterministic Code (Python example):**

Python

import glob

def find\_files(pattern):  
  return glob.glob(pattern)

---

### **Anti-Patterns**

Here are some common mistakes to avoid:

#### **Anti-Pattern 1: Generating and executing code directly**

A user asks you to list the files in the current directory.

* **Your incorrect output (generating code to be executed):**

JSON

{  
  "action": "execute\_code",  
  "code": "import os; print(os.listdir('.'))"  
}

This is an anti-pattern because it's less reliable, harder to test, and poses a security risk. The agent should not be generating and executing arbitrary code.

#### **Anti-Pattern 2: Using unstructured output**

A user asks you to create a new file.

* **Your incorrect output (unstructured natural language):**

"OK, I will create a file named app.py with the content print('hello world')"

This is an anti-pattern because it requires the environment to parse natural language, which is inherently unreliable. The output should always be structured and machine-readable.

By adhering to the principle of "Tools are Structured Outputs", you can build more reliable, secure, and testable agentic systems.

# Factor 5: Unify Execution State and Business State

The core principle of **Factor 5: Unify Execution State and Business State** is to maintain a single, comprehensive, and chronologically ordered log of all events and states for an agent's operation. This unified log should not differentiate between the agent's internal "execution state" (e.g., current step, waiting for a tool response) and the "business state" (e.g., what has been accomplished for the user).

Think of it as a single, immutable thread of messages or events that represents the entire history of a task. This thread contains everything from the initial user request to every tool call, tool response, intermediate reasoning step, and final output.

For a coding agent, this means your state should be managed as a pure function: state\_n+1 \= f(state\_n, event). The current state is simply a fold or reduction of all previous events.

The key benefits of this approach are:

* **Simplicity and a Single Source of Truth:** No need to synchronize or reconcile different state machines.  
* **Enhanced Debugging and Observability:** The entire history of an agent's execution is in one place, making it easy to trace and debug issues.  
* **Trivial Serialization/Deserialization:** The state can be easily saved and loaded, which is crucial for long-running, asynchronous tasks.  
* **Easy Recovery and Forking:** An agent can be paused and resumed from any point in its execution by simply replaying the event log. It also allows for easy forking of the execution to explore different paths.

---

### **Model Example**

A good model for unified state is a **chat-based interface or a message queue**. Consider an agent designed to book a flight. The state would be a single, ordered list of messages:

JSON

\[  
  {  
    "role": "user",  
    "content": "Book a flight from New York to London for next Tuesday."  
  },  
  {  
    "role": "assistant",  
    "content": "I will search for flights from NYC to LHR for next Tuesday."  
  },  
  {  
    "role": "tool\_call",  
    "tool\_name": "flight\_search",  
    "arguments": {  
      "departure\_city": "NYC",  
      "arrival\_city": "LHR",  
      "date": "2025-10-28"  
    }  
  },  
  {  
    "role": "tool\_response",  
    "tool\_name": "flight\_search",  
    "content": {  
      "flight\_number": "BA112",  
      "departure\_time": "20:00",  
      "arrival\_time": "08:00+1",  
      "price": "650.00"  
    }  
  },  
  {  
    "role": "assistant",  
    "content": "I found a flight on British Airways for $650. Would you like to book it?"  
  },  
  {  
    "role": "user",  
    "content": "Yes, please."  
  },  
  {  
    "role": "tool\_call",  
    "tool\_name": "book\_flight",  
    "arguments": {  
      "flight\_number": "BA112"  
    }  
  },  
  {  
    "role": "tool\_response",  
    "tool\_name": "book\_flight",  
    "content": {  
      "success": true,  
      "confirmation\_number": "XYZ789"  
    }  
  },  
  {  
    "role": "assistant",  
    "content": "Your flight is booked. Your confirmation number is XYZ789."  
  }  
\]

In this example, both the "business state" (the user's request and the final booking) and the "execution state" (the tool calls and responses) are part of the same, unified log. To resume this task after a crash, you would simply load this list of messages.

---

### **Anti-Patterns**

An anti-pattern would be to separate the execution and business states into different systems or data structures. This creates complexity and makes the agent harder to manage.

For example, imagine the same flight booking agent, but with a state management system that looks like this:

* **A database table for "Bookings"**:  
  * booking\_id (Primary Key)  
  * user\_id  
  * departure\_city  
  * arrival\_city  
  * status (e.g., "pending", "confirmed", "failed")  
* **A separate, in-memory object for the "Execution State"**:  
* Python

class AgentState:  
    def \_\_init\_\_(self, user\_id):  
        self.user\_id \= user\_id  
        self.current\_step \= "search\_flights"  
        self.last\_tool\_response \= None  
        self.is\_waiting\_for\_user \= False

*   
* 

In this anti-pattern:

* **There are two sources of truth:** The database and the in-memory agent state. These can easily become out of sync.  
* **Debugging is difficult:** To understand what happened, you would need to cross-reference the database record with the agent's logs, which might be stored elsewhere.  
* **Recovery is complex:** If the agent crashes, you have to try and reconstruct the in-memory AgentState from the database and logs, which may not be possible to do with perfect fidelity.  
* **Asynchronous operations are a challenge:** If a tool takes a long time to execute, saving and restoring the agent's state becomes a custom, error-prone process.

# Factor 6\. Launch/Pause/Resume

The **Launch/Pause/Resume** factor is a design principle for building robust and long-running AI agents. It mandates that an agent's lifecycle be controllable through simple, explicit API calls. This is crucial for tasks that are not instantaneous and require waiting for external events, such as human feedback, long-running computations, or API callbacks.

Instead of a single, monolithic execution block, the agent's work should be broken down into discrete, resumable steps. This allows the agent to be paused and its state to be persisted. When the external event it's waiting for occurs, the agent can be resumed from where it left off, with its full context and history intact.

This architectural pattern is vital for:

* **Asynchronous Operations**: Handling tasks that involve waiting for external systems without blocking the entire application.  
* **Human-in-the-Loop Workflows**: Pausing execution to wait for user input, approval, or clarification.  
* **Resource Management**: Freeing up compute resources while an agent is in a waiting state.  
* **Fault Tolerance**: Recovering an agent's state after a crash or system restart.

---

### **Model Examples**

Here are some examples of how to correctly implement the Launch/Pause/Resume pattern:

#### **Example 1: A Simple API for a Research Agent**

Imagine a research agent that needs to find information and then get it approved by a human.

* **Launch**: An initial API call starts the agent with a research topic.  
* JSON

POST /agents/research/launch  
{  
  "topic": "The history of the Jacquard Loom"  
}

*   
* The agent runs until it has a draft, then it pauses.  
* **Pause**: When the agent needs human input, it saves its state and returns a "paused" status with a request for feedback.  
* JSON

{  
  "agent\_id": "research-123",  
  "status": "paused",  
  "action\_required": "human\_feedback",  
  "data": {  
    "draft\_summary": "The Jacquard Loom was a pivotal invention in the history of computing...",  
    "feedback\_url": "/feedback/research-123"  
  }  
}

*   
*   
* **Resume**: After the human provides feedback, a separate API call resumes the agent's execution.  
* JSON

POST /agents/research/resume  
{  
  "agent\_id": "research-123",  
  "input": {  
    "feedback": "This is a good start, but can you add more about its influence on Charles Babbage?"  
  }  
}

*   
* The agent then continues its work with the new information.

#### **Example 2: A Code-Generating Agent with a Long-Running Test Suite**

* **Launch**: The agent is tasked with writing a new feature and running tests.  
* **Pause**: After generating the code, the agent triggers a long-running test suite in a separate system. It then pauses itself, perhaps with a webhook URL for the test system to call upon completion.  
* **Resume**: When the test suite finishes, it calls the webhook, which in turn triggers the "resume" API for the agent. The agent then analyzes the test results and continues its task.

---

### **Anti-Patterns**

Here are some common anti-patterns to avoid:

#### **Anti-Pattern 1: The Monolithic run() Function**

A single, long-running run() function that contains the entire logic of the agent is a major anti-pattern.

* **Problem**: This approach makes it impossible to pause and resume the agent without complex and fragile state management. If the process crashes, all progress is lost. It also holds onto resources for the entire duration of the task, even when it's just waiting.  
* **Example of what to avoid**:  
* Python

def run\_agent(topic):  
    \# ... agent does a lot of work ...  
    draft \= research(topic)  
    \# ... now it waits for input, blocking everything ...  
    feedback \= get\_user\_feedback(draft) \# This could take days\!  
    \# ... finally continues ...  
    final\_report \= incorporate\_feedback(draft, feedback)  
    return final\_report

*   
* 

#### **Anti-Pattern 2: Storing State in Memory**

Relying on in-memory variables to store the agent's state is another common mistake.

* **Problem**: If the process restarts, all state is lost. This makes the agent fragile and not suitable for production environments.  
* **Example of what to avoid**:  
* Python

class ResearchAgent:  
    def \_\_init\_\_(self, topic):  
        self.topic \= topic  
        self.draft \= None \# Stored in memory\!  
        self.feedback \= None \# Also in memory\!

    def run(self):  
        \# ...

*   
* 

#### **Anti-Pattern 3: Complex, Ad-Hoc Resumption Logic**

If resuming an agent requires a complex series of steps and manual data loading, it's a sign of a poor architecture.

* **Problem**: This makes the system hard to maintain and reason about. The logic for resuming the agent should be as simple as the logic for launching it.  
* **Example of what to avoid**: Having to manually reconstruct the agent's state from multiple database tables and log files before you can resume its execution.

# Factor 7: Contact Humans with Tools

The core idea of this principle is to **treat all interactions with humans as tool calls**, just like any other action an agent can take. Instead of having the Large Language Model (LLM) choose between generating a natural language response for a human or a structured tool call for the system, the agent should *always* output a structured tool call. This creates a more robust and predictable system.

When an agent needs to communicate with a human, it should use a specific tool call, like request\_human\_input or done\_for\_now. This approach has several advantages:

* **Clear Instructions**: It enables you to define different tool calls for various types of human interactions, such as asking a clarifying question, requesting approval, or simply notifying the user of a completed task.  
* **Agent-Initiated Workflows**: It allows for workflows that are initiated by the agent rather than always starting with a human prompt.  
* **Multi-Agent and Multi-Human Coordination**: By standardizing communication through tool calls, it becomes easier to coordinate complex interactions between multiple agents and multiple humans.

---

### **Model Examples**

Here are some specific examples of how to implement this principle:

**Example 1: Requesting Clarification**

Imagine an agent is tasked with sending an email, but the recipient is ambiguous. Instead of just returning a text string like "Who should I send this to?", the agent should make a tool call.

JSON

{  
  "tool\_name": "request\_human\_input",  
  "parameters": {  
    "prompt": "The contact 'Jeff' is ambiguous. Please select the correct recipient:",  
    "options": \[  
      "jeff.smith@example.com",  
      "jeff.jones@example.com"  
    \]  
  }  
}

**Example 2: Seeking Approval for a Destructive Action**

If an agent is about to perform a destructive or irreversible action, like deleting a file or making a payment, it's crucial to get human approval.

JSON

{  
  "tool\_name": "request\_approval",  
  "parameters": {  
    "action\_description": "You are about to delete the file 'project\_alpha\_final.docx'.",  
    "confirmation\_prompt": "Are you sure you want to proceed?"  
  }  
}

---

### **Anti-Patterns**

Here are some common mistakes to avoid when implementing human-in-the-loop systems:

**Anti-Pattern 1: Mixed Output Types**

The most significant anti-pattern is allowing the LLM to decide whether to return a natural language response or a structured tool call. This creates a bifurcation in the agent's logic, making the control flow more complex and error-prone. The agent should **always** return a structured output.

**Incorrect:**

Python

\# The LLM has to decide between two different return types, which is bad.  
next\_step \= llm.decide\_next\_step(prompt)  
if isinstance(next\_step, str):  
  \# It's a natural language response for the user  
  print(next\_step)  
else:  
  \# It's a tool call  
  execute\_tool(next\_step)

**Anti-Pattern 2: A Single, Vague "Ask Human" Tool**

Another common mistake is to have a single, generic ask\_human tool that is used for all types of human interaction. This is better than having no tool at all, but it still lacks the specificity needed for robust and complex workflows. It's better to have more specialized tools for different kinds of human interaction.

**Incorrect:**

JSON

{  
  "tool\_name": "ask\_human",  
  "parameters": {  
    "question": "What should I do next?"  
  }  
}

This is not as good as having specific tools like request\_clarification, request\_approval, or notify\_user because it forces the human to figure out what the agent needs, rather than the agent explicitly stating its needs.

An agentic coding agent must maintain explicit control over its execution flow rather than delegating it to abstract frameworks. This principle, "Own Your Control Flow," is the eighth factor of the 12-Factor Agent framework. Here's a summary and specific examples of how to apply this principle.

### **Summary: Factor 8 \- Own Your Control Flow 📜**

For an agentic coding agent, owning your control flow means you should not use a generic, pre-built agentic loop. Instead, you should implement the logic that drives the agent's execution. This allows you to:

* **Customize**: Tailor the control flow to your specific use case. Not all tasks are the same; some require simple loops, while others need complex state machines.  
* **Interrupt**: Pause the agent's execution between when a tool is selected and when it is executed. This is critical for human-in-the-loop (HITL) workflows, such as requiring approval before running a command.  
* **Handle long-running tasks**: Break out of a loop to wait for asynchronous operations to complete without blocking the entire system.  
* **Debug**: Have full visibility into the agent's state and execution path, making it easier to identify and fix issues.

In short, treat the agent's control flow as a first-class part of your application's code.

---

### **Model Examples ✅**

Here are some examples of how a coding agent can "own its control flow":

* **State Machine**: Implement a finite state machine (FSM) where each state represents a specific step in the agent's process. The agent transitions between states based on the output of the LLM and the results of tool calls.  
* Python

class AgentState:  
    GATHERING\_REQUIREMENTS \= 1  
    WRITING\_CODE \= 2  
    TESTING\_CODE \= 3  
    WAITING\_FOR\_APPROVAL \= 4  
    DEPLOYING \= 5  
    DONE \= 6

\# The agent's main loop would be a state machine  
\# that transitions between these states.

*   
*   
* **Explicit Loop with Interrupts**: Use a simple while loop with explicit conditions to break out of the loop.  
* Python

while True:  
    next\_step \= llm.decide\_next\_step(context)

    if next\_step.tool \== "human\_approval":  
        \# Break the loop to wait for human input  
        break  
    elif next\_step.tool \== "execute\_code":  
        \# Get approval before executing  
        if get\_human\_approval(next\_step.code):  
            execute(next\_step.code)  
        else:  
            \# Handle disapproval  
            pass  
    elif next\_step.tool \== "done":  
        break

*   
*   
* **Workflow Engine**: For more complex agents, use a workflow engine (like Temporal, Prefect, or Dagster) to orchestrate the agent's execution as a series of well-defined steps.

---

### **Anti-Patterns ❌**

Here are some anti-patterns to avoid:

* **Black-Box Agent Loops**: Relying on a generic agent.run() method from a framework where you have no control over the internal loop.  
* Python

\# Anti-pattern: The internal loop of agent.run() is a black box  
agent.run("Build and deploy a web server.")

*   
*   
* **Monolithic Loop**: Using the same generic loop for every type of task, regardless of whether it's a simple Q\&A or a complex, multi-step process that requires human oversight.  
* **No Human-in-the-Loop**: Designing an agent that cannot be interrupted for human review, especially for high-stakes actions like deploying code or deleting data.  
* **Implicit Control Flow in Prompts**: Trying to control the agent's execution flow entirely through prompting. This is brittle and hard to maintain.

\# Anti-pattern: Relying on the prompt to control the execution flow  
"If you need to write code, first ask for approval.  
If you get approval, then write the code.  
After you write the code, ask for approval to run the tests..."

*   
* 

# Factor 9 \- Compact Errors into Context Window 📝

For an agentic coding agent, **Factor 9: Compact Errors into Context Window** means that when a tool or action fails, the error message should be treated as a valuable piece of information. Instead of a generic failure, the error should be a concise and descriptive summary of what went wrong. This "compact error" is then added back into the agent's context window. This allows the agent to understand the mistake and attempt to self-correct in its next step. Think of it as a feedback loop for the agent's reasoning process. The goal is to make errors a part of the conversation, enabling the agent to learn and adapt.

---

### **Model Examples ✅**

Here are some examples of how to correctly implement this principle:

* **Example 1: API Call Failure**  
  * **Tool:** execute\_api\_call(endpoint, data)  
  * **Error:** The API returns a 401 Unauthorized error.  
  * **Compact Error added to context:** Tool "execute\_api\_call" failed with status 401: Unauthorized. The API key may be invalid or expired.  
  * **Agent's next step:** The agent, seeing this error, could then use a tool to retrieve a new API key and retry the original call.  
* **Example 2: File Not Found**  
  * **Tool:** read\_file(path)  
  * **Error:** The file at the specified path does not exist.  
  * **Compact Error added to context:** Tool "read\_file" failed. File not found at path: /data/non\_existent\_file.csv  
  * **Agent's next step:** The agent could then use a list\_files tool to see the available files in the /data/ directory and correct the file path.  
* **Example 3: Invalid Tool Input**  
  * **Tool:** calculate\_shipping\_cost(weight\_kg, destination)  
  * **Error:** The weight\_kg is provided as a negative number.  
  * **Compact Error added to context:** Tool "calculate\_shipping\_cost" failed. Invalid input: weight\_kg cannot be negative.  
  * **Agent's next step:** The agent can then re-examine the input it provided and correct the weight to a positive number.

---

### **Anti-Patterns ❌**

Here are some examples of what *not* to do:

* **Anti-Pattern 1: Generic, Unhelpful Errors**  
  * **Error:** Tool call failed.  
  * **Why it's bad:** This gives the agent no information about *why* the tool failed. The agent is likely to either give up or retry the exact same failed step.  
* **Anti-Pattern 2: Overly Verbose Stack Traces**  
  * **Error:** A full, multi-page stack trace is dumped into the context window.  
  * **Why it's bad:** This pollutes the context window with irrelevant information. The agent has to sift through a large amount of text to find the actual cause of the error, which is inefficient and can lead to confusion.  
* **Anti-Pattern 3: Ignoring Errors and Moving On**  
  * **Error:** The tool fails silently, and the agent proceeds as if it succeeded.  
  * **Why it's bad:** This leads to a cascade of failures. The agent's subsequent steps are based on a false premise, leading to incorrect and unpredictable behavior.  
* **Anti-Pattern 4: Exposing Sensitive Information in Errors**  
  * **Error:** Tool "database\_connect" failed. Invalid password 'Admin123\!' for user 'root'.  
  * **Why it's bad:** Error messages should be informative but not expose secrets or sensitive data. This is a security risk.

An agentic coding agent should understand the "small, focused agents" principle as a core tenet of building robust and maintainable AI systems. Here's a summary of Factor 10 from the 12-Factor Agents methodology, along with model examples and anti-patterns.

# Factor 10 \- Small, Focused Agents

The core idea behind **small, focused agents** is to build agents that excel at a single, well-defined task. This is in stark contrast to creating a large, monolithic agent that attempts to handle a wide array of functions. Think of it as applying the microservices architecture principle to AI agent development.

For an agentic coding agent, this means your design philosophy should be:

* **Decomposition**: Break down complex workflows into smaller, logical units. Each unit becomes a candidate for a dedicated agent.  
* **Specialization**: Each agent should be an expert in its specific domain. This makes it easier to define its tools, prompts, and context.  
* **Composability**: Design agents to be building blocks. You can then orchestrate these smaller agents to accomplish more complex, multi-step tasks. The control flow and orchestration logic should reside in your code, not be left to a single, large language model to figure out.

The primary benefits of this approach are:

* **Improved Reliability**: Smaller agents are easier to test, debug, and validate. You can isolate failures and reason about their behavior more effectively.  
* **Enhanced Maintainability**: As your system evolves, it's simpler to update or replace a small, focused agent than to refactor a monolithic one.  
* **Scalability**: You can scale individual agents based on their specific workloads.

---

### **Model Examples**

Here are some specific examples of how to apply the "small, focused agents" principle:

* **Customer Support Automation**:  
  * **Agent A: Intent Classifier**: This agent's sole responsibility is to take the user's initial query and classify their intent (e.g., "billing issue," "technical question," "refund request").  
  * **Agent B: Document Searcher**: Once the intent is known, this agent searches the knowledge base or internal documentation for relevant information.  
  * **Agent C: Summarizer**: This agent takes the search results and synthesizes a concise answer for the user.  
  * **Agent D: Action Executor**: If the user's request requires an action (e.g., processing a refund), this agent would handle the API calls and state changes.  
* **Software Development Assistant**:  
  * **Agent A: Code Retriever**: Fetches relevant code snippets from a repository based on a natural language query.  
  * **Agent B: Linter/Code Checker**: Analyzes a piece of code for errors or style violations.  
  * **Agent C: Test Case Generator**: Writes unit tests for a given function or class.  
  * **Agent D: Deployment Agent**: Handles the process of deploying code to a staging or production environment.

---

### **Anti-Patterns**

The primary anti-pattern is the **monolithic agent**. This is an agent designed to do everything, and it often exhibits the following characteristics:

* **A "God" Prompt**: A single, massive prompt that tries to instruct the language model on how to handle every possible scenario. This is brittle and difficult to maintain.  
* **Over-reliance on the LLM for Control Flow**: Instead of using code to orchestrate the steps, the monolithic agent relies on the language model to decide what to do next in a long, open-ended loop. This leads to unpredictable behavior and makes it hard to enforce business rules.  
* **Large, Generic Toolsets**: A monolithic agent will have a large collection of tools, and it's up to the language model to figure out which one to use. This increases the chances of error and makes the agent's behavior less deterministic.  
* **Difficult to Debug**: When a monolithic agent fails, it's challenging to pinpoint the exact cause of the failure. The error could be in the prompt, the model's reasoning, or the interaction between tools.

Here is a summary of the "Stateless Reducer" principle for agentic coding, along with model examples and anti-patterns.

# Factor 12: Stateless Reducer

For an agentic coding agent, the **Stateless Reducer** principle dictates that an agent should be designed as a **pure function**. This means the agent's core logic takes the current state and a new event (or input) and returns a new, updated state. The agent itself does not maintain any internal, hidden state between invocations.

This approach is analogous to a reducer function in functional programming. The key characteristics are:

* **Predictability:** Given the same input state and event, the agent will always produce the same output state. This makes the agent's behavior deterministic and easy to reason about.  
* **Testability:** Each state transition can be tested independently, simplifying the creation of robust test suites.  
* **Debuggability:** When an error occurs, the entire history of states and events can be reviewed to understand the exact point of failure. There are no hidden variables or internal states to inspect.  
* **Scalability:** Stateless agents can be easily distributed and scaled horizontally, as there is no need to synchronize or replicate internal state across multiple instances.

---

### **Model Examples**

Here are some examples of how the Stateless Reducer principle can be applied in practice:

**1\. A Simple Counter Agent:**

This agent's job is to simply increment a counter.

* **State:** { "count": 5 }  
* **Event:** { "type": "INCREMENT" }  
* **Agent Logic (as a function):**  
* Python

def counter\_agent(state, event):  
  if event\["type"\] \== "INCREMENT":  
    return { "count": state\["count"\] \+ 1 }  
  else:  
    return state

*   
* 

**2\. A Financial Transaction Agent:**

This agent processes deposits and withdrawals.

* **Initial State:** { "balance": 100, "transactions": \[\] }  
* **Event:** { "type": "DEPOSIT", "amount": 50 }  
* **Agent Logic (as a function):**  
* Python

def transaction\_agent(state, event):  
  if event\["type"\] \== "DEPOSIT":  
    new\_balance \= state\["balance"\] \+ event\["amount"\]  
    new\_transactions \= state\["transactions"\] \+ \[event\]  
    return { "balance": new\_balance, "transactions": new\_transactions }  
  elif event\["type"\] \== "WITHDRAWAL":  
    \# ... logic for withdrawal  
  else:  
    return state

*   
* 

In both examples, the agent is a stateless function that transforms the given state based on the event and returns a completely new state.

---

### **Anti-Patterns**

Here are some common anti-patterns that violate the Stateless Reducer principle:

**1\. Agents with Internal State:**

An agent that maintains its own internal state, which is not passed in with each call.

* **Problem:** The agent's behavior is no longer predictable. The same input can produce different outputs depending on the agent's hidden internal state. This makes it difficult to debug and test.  
* **Example:**  
* Python

class StatefulAgent:  
  def \_\_init\_\_(self):  
    self.count \= 0

  def process(self, event):  
    if event\["type"\] \== "INCREMENT":  
      self.count \+= 1  
    return { "current\_count": self.count }

*   
* 

**2\. Agents that Modify State in Place:**

An agent that directly modifies the input state object instead of returning a new, immutable state.

* **Problem:** This can lead to unexpected side effects, especially in a concurrent environment. It breaks the functional paradigm of immutability and makes it harder to track changes to the state over time.  
* **Example:**  
* Python

def mutable\_agent(state, event):  
    if event\["type"\] \== "DEPOSIT":  
        state\["balance"\] \+= event\["amount"\] \# Modifying state directly  
        return state

*   
* 

**3\. Agents that rely on External State without Explicit Input:**

An agent that reads from a database, a file, or a global variable without that information being explicitly passed in as part of the current state.

* **Problem:** This makes the agent's behavior dependent on external factors that are not part of the explicit input, making it difficult to test in isolation.  
* **Example:**  
* Python

\# global\_variable is not passed in as part of the state  
global\_variable \= 10

def external\_state\_agent(state, event):  
  return { "result": state\["value"\] \+ global\_variable }

*   
* 


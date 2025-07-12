import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
load_dotenv()

async def main():
    model = init_chat_model("openai:gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))
    client = MultiServerMCPClient(
        {
            "google-rss-mcp": {
                "command": "python",
                "args": ["./src/server.py"],
                "transport": "stdio",
            },
        }
    )
    tools = await client.get_tools()
    print(tools)

    def call_model(state: MessagesState):
        response = model.bind_tools(tools).invoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    response = await graph.ainvoke({"messages": "what's the latest news about AI?"})
    
    # Print only the content of the last AI message
    messages = response["messages"]
    if messages and hasattr(messages[-1], 'content') and messages[-1].content:
        print("\n" + "="*50)
        print("AI News Search Result:")
        print("="*50)
        print(messages[-1].content)
        print("="*50)
    else:
        print("No response found.")

if __name__ == "__main__":
    asyncio.run(main())

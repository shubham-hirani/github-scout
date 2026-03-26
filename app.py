import streamlit as st
import asyncio
import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters
from google.genai.types import Content, Part

# --- 1. SETUP ---
st.set_page_config(page_title="GitHub Scout", layout="wide")

# Setup MCP Parameters
# Note: Use 'python' for Windows or 'python3' for Mac/Linux
mcp_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
    env={**os.environ}
)

# Initialize Agent and Tools
if "agent_system" not in st.session_state:
    mcp_toolset = McpToolset(connection_params=mcp_params)

    st.session_state.agent = Agent(
        name="GitHubScout",
        model="gemini-1.5-flash",
        instruction="You are a GitHub expert. Use 'get_repo_summary' for any repo queries.",
        tools=[mcp_toolset]
    )

    st.session_state.session_service = InMemorySessionService()
    st.session_state.runner = Runner(
        agent=st.session_state.agent,
        session_service=st.session_state.session_service,
        app_name="github_scout"
    )
    st.session_state.agent_system = True

# --- 2. UI ---
st.title("🔍 GitHub Scout")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. AGENT EXECUTION ---
if prompt := st.chat_input("Ask about a repo (e.g., google/adk)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Talking to MCP Server..."):
            async def run_agent():
                # 1. Ensure session is ready
                await st.session_state.session_service.create_session(
                    app_name="github_scout",
                    user_id="user_1",
                    session_id="session_1"
                )

                # 2. Wrap the prompt in the 1.27.5 'Content' structure
                user_content = Content(
                    role="user",
                    parts=[Part(text=prompt)]
                )

                # 3. Run and iterate through events
                # We use run_async to avoid the Threading issues you saw
                response_text = ""
                async for event in st.session_state.runner.run_async(
                        new_message=user_content,
                        user_id="user_1",
                        session_id="session_1"
                ):
                    if event.is_final_response():
                        response_text = event.content.parts[0].text
                return response_text


            try:
                # Standard way to run async in Streamlit
                final_answer = asyncio.run(run_agent())
                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            except Exception as e:
                st.error(f"System Error: {str(e)}")
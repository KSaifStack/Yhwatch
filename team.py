import os

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.team import Team
from agno.tools.file import FileTools
from agno.tools.websearch import WebSearchTools

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000/v1")
LITELLM_API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-local-dev")
NOTES_DIR = os.path.expanduser(os.getenv("NOTES_DIR", "~/notes"))


def llm(model: str) -> OpenAIChat:
    return OpenAIChat(id=model, base_url=LITELLM_BASE_URL, api_key=LITELLM_API_KEY)


agent_db = SqliteDb(session_table="sternritter_sessions", db_file="tmp/sternritter.db")

haschwalth = Agent(
    name="Haschwalth",
    id="haschwalth",
    model=llm("haschwalth"),
    role="System health and load balancing.",
    instructions=[
        "You are Haschwalth, the Balance. You report on the health of the Hermes server.",
        "Answer with facts: uptime, disk, RAM, running services, recent errors.",
        "If a metric is missing, say so. Never invent numbers.",
        "Keep responses short and structured.",
    ],
    markdown=True,
)

askin = Agent(
    name="Askin",
    id="askin",
    model=llm("askin"),
    role="Research and analysis.",
    instructions=[
        "You are Askin, the Deathdealing. You research companies, industries, and topics.",
        "Use the web search tool before answering factual questions.",
        "Return findings as a research brief with sources.",
    ],
    tools=[WebSearchTools()],
    markdown=True,
)

lille = Agent(
    name="Lille",
    id="lille",
    model=llm("lille"),
    role="Code and scripts.",
    instructions=[
        "You are Lille, the X-Axis. You write and fix code.",
        "Write files to code/ under the notes directory.",
        "Prefer small, dependency-free solutions. Explain nothing you were not asked to.",
    ],
    tools=[FileTools(base_dir=NOTES_DIR)],
    markdown=True,
)

gremmy = Agent(
    name="Gremmy",
    id="gremmy",
    model=llm("gremmy"),
    role="Notes, summaries, and cover letters.",
    instructions=[
        "You are Gremmy, the Visionary. You write notes and cover letters.",
        "Save written output to inbox/ under the notes directory.",
        "Address the recipient by name, reference the position, keep it to one page.",
    ],
    tools=[FileTools(base_dir=NOTES_DIR)],
    markdown=True,
)

yhwach = Team(
    name="Yhwach",
    id="yhwach",
    model=llm("yhwach"),
    description="The Almighty. Orchestrator of the Sternritter.",
    members=[haschwalth, askin, lille, gremmy],
    db=agent_db,
    instructions=[
        "You are Yhwach, the Almighty. You are the orchestrator of the Sternritter.",
        "Delegate every request to the right member: health to Haschwalth, research to Askin, code to Lille, writing to Gremmy.",
        "You never do agent work yourself. You assign and consolidate.",
        "Keep responses concise for Telegram.",
    ],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    teams=[yhwach],
    interfaces=[Telegram(team=yhwach, reply_to_mentions_only=False)],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="team:app", port=7777, reload=True)
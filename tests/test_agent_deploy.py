import os
from pathlib import Path

import pytest

from maam.config.io import save_model
from maam.config.models import DeploymentMode, ProjectConfig, UserConfig
from maam.core.service import MAAMService


@pytest.fixture
def mock_env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    # Setup local agent file
    agent_src = tmp_path / "my-agent.md"
    agent_src.write_text("# My Agent")

    # Setup local skill dir
    skill_src = tmp_path / "my-skill"
    skill_src.mkdir()
    (skill_src / "SKILL.md").write_text("# My Skill")

    return {
        "home": home,
        "project": project,
        "agent_src": agent_src,
        "skill_src": skill_src,
    }


def test_agent_copy_and_extension(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))

    user_config = UserConfig(default_deployment_mode=DeploymentMode.SYMLINK)
    # Only enable opencode to keep it simple
    user_config.tools = {"opencode": user_config.tools["opencode"]}

    service = MAAMService(user_config, mock_env["project"])

    # Discovering the agent file
    # We simulate this by putting it in the registry/agents folder
    registry_agents = mock_env["home"] / "registry" / "agents"
    registry_agents.mkdir(parents=True)
    import shutil

    shutil.copy(mock_env["agent_src"], registry_agents / "my-agent.md")

    # Discovering the skill dir
    registry_skills = mock_env["home"] / "registry" / "skills"
    registry_skills.mkdir(parents=True)
    shutil.copytree(mock_env["skill_src"], registry_skills / "my-skill")

    # Configure project
    project_config = ProjectConfig(local_assets=["agent:my-agent", "skill:my-skill"])
    save_model(mock_env["project"] / ".maam" / "project.yaml", project_config)

    # Sync
    deployments = service.sync()

    # Verify Agent
    agent_deployment = next(d for d in deployments if d.asset_kind == "agent")
    assert agent_deployment.mode == DeploymentMode.COPY
    agent_target = Path(agent_deployment.target)
    assert agent_target.name == "my-agent.md"
    assert agent_target.exists()
    assert not agent_target.is_symlink()

    # Verify Skill
    skill_deployment = next(d for d in deployments if d.asset_kind == "skill")
    assert skill_deployment.mode == DeploymentMode.SYMLINK
    skill_target = Path(skill_deployment.target)
    assert skill_target.name == "my-skill"
    assert skill_target.exists()
    assert skill_target.is_symlink()

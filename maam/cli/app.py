import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List
from pathlib import Path
from maam.config.paths import get_maam_home, get_project_dir, get_project_config_path, get_user_config_path, get_project_state_path
from maam.config.io import load_model, save_model
from maam.config.models import (
    UserConfig, ProjectConfig, AssetKind, RegistryConfig, 
    ToolConfig, ToolKindConfig, ProfileConfig, ProjectState
)
from maam.catalog.manager import CatalogManager
from maam.tools.manager import ToolManager
from maam.core.service import MAAMService
from maam.validate.health import HealthChecker

app = typer.Typer(
    name="maam",
    help="MAAM: My Agentic Assets Manager",
    add_completion=False,
)

asset_app = typer.Typer(name="asset", help="Manage assets.")
registry_app = typer.Typer(name="registry", help="Manage remote registries.")
tool_app = typer.Typer(name="tool", help="Manage tools and capabilities.")
profile_app = typer.Typer(name="profile", help="Manage reusable profiles.")
project_app = typer.Typer(name="project", help="Manage project configuration.")

app.add_typer(asset_app)
app.add_typer(registry_app)
app.add_typer(tool_app)
app.add_typer(profile_app)
app.add_typer(project_app)

console = Console()

def get_user_config() -> UserConfig:
    path = get_user_config_path()
    try:
        return load_model(UserConfig, path)
    except Exception:
        return UserConfig()

def version_callback(value: bool):
    if value:
        console.print("MAAM version: 0.1.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version and exit."
    ),
):
    """
    Project-local asset manager for agentic development environments.
    """
    pass

@app.command()
def wizard():
    """
    Launch the interactive setup wizard.
    """
    from maam.cli.wizard import run_wizard
    run_wizard()

@app.command()
def doctor():
    """
    Check the health of the MAAM environment and current project.
    """
    home = get_maam_home()
    user_config_path = get_user_config_path()
    project_dir = get_project_dir()
    project_config_path = get_project_config_path(project_dir)
    project_state_path = get_project_state_path(project_dir)
    
    console.print(Panel.fit("MAAM Doctor", style="bold green"))
    console.print(f"Version: 0.1.0")
    console.print(f"MAAM home: [blue]{home}[/blue]")
    
    user_config = get_user_config()
    checker = HealthChecker(user_config, project_dir)
    
    if user_config_path.exists():
        console.print(f"User config: [green]found[/green] ({user_config_path})")
    else:
        console.print(f"User config: [yellow]not found[/yellow] (using defaults)")
    
    console.print(f"  Registries: {len(user_config.registries)}")
    console.print(f"  Tools: {len(user_config.tools)}")

    profiles_dir = home / "profiles"
    profile_count = len(list(profiles_dir.glob("*.yaml"))) if profiles_dir.exists() else 0
    console.print(f"  Profiles: {profile_count}")

    issues = []
    if project_config_path.exists():
        try:
            project_config = load_model(ProjectConfig, project_config_path)
            console.print(f"Project config: [green]found[/green] ({project_config_path})")
            if project_config.profile:
                console.print(f"  Profile: [cyan]{project_config.profile}[/cyan]")
            console.print(f"  Local assets: {len(project_config.local_assets)}")
            
            issues.extend(checker.check_config_resolution(project_config))
        except Exception as e:
            console.print(f"Project config: [red]error[/red] ({project_config_path})")
            console.print(f"  [red]{e}[/red]")
    else:
        console.print(f"Project config: [yellow]not found[/yellow]")

    if project_state_path.exists():
        try:
            state = load_model(ProjectState, project_state_path)
            console.print(f"Project state: [green]found[/green] ({project_state_path})")
            console.print(f"  Deployments: {len(state.deployments)}")
            
            issues.extend(checker.check_deployments(state))
        except Exception as e:
            console.print(f"Project state: [red]error[/red] ({project_state_path})")
            console.print(f"  [red]{e}[/red]")

    if issues:
        console.print("\n[bold yellow]Health Issues:[/bold yellow]")
        for level, msg in issues:
            color = "red" if level == "error" else "yellow"
            console.print(f"  [{color}][{level.upper()}][/{color}] {msg}")
    else:
        console.print(f"\nStatus: [bold green]healthy[/bold green]")

@app.command()
def sync():
    """Synchronize project deployments with configuration."""
    project_dir = get_project_dir()
    project_config_path = get_project_config_path(project_dir)
    
    if not project_config_path.exists():
        console.print(f"[yellow]No project config found at {project_config_path}[/yellow]")
        console.print("Run 'maam project init' first.")
        raise typer.Exit(1)
        
    user_config = get_user_config()
    service = MAAMService(user_config, project_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Synchronizing assets...", total=None)
        deployments = service.sync()
        
    if not deployments:
        console.print("[yellow]No assets deployed. Check your project.yaml, profile, and tool capabilities.[/yellow]")
    else:
        console.print(f"[green]Successfully synchronized {len(deployments)} assets.[/green]")
        
        table = Table(title="Realized Deployments")
        table.add_column("Asset", style="green")
        table.add_column("Kind", style="cyan")
        table.add_column("Tool", style="magenta")
        table.add_column("Mode", style="blue")
        table.add_column("Target")

        for d in sorted(deployments, key=lambda x: (x.tool, x.asset_name)):
            rel_target = Path(d.target).relative_to(project_dir)
            table.add_row(
                d.asset_name,
                d.asset_kind,
                d.tool,
                d.mode.value,
                str(rel_target)
            )
        console.print(table)

@app.command()
def export(path: Path = typer.Argument(..., help="Path to save the export file.")):
    """Export profiles, tools, and registries."""
    user_config = get_user_config()
    service = MAAMService(user_config, get_project_dir())
    try:
        service.export_config(path)
        console.print(f"[green]Exported configuration to {path}[/green]")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        raise typer.Exit(1)

@app.command("import")
def import_config(path: Path = typer.Argument(..., help="Path to the export file.")):
    """Import profiles, tools, and registries."""
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(1)
        
    user_config = get_user_config()
    service = MAAMService(user_config, get_project_dir())
    try:
        service.import_config(path)
        console.print(f"[green]Imported configuration from {path}[/green]")
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")
        raise typer.Exit(1)

@asset_app.command("list")
def asset_list():
    """List all available assets."""
    config = get_user_config()
    manager = CatalogManager(config)
    all_assets = manager.list_assets()
    
    if not all_assets:
        console.print("No assets found.")
        return

    table = Table(title="Available Assets")
    table.add_column("Kind", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version")
    table.add_column("Source", style="blue")
    table.add_column("Description")

    keys = sorted(all_assets.keys(), key=lambda x: (x[0], x[1]))
    for key in keys:
        kind, name = key
        matches = all_assets[key]
        source_name, _, manifest = matches[0]
        dup_indicator = f" (+{len(matches)-1} more)" if len(matches) > 1 else ""
        
        table.add_row(
            kind,
            name,
            manifest.version,
            f"{source_name}{dup_indicator}",
            manifest.description
        )

    console.print(table)

@asset_app.command("add")
def asset_add(path: Path = typer.Argument(..., help="Path to the asset directory.")):
    """Add a local asset to the local registry."""
    if not path.exists():
        console.print(f"[red]Path does not exist: {path}[/red]")
        raise typer.Exit(1)
        
    config = get_user_config()
    manager = CatalogManager(config)
    try:
        manifest = manager.add_local_asset(path)
        console.print(f"[green]Successfully added {manifest.kind} '{manifest.name}' to local registry.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to add asset: {e}[/red]")
        raise typer.Exit(1)

@asset_app.command("remove")
def asset_remove(
    kind: AssetKind = typer.Argument(..., help="Kind of the asset."),
    name: str = typer.Argument(..., help="Name of the asset.")
):
    """Remove an asset from the local registry."""
    config = get_user_config()
    manager = CatalogManager(config)
    if manager.remove_local_asset(kind, name):
        console.print(f"[green]Successfully removed {kind} '{name}' from local registry.[/green]")
    else:
        console.print(f"[yellow]Asset {kind} '{name}' not found in local registry.[/yellow]")

@registry_app.command("add")
def registry_add(
    name: str = typer.Argument(..., help="Name of the registry."),
    url: str = typer.Argument(..., help="Git URL of the registry.")
):
    """Add a remote Git registry."""
    config = get_user_config()
    config.registries[name] = RegistryConfig(url=url)
    save_model(get_user_config_path(), config)
    console.print(f"[green]Added registry '{name}' with URL: {url}[/green]")

@registry_app.command("list")
def registry_list():
    """List configured remote registries."""
    config = get_user_config()
    if not config.registries:
        console.print("No remote registries configured.")
        return

    table = Table(title="Remote Registries")
    table.add_column("Name", style="green")
    table.add_column("URL", style="blue")
    
    for name, reg_config in config.registries.items():
        table.add_row(name, reg_config.url)
        
    console.print(table)

@registry_app.command("update")
def registry_update():
    """Update all remote registries."""
    config = get_user_config()
    manager = CatalogManager(config)
    console.print("Updating registries...")
    manager.update_registries()
    console.print("[green]Registries updated.[/green]")

@tool_app.command("list")
def tool_list():
    """List configured tools and their capabilities."""
    config = get_user_config()
    manager = ToolManager(config)
    tools = manager.list_tools(enabled_only=False)
    
    if not tools:
        console.print("No tools configured.")
        return

    table = Table(title="Configured Tools")
    table.add_column("Tool", style="green")
    table.add_column("Enabled", style="cyan")
    table.add_column("Capabilities (Kind: Path)")

    for name, tool_config in sorted(tools.items()):
        capabilities = ", ".join([
            f"{kind}: {cfg.local_path}" 
            for kind, cfg in tool_config.kinds.items()
        ])
        table.add_row(
            name,
            "[green]yes[/green]" if tool_config.enabled else "[red]no[/red]",
            capabilities or "None"
        )

    console.print(table)

@tool_app.command("add-capability")
def tool_add_capability(
    tool: str = typer.Argument(..., help="Name of the tool."),
    kind: AssetKind = typer.Argument(..., help="Asset kind."),
    path: str = typer.Argument(..., help="Project-local target path.")
):
    """Add or update a tool capability."""
    config = get_user_config()
    if tool not in config.tools:
        config.tools[tool] = ToolConfig()
    
    config.tools[tool].kinds[kind] = ToolKindConfig(local_path=path)
    save_model(get_user_config_path(), config)
    console.print(f"[green]Updated tool '{tool}' capability: {kind} -> {path}[/green]")

@profile_app.command("list")
def profile_list():
    """List all available profiles."""
    home = get_maam_home()
    profiles_dir = home / "profiles"
    if not profiles_dir.exists():
        console.print("No profiles found.")
        return
        
    profiles = list(profiles_dir.glob("*.yaml"))
    if not profiles:
        console.print("No profiles found.")
        return

    table = Table(title="Available Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Assets", style="green")
    table.add_column("Tools", style="magenta")
    table.add_column("Description")

    for p_path in sorted(profiles):
        try:
            profile = load_model(ProfileConfig, p_path)
            table.add_row(
                profile.name,
                ", ".join(profile.assets) if profile.assets else "None",
                ", ".join(profile.tools.keys()) if profile.tools else "None",
                profile.description or ""
            )
        except Exception:
            continue
            
    console.print(table)

@profile_app.command("new")
def profile_new(name: str = typer.Argument(..., help="Name of the profile.")):
    """Scaffold a new profile."""
    home = get_maam_home()
    profile_path = home / "profiles" / f"{name}.yaml"
    if profile_path.exists():
        console.print(f"[red]Profile '{name}' already exists at {profile_path}[/red]")
        raise typer.Exit(1)
        
    profile = ProfileConfig(name=name, description=f"Description for {name}")
    save_model(profile_path, profile)
    console.print(f"[green]Scaffolded new profile '{name}' at {profile_path}[/green]")

@project_app.command("init")
def project_init(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to bind the project to.")
):
    """Initialize a new MAAM project."""
    project_dir = get_project_dir()
    project_config_path = get_project_config_path(project_dir)
    
    if project_config_path.exists():
        console.print(f"[yellow]Project already initialized at {project_config_path}[/yellow]")
        raise typer.Exit(0)
        
    config = ProjectConfig(profile=profile)
    save_model(project_config_path, config)
    console.print(f"[green]Initialized MAAM project at {project_dir}[/green]")
    if profile:
        console.print(f"Bound to profile: [cyan]{profile}[/cyan]")
    console.print("Run 'maam sync' to materialize assets.")

if __name__ == "__main__":
    app()

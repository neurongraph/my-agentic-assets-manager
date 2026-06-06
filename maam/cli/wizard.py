import questionary
from pathlib import Path
from rich.console import Console
from rich.table import Table
from maam.config.models import UserConfig, ProfileConfig, RegistryConfig, ProjectConfig, AssetKind
from maam.config.io import load_model, save_model
from maam.config.paths import get_user_config_path, get_maam_home, get_project_dir, get_project_config_path
from maam.catalog.manager import CatalogManager
from maam.core.service import MAAMService

console = Console()

def run_wizard():
    while True:
        console.print("\n[bold green]MAAM Guided Setup Wizard[/bold green]")
        
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "1. View current configuration (Registries & Profiles)",
                "2. Register or Sync registries (GitHub)",
                "3. Build or Update a profile (Combine assets into a template)",
                "4. Sync current project (Update agents/skills)",
                "5. Initialize a new project in this directory",
                "6. Exit"
            ]
        ).ask()

        if choice == "1. View current configuration (Registries & Profiles)":
            view_config()
        elif choice == "2. Register or Sync registries (GitHub)":
            manage_registries_wizard()
        elif choice == "3. Build or Update a profile (Combine assets into a template)":
            manage_profiles_wizard()
        elif choice == "4. Sync current project (Update agents/skills)":
            sync_project_wizard()
        elif choice == "5. Initialize a new project in this directory":
            init_project_wizard()
        elif choice == "6. Exit" or choice is None:
            break

def view_config():
    path = get_user_config_path()
    try:
        config = load_model(UserConfig, path)
    except:
        config = UserConfig()
        
    if config.registries:
        table = Table(title="Registered Repositories")
        table.add_column("Name", style="green")
        table.add_column("URL", style="blue")
        for name, reg in config.registries.items():
            table.add_row(name, reg.url)
        console.print(table)
    else:
        console.print("[yellow]No registries registered.[/yellow]")

    home = get_maam_home()
    profiles_dir = home / "profiles"
    profiles = list(profiles_dir.glob("*.yaml")) if profiles_dir.exists() else []
    
    if profiles:
        p_table = Table(title="Available Profiles")
        p_table.add_column("Name", style="cyan")
        p_table.add_column("Assets", style="green")
        for p_path in sorted(profiles):
            try:
                p = load_model(ProfileConfig, p_path)
                # Show assets with their kind prefixes
                p_table.add_row(p.name, "\n".join(p.assets))
            except: continue
        console.print(p_table)
    else:
        console.print("[yellow]No profiles found.[/yellow]")

def manage_registries_wizard():
    sub_choice = questionary.select(
        "Registry Management:",
        choices=[
            "Add a new GitHub registry",
            "Sync all registries (Pull latest from GitHub)",
            "Back"
        ]
    ).ask()

    if sub_choice == "Add a new GitHub registry":
        add_registry_wizard()
    elif sub_choice == "Sync all registries (Pull latest from GitHub)":
        sync_registries_action()

def add_registry_wizard():
    name = questionary.text("Enter a name for the registry (e.g., 'superpowers'):").ask()
    url = questionary.text("Enter the Git URL (e.g., 'https://github.com/user/repo'):").ask()
    
    if name and url:
        path = get_user_config_path()
        try:
            config = load_model(UserConfig, path)
        except:
            config = UserConfig()
            
        config.registries[name] = RegistryConfig(url=url)
        save_model(path, config)
        console.print(f"\n[green]Registry '{name}' registered![/green]")
        if questionary.confirm("Would you like to pull the assets from this registry now?").ask():
            sync_registries_action()

def sync_registries_action():
    try:
        config = load_model(UserConfig, get_user_config_path())
    except:
        config = UserConfig()
    manager = CatalogManager(config)
    console.print("Pulling assets from GitHub...")
    manager.update_registries()
    console.print("[green]Registries updated successfully.[/green]")

def manage_profiles_wizard():
    sub_choice = questionary.select(
        "Profile Management:",
        choices=[
            "Build a new profile",
            "Update an existing profile",
            "Back"
        ]
    ).ask()

    if sub_choice == "Build a new profile":
        build_profile_wizard()
    elif sub_choice == "Update an existing profile":
        update_profile_wizard()

def build_profile_wizard():
    name = questionary.text("Enter a name for the new profile:").ask()
    if not name: return
    save_profile_wizard(name)

def update_profile_wizard():
    home = get_maam_home()
    profiles_dir = home / "profiles"
    profiles = [p.stem for p in profiles_dir.glob("*.yaml")] if profiles_dir.exists() else []
    
    if not profiles:
        console.print("[yellow]No profiles found to update.[/yellow]")
        return
        
    name = questionary.select("Select a profile to update:", choices=profiles).ask()
    if name:
        save_profile_wizard(name)

def save_profile_wizard(name: str):
    try:
        config = load_model(UserConfig, get_user_config_path())
    except:
        config = UserConfig()
    manager = CatalogManager(config)
    all_assets = manager.list_assets()
    
    if not all_assets:
        console.print("[yellow]No assets found. Add or sync GitHub registries first.[/yellow]")
        return
        
    existing_identifiers = []
    existing_desc = ""
    profile_path = get_maam_home() / "profiles" / f"{name}.yaml"
    if profile_path.exists():
        try:
            existing = load_model(ProfileConfig, profile_path)
            existing_identifiers = existing.assets
            existing_desc = existing.description or ""
        except: pass

    asset_choices = []
    for (kind, a_name) in sorted(all_assets.keys()):
        identifier = f"{kind}:{a_name}"
        checked = (identifier in existing_identifiers or a_name in existing_identifiers)
        
        asset_choices.append(questionary.Choice(
            title=f"[{kind}] {a_name}", 
            value=identifier,
            checked=checked
        ))
        
    selected_assets = questionary.checkbox(
        f"Select assets for profile '{name}':",
        choices=asset_choices
    ).ask()
    
    if selected_assets is not None:
        description = questionary.text("Enter a description for this profile:", default=existing_desc).ask()
        profile = ProfileConfig(name=name, description=description, assets=selected_assets)
        
        profiles_dir = get_maam_home() / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        save_model(profiles_dir / f"{name}.yaml", profile)
        console.print(f"\n[green]Profile '{name}' saved successfully with explicit identifiers![/green]")

def sync_project_wizard():
    project_dir = get_project_dir()
    project_config_path = get_project_config_path(project_dir)
    
    if not project_config_path.exists():
        console.print("[yellow]This directory is not initialized as a MAAM project.[/yellow]")
        if questionary.confirm("Would you like to initialize it now?").ask():
            init_project_wizard()
        return

    try:
        user_config = load_model(UserConfig, get_user_config_path())
    except:
        user_config = UserConfig()
    
    service = MAAMService(user_config, project_dir)
    console.print(f"Syncing project at {project_dir}...")
    service.sync()
    console.print("[green]Project synced successfully![/green]")

def init_project_wizard():
    home = get_maam_home()
    profiles_dir = home / "profiles"
    profiles = list(profiles_dir.glob("*.yaml")) if profiles_dir.exists() else []
    
    profile_choices = ["None (Custom setup)"] + [p.stem for p in profiles]
    selected_profile = questionary.select(
        "Select a profile for this project:",
        choices=profile_choices
    ).ask()
    
    profile_name = None if selected_profile == "None (Custom setup)" else selected_profile
    
    project_dir = get_project_dir()
    project_config_path = get_project_config_path(project_dir)
    
    config = ProjectConfig(profile=profile_name)
    save_model(project_config_path, config)
    
    console.print(f"\n[green]Project initialized at {project_dir}[/green]")
    if questionary.confirm("Would you like to sync assets now?").ask():
        sync_project_wizard()

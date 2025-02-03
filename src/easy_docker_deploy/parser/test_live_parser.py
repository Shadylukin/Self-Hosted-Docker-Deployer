"""
Test script for parsing the live awesome-selfhosted repository.
"""
from rich.console import Console
from rich.table import Table
from easy_docker_deploy.parser.github_parser import GithubParser

def main():
    """Main function to test the parser."""
    console = Console()
    
    # Initialize parser
    parser = GithubParser()
    
    # Fetch and parse repository
    console.print("🔍 Fetching awesome-selfhosted repository...")
    content = parser.fetch_repository()
    
    console.print("📝 Parsing content...")
    parser.parse_content(content)
    
    # Get statistics
    all_apps = parser.get_applications()
    docker_apps = parser.get_docker_ready_applications()
    
    # Print summary
    console.print(f"\n📊 Found {len(all_apps)} applications")
    console.print(f"🐳 {len(docker_apps)} applications have Docker support")
    
    # Create a table of Docker-ready applications
    table = Table(title="Docker-Ready Applications")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Language", style="yellow")
    table.add_column("License", style="magenta")
    table.add_column("Docker URL", style="blue", no_wrap=False)
    
    for app in sorted(docker_apps, key=lambda x: x.name)[:20]:  # Show first 20 for brevity
        table.add_row(
            app.name,
            app.category,
            app.language or "N/A",
            app.license_type or "N/A",
            app.docker_url or "N/A"
        )
    
    console.print(table)

if __name__ == "__main__":
    main() 
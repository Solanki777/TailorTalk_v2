from jinja2 import Environment, FileSystemLoader
from pathlib import Path

try:
    templates_dir = Path(__file__).resolve().parent / "app" / "templates"
    print("Templates directory:", templates_dir)
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    
    # Try to get template
    print("Loading index.html...")
    template = env.get_template("index.html")
    print("Loaded template successfully!")
    
    # Try to render
    print("Rendering...")
    html = template.render(title="TestPilot AI - Home", request=None)
    print("Rendered successfully! Length:", len(html))
except Exception as e:
    import traceback
    traceback.print_exc()

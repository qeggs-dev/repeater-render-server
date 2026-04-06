from render_server.api import Resource
from render_server.global_config_manager import ConfigManager

def main():
    ConfigManager.load(create_if_missing=True)
    # Get the config
    configs = ConfigManager.get_configs()

    # Create a new resource
    resource = Resource()

    # Initialize the resource
    resource.init_all()

    # Start the server
    resource.run_server(
        configs.server.host,
        configs.server.port,
        configs.server.workers,
        configs.server.reload
    )

if __name__ == "__main__":
    main()
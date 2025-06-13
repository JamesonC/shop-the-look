import json
from api.config import settings, env_file


def main():
    info = {
        "project_id": settings.project_id,
        "env_file": env_file,
    }
    print(json.dumps(info))


if __name__ == "__main__":
    main()

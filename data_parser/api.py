import requests

class API():
    def __init__(self) -> None:
        pass

    def get_monthly_archive(self, user: str) -> list[str]:
        monthly_archive_url = f"https://api.chess.com/pub/player/{user.lower()}/games/archives"
        headers = {
            'User-Agent': 'YourAppName/1.0'  # Replace 'YourAppName/1.0' with your app's name and version
        }
        response = requests.get(monthly_archive_url, headers=headers)
        if response.status_code == 200:
            return response.json()["archives"]
        elif response.status_code == 403:
            print(f"Access forbidden: {response.status_code}")
        else:
            print(f"Failed to retrieve data: {response.status_code}")        


    def get_games_from_month(self, month_url: str) -> list[dict]:
        headers = {
            'User-Agent': 'YourAppName/1.0'  # Replace 'YourAppName/1.0' with your app's name and version
        }
        response = requests.get(month_url, headers=headers)
        if response.status_code == 200:
            return response.json()["games"]
        elif response.status_code == 403:
            print(f"Access forbidden: {response.status_code}")
        else:
            print(f"Failed to retrieve data: {response.status_code}")
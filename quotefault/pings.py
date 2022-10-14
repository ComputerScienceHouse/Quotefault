from quotefault import app
import requests

def send_quote_ping(user):
    pings_quote_route = app.config.get("PINGS_QUOTE_ROUTE")
    pings_token = app.config.get("PINGS_TOKEN")
    requests.post(
        f"https://pings.csh.rit.edu/service/route/{pings_quote_route}/ping",
        json = {
            "username": user,
            "body": "You have been quoted!!!"
        },
        headers = {
            "Authorization": f"Bearer {pings_token}"
        }
    )
    print(f"Sent ping to {user}")

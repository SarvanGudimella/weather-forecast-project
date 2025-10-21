from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
from meteostat import Point, Daily
import os  # <-- for environment variables

app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.environ.get("API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error_message = None
    historical_avg = None
    comparison = None

    if request.method == "POST":
        city = request.form.get("city")
        if not city:
            error_message = "Please enter a city name"
        else:
            params = {"q": city, "appid": API_KEY, "units": "metric"}
            response = requests.get(BASE_URL, params=params)

            if response.status_code == 200:
                weather_data = response.json()
                lat = weather_data["coord"]["lat"]
                lon = weather_data["coord"]["lon"]

                today = datetime.now()
                avg_temps = []

                for year_offset in range(1, 6):
                    try:
                        year = today.year - year_offset
                        date_past = datetime(year, today.month, today.day)
                        start = date_past - timedelta(days=1)
                        end = date_past + timedelta(days=1)

                        location = Point(lat, lon)
                        data = Daily(location, start, end).fetch()

                        if not data.empty and "tavg" in data.columns:
                            avg_temps.extend(data["tavg"].dropna().tolist())
                    except:
                        continue

                if avg_temps:
                    historical_avg = round(sum(avg_temps) / len(avg_temps), 1)
                    current_temp = weather_data["main"]["temp"]

                    if current_temp > historical_avg + 1:
                        comparison = "Hotter than usual 🌡️"
                    elif current_temp < historical_avg - 1:
                        comparison = "Cooler than usual ❄️"
                    else:
                        comparison = "Similar to average 🌤️"
                else:
                    historical_avg = "N/A"
                    comparison = "No historical data available 📉"

            else:
                error_message = f"City '{city}' not found or API error."

    return render_template(
        "index.html",
        weather_data=weather_data,
        error_message=error_message,
        historical_avg=historical_avg,
        comparison=comparison
    )

if __name__ == "__main__":
    app.run(debug=True)

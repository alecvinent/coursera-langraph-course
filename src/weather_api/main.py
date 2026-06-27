from datetime import date, time

from fastapi import FastAPI, HTTPException

from weather_api.models import DailyForecast, ErrorResponse, HourlyForecast, WeatherResponse, get_weather_forecast_icon

SAMPLE_DATA: dict[str, WeatherResponse] = {
    "New York": WeatherResponse(
        location="New York",
        temperature=72,
        unit="imperial",
        daily=[
            DailyForecast(
                date=date(2026, 6, 26),
                temperature=72,
                highest_temperature=82,
                lowest_temperature=65,
                sunrise="05:27",
                sunset="20:31",
                weather_image=get_weather_forecast_icon("SUNNY"),
                hourly=[
                    HourlyForecast(time=time(6, 0), temperature=65, feels_like=64, humidity=70, kind="SUNNY", description="Sunny", wind_speed=8, precipitation=0.0, visibility=10.0, pressure=30.1),
                    HourlyForecast(time=time(9, 0), temperature=70, feels_like=70, humidity=60, kind="SUNNY", description="Sunny", wind_speed=9, precipitation=0.0, visibility=10.0, pressure=30.1),
                    HourlyForecast(time=time(12, 0), temperature=78, feels_like=78, humidity=45, kind="PARTLY_CLOUDY", description="Partly Cloudy", wind_speed=10, precipitation=0.0, visibility=10.0, pressure=30.0),
                    HourlyForecast(time=time(15, 0), temperature=82, feels_like=81, humidity=40, kind="PARTLY_CLOUDY", description="Partly Cloudy", wind_speed=12, precipitation=0.0, visibility=10.0, pressure=29.9),
                    HourlyForecast(time=time(18, 0), temperature=78, feels_like=78, humidity=50, kind="SUNNY", description="Sunny", wind_speed=10, precipitation=0.0, visibility=10.0, pressure=29.9),
                    HourlyForecast(time=time(21, 0), temperature=72, feels_like=71, humidity=65, kind="CLEAR", description="Clear", wind_speed=7, precipitation=0.0, visibility=10.0, pressure=30.0),
                ],
            ),
            DailyForecast(
                date=date(2026, 6, 27),
                temperature=68,
                highest_temperature=75,
                lowest_temperature=62,
                sunrise="05:27",
                sunset="20:31",
                weather_image=get_weather_forecast_icon("CLOUDY"),
                hourly=[
                    HourlyForecast(time=time(6, 0), temperature=62, feels_like=61, humidity=80, kind="CLOUDY", description="Cloudy", wind_speed=10, precipitation=0.1, visibility=8.0, pressure=29.8),
                    HourlyForecast(time=time(9, 0), temperature=64, feels_like=63, humidity=78, kind="LIGHT_RAIN", description="Light Rain", wind_speed=12, precipitation=0.2, visibility=6.0, pressure=29.8),
                    HourlyForecast(time=time(12, 0), temperature=70, feels_like=70, humidity=65, kind="CLOUDY", description="Cloudy", wind_speed=11, precipitation=0.1, visibility=8.0, pressure=29.7),
                    HourlyForecast(time=time(15, 0), temperature=75, feels_like=75, humidity=55, kind="PARTLY_CLOUDY", description="Partly Cloudy", wind_speed=13, precipitation=0.0, visibility=10.0, pressure=29.7),
                    HourlyForecast(time=time(18, 0), temperature=72, feels_like=71, humidity=60, kind="PARTLY_CLOUDY", description="Partly Cloudy", wind_speed=10, precipitation=0.0, visibility=10.0, pressure=29.8),
                    HourlyForecast(time=time(21, 0), temperature=68, feels_like=67, humidity=72, kind="CLEAR", description="Clear", wind_speed=8, precipitation=0.0, visibility=10.0, pressure=29.9),
                ],
            ),
        ],
    ),
    "London": WeatherResponse(
        location="London",
        temperature=55,
        unit="imperial",
        daily=[
            DailyForecast(
                date=date(2026, 6, 26),
                temperature=55,
                highest_temperature=62,
                lowest_temperature=50,
                sunrise="04:45",
                sunset="21:20",
                weather_image=get_weather_forecast_icon("CLOUDY"),
                hourly=[
                    HourlyForecast(time=time(6, 0), temperature=50, feels_like=47, humidity=85, kind="CLOUDY", description="Overcast", wind_speed=12, precipitation=0.3, visibility=5.0, pressure=29.6),
                    HourlyForecast(time=time(9, 0), temperature=53, feels_like=50, humidity=80, kind="LIGHT_RAIN", description="Light Rain", wind_speed=14, precipitation=0.4, visibility=4.0, pressure=29.6),
                    HourlyForecast(time=time(12, 0), temperature=58, feels_like=55, humidity=72, kind="CLOUDY", description="Cloudy", wind_speed=13, precipitation=0.2, visibility=6.0, pressure=29.7),
                    HourlyForecast(time=time(15, 0), temperature=62, feels_like=60, humidity=65, kind="CLOUDY", description="Cloudy", wind_speed=12, precipitation=0.1, visibility=8.0, pressure=29.7),
                    HourlyForecast(time=time(18, 0), temperature=60, feels_like=58, humidity=70, kind="PARTLY_CLOUDY", description="Partly Cloudy", wind_speed=10, precipitation=0.0, visibility=10.0, pressure=29.8),
                    HourlyForecast(time=time(21, 0), temperature=55, feels_like=53, humidity=78, kind="CLEAR", description="Clear", wind_speed=8, precipitation=0.0, visibility=10.0, pressure=29.9),
                ],
            ),
        ],
    ),
}


app = FastAPI(
    title="Weather API",
    version="0.1.0",
)


@app.get("/weather/{location}", response_model=WeatherResponse, responses={404: {"model": ErrorResponse}})
async def get_weather(location: str) -> WeatherResponse:
    data = SAMPLE_DATA.get(location)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Weather data not found for '{location}'")
    return data


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

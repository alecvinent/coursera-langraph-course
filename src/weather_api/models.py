from datetime import date, time

from pydantic import BaseModel


BASE_URL = "https://openweathermap.org/img/wn"

ICON_MAP: dict[str, str] = {
    "SUNNY": "01d",
    "CLEAR": "01d",
    "PARTLY_CLOUDY": "02d",
    "CLOUDY": "03d",
    "VERY_CLOUDY": "04d",
    "FOG": "50d",
    "DRIZZLE": "50d",
    "LIGHT_SHOWERS": "10d",
    "LIGHT_RAIN": "10d",
    "HEAVY_SHOWERS": "09d",
    "HEAVY_RAIN": "09d",
    "LIGHT_SLEET": "13d",
    "LIGHT_SLEET_SHOWERS": "13d",
    "LIGHT_SNOW": "13d",
    "HEAVY_SNOW": "13d",
    "LIGHT_SNOW_SHOWERS": "13d",
    "HEAVY_SNOW_SHOWERS": "13d",
    "THUNDERY_SHOWERS": "11d",
    "THUNDERY_HEAVY_RAIN": "11d",
    "THUNDERY_SNOW_SHOWERS": "11d",
}


def get_weather_forecast_icon(kind: str) -> str:
    code = ICON_MAP.get(kind.upper(), "01d")
    return f"{BASE_URL}/{code}@2x.png"


class HourlyForecast(BaseModel):
    time: time
    temperature: int
    feels_like: int
    humidity: int
    kind: str
    description: str
    wind_speed: int
    precipitation: float
    visibility: float
    pressure: float


class DailyForecast(BaseModel):
    date: date
    temperature: int
    highest_temperature: int
    lowest_temperature: int
    sunrise: str
    sunset: str
    weather_image: str
    hourly: list[HourlyForecast]


class WeatherResponse(BaseModel):
    location: str
    temperature: int
    unit: str
    daily: list[DailyForecast]


class ErrorResponse(BaseModel):
    error: str

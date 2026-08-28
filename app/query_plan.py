from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Variable = Literal["temperature", "salinity", "oxygen", "chlorophyll", "bbp700", "nitrate", "ph"]
Visualization = Literal["map", "depth_profile", "depth_time", "trajectory", "comparison", "table"]


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Literal["profile_query", "nearest_floats", "region_compare", "general_search"] = "general_search"
    parameter: Variable | None = None
    variables: list[Variable] = Field(default_factory=lambda: ["temperature"], min_length=1, max_length=8)
    start_date: date | None = None
    end_date: date | None = None
    relative_months: int | None = Field(default=None, ge=1, le=120)
    latitude_min: float | None = Field(default=None, ge=-90, le=90)
    latitude_max: float | None = Field(default=None, ge=-90, le=90)
    longitude_min: float | None = Field(default=None, ge=-180, le=180)
    longitude_max: float | None = Field(default=None, ge=-180, le=180)
    target_latitude: float | None = Field(default=None, ge=-90, le=90)
    target_longitude: float | None = Field(default=None, ge=-180, le=180)
    target_lat: float | None = Field(default=None, ge=-90, le=90)
    target_lon: float | None = Field(default=None, ge=-180, le=180)
    radius_km: float | None = Field(default=None, gt=0, le=20000)
    min_depth: float | None = Field(default=None, ge=0)
    max_depth: float | None = Field(default=None, ge=0)
    float_ids: list[int] = Field(default_factory=list, max_length=100)
    status: Literal["ACTIVE", "INACTIVE"] | None = None
    region: str | None = None
    limit: int = Field(default=1000, ge=1, le=10000)
    visualization: Visualization = "map"
    aggregation: Literal["mean", "min", "max", "none"] = "mean"
    sort_by: Literal["timestamp", "depth", "distance_km"] = "timestamp"

    @field_validator("variables")
    @classmethod
    def unique_variables(cls, values: list[Variable]) -> list[Variable]:
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.parameter and not self.variables:
            self.variables = [self.parameter]
        if self.parameter and self.variables == ["temperature"]:
            self.variables = [self.parameter]
        if self.target_latitude is None:
            self.target_latitude = self.target_lat
        if self.target_longitude is None:
            self.target_longitude = self.target_lon
        if self.latitude_min is not None and self.latitude_max is not None and self.latitude_min > self.latitude_max:
            raise ValueError("latitude_min must not exceed latitude_max")
        if self.longitude_min is not None and self.longitude_max is not None and self.longitude_min > self.longitude_max:
            raise ValueError("longitude_min must not exceed longitude_max")
        if self.min_depth is not None and self.max_depth is not None and self.min_depth > self.max_depth:
            raise ValueError("min_depth must not exceed max_depth")
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date must not exceed end_date")
        if self.intent == "nearest_floats" and (self.target_latitude is None or self.target_longitude is None):
            raise ValueError("nearest_floats requires target coordinates")
        return self

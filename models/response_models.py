"""Response models for structured output."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    """Structured weather response."""
    location: str = Field(description="Location name")
    current_temperature: str = Field(description="Current temperature with unit")
    condition: str = Field(description="Weather condition")
    humidity: Optional[str] = Field(None, description="Humidity percentage")
    wind_speed: Optional[str] = Field(None, description="Wind speed")
    forecast: Optional[List[Dict[str, str]]] = Field(None, description="Weather forecast")
    message: str = Field(description="Human-readable weather message")

class ComparisonResponse(BaseModel):
    """Structured comparison response."""
    comparison_type: str = Field(description="Type of comparison")
    items: List[Dict[str, Any]] = Field(description="Items being compared")
    winner: Optional[str] = Field(None, description="Better option")
    difference: str = Field(description="Key differences")
    summary: str = Field(description="Comparison summary")
    message: str = Field(description="Human-readable comparison message")

class TableResponse(BaseModel):
    """Structured table response."""
    title: Optional[str] = Field(None, description="Table title")
    headers: List[str] = Field(description="Column headers")
    rows: List[Dict[str, str]] = Field(description="Table rows")
    message: str = Field(description="Human-readable table description")

class ListResponse(BaseModel):
    """Structured list response."""
    title: Optional[str] = Field(None, description="List title")
    type: str = Field(default="unordered", description="List type")
    items: List[Dict[str, str]] = Field(description="List items")
    message: str = Field(description="Human-readable list description")

class YesNoResponse(BaseModel):
    """Structured yes/no response."""
    question: Optional[str] = Field(None, description="Question being answered")
    answer: str = Field(description="yes, no, or unknown")
    confidence: str = Field(default="medium", description="Confidence level")
    reasoning: str = Field(description="Explanation for the answer")
    additional_info: Optional[str] = Field(None, description="Additional information")
    message: str = Field(description="Human-readable response")

class ErrorResponse(BaseModel):
    """Structured error response."""
    error_type: str = Field(description="Type of error")
    error_message: str = Field(description="Error message")
    details: str = Field(description="Detailed error information")
    suggestion: str = Field(description="Suggestion for resolution")
    error_code: Optional[str] = Field(None, description="Error code")
    message: str = Field(description="Human-readable error message")

class GeneralResponse(BaseModel):
    """General structured response."""
    #content: str = Field(description="Response content")
    component_type: str = Field(description="UI component type")
    data: Optional[str] = Field(None, description="Additional structured data as JSON string")
    message: str = Field(description="Human-readable response message")

class FlightSearchResponse(BaseModel):
    """Structured flight search response."""
    origin_city: str = Field(description="The departure city or airport code.")
    destination_city: str = Field(description="The arrival city or airport code.")
    travel_date: str = Field(description="The requested travel date.")
    flights_found: Optional[List[Dict[str, Union[str, int, float]]]] = Field(description="List of available flight options. This list should be empty if no flights were found or an error occurred.")
    message: str = Field(description="A concise, human-readable summary of the flight search results and recommendations, including explicit mention of any tool error.")

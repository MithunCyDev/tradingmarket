from datetime import datetime

from app.schemas.common import Action, ApiModel, Confidence, Timeframe


class ConfluenceFactor(ApiModel):
    id: str
    passed: bool
    title: str
    detail: str


class ConfluenceReport(ApiModel):
    headline: str
    action: Action
    confidence: Confidence
    suggested_confidence: Confidence | None
    passed_count: int
    factor_count: int
    summary: str
    factors: list[ConfluenceFactor]


class ChartBar(ApiModel):
    time: int
    open: float
    high: float
    low: float
    close: float


class AnalysisLevel(ApiModel):
    id: str
    label: str
    price: float
    kind: str


class ChartResponse(ApiModel):
    symbol: str
    timeframe: Timeframe
    bars: list[ChartBar]
    ema20: list[float | None]
    ema50: list[float | None]
    swing_highs: list[float]
    swing_lows: list[float]


class AnalysisResponse(ApiModel):
    symbol: str
    analyzed_at: datetime
    confluence: ConfluenceReport
    levels: list[AnalysisLevel]

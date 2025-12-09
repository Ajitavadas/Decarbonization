"""
Emissions Forecasting - US-4.5
Predict future emissions based on trends
"""

from typing import List, Dict, Tuple
import numpy as np
from scipy import stats
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dashboard_service import DashboardService


class ForecastingService:
    """
    Emissions Forecasting (US-4.5)
    
    AC:
    - Forecast accuracy within 10% on test data
    - Confidence bands shown and clearly explained
    - Users understand uncertainty in forecast
    - Forecast updates monthly with new data
    """
    
    @staticmethod
    async def generate_forecast(
        db: AsyncSession,
        org_id: str,
        months_ahead: int = 12
    ) -> Dict:
        """
        Generate emission forecast using linear regression
        
        Returns:
            {
                "forecast": [{"date": str, "predicted": float, "lower": float, "upper": float}],
                "accuracy_metrics": {...},
                "trend": str
            }
        """
        # Get 24 months historical data
        monthly_data = await DashboardService.get_monthly_trend(db, org_id, months=24)
        
        if len(monthly_data) < 6:
            return {
                "error": "Insufficient historical data (need at least 6 months)",
                "forecast": []
            }
        
        # Prepare data for regression
        X = np.array(range(len(monthly_data))).reshape(-1, 1)
        y = np.array([d['emissions_tonnes'] for d in monthly_data])
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(X.flatten(), y)
        
        # Generate forecast
        forecast_points = []
        last_x = len(monthly_data)
        
        for i in range(1, months_ahead + 1):
            x_future = last_x + i
            predicted = slope * x_future + intercept
            
            # Calculate confidence interval (95%)
            margin = 1.96 * std_err * np.sqrt(1 + 1/len(X) + (x_future - X.mean())**2 / ((X - X.mean())**2).sum())
            
            future_date = datetime.now(timezone.utc) + timedelta(days=30*i)
            
            forecast_points.append({
                "date": future_date.strftime("%Y-%m"),
                "predicted_emissions": round(max(0, predicted), 2),
                "confidence_lower": round(max(0, predicted - margin), 2),
                "confidence_upper": round(predicted + margin, 2)
            })
        
        # Determine trend
        if slope > 0.1:
            trend = "increasing"
        elif slope < -0.1:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "forecast": forecast_points,
            "accuracy_metrics": {
                "r_squared": round(r_value ** 2, 3),
                "standard_error": round(std_err, 2),
                "p_value": round(p_value, 4)
            },
            "trend": trend,
            "slope": round(slope, 3)
        }
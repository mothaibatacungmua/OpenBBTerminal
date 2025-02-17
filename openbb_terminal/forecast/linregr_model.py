# pylint: disable=too-many-arguments
"""Linear Regression Model"""
__docformat__ = "numpy"

import logging
from typing import Any, Tuple, Union, List, Optional
import warnings


import pandas as pd

from darts import TimeSeries
from darts.models import LinearRegressionModel
from openbb_terminal.decorators import log_start_end

from openbb_terminal.forecast import helpers

logger = logging.getLogger(__name__)


@log_start_end(log=logger)
def get_linear_regression_data(
    data: Union[pd.Series, pd.DataFrame],
    target_column: str = "close",
    n_predict: int = 5,
    past_covariates: str = None,
    train_split: float = 0.85,
    forecast_horizon: int = 5,
    output_chunk_length: int = 5,
    lags: Union[int, List[int]] = 14,
    random_state: Optional[int] = None,
) -> Tuple[List[TimeSeries], List[TimeSeries], List[TimeSeries], float, Any]:
    """Perform Linear Regression Forecasting

    Parameters
    ----------
    data: Union[pd.Series, pd.DataFrame]
        Input Data
    target_column: str
        Target column to forecast. Defaults to "close".
    n_predict: int
        Days to predict. Defaults to 5.
    train_split: float
        Train/val split. Defaults to 0.85.
    past_covariates: str
        Multiple secondary columns to factor in when forecasting. Defaults to None.
    forecast_horizon: int
        Forecast horizon when performing historical forecasting. Defaults to 5.
    output_chunk_length: int
        The length of the forecast of the model. Defaults to 1.
    lags: Union[int, List[int]]
        lagged target values to predict the next time step
    random_state: Optional[int]
        The state for the model

    Returns
    -------
    List[TimeSeries]
        Adjusted Data series
    List[TimeSeries]
        Historical forecast by best RNN model
    List[TimeSeries]
        list of Predictions
    float
        Mean average precision error
    Any
        Best Linear Regression Model
    """
    use_scalers = False
    probabilistic = True

    scaler, ticker_series = helpers.get_series(
        data, target_column, is_scaler=use_scalers
    )

    past_covariate_whole, _, _ = helpers.past_covs(
        past_covariates, data, train_split, use_scalers
    )

    if past_covariates is not None:
        lags_past_covariates = lags
    else:
        lags_past_covariates = None

    lin_reg_model = LinearRegressionModel(
        output_chunk_length=output_chunk_length,
        lags=lags,
        lags_past_covariates=lags_past_covariates,
        likelihood="quantile",
        quantiles=[0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
        random_state=random_state,
    )

    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        if past_covariates is not None:
            lin_reg_model.fit(
                series=ticker_series, past_covariates=past_covariate_whole
            )
        else:
            lin_reg_model.fit(series=ticker_series)

    return helpers.get_prediction(
        "Logistic Regression",
        probabilistic,
        use_scalers,
        scaler,
        past_covariates,
        lin_reg_model,
        ticker_series,
        past_covariate_whole,
        train_split,
        forecast_horizon,
        n_predict,
    )

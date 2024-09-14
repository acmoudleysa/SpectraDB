from spectradb.dataloaders import FluorescenceDataLoader, FTIRDataLoader, NMRDataLoader
import plotly.graph_objects as go
from typing import Union
import numpy as np



def contourplot(
        obj: FluorescenceDataLoader, 
        identifier: str
) -> go.Figure: 
    """
    Creates a contour plot of fluorescence data.

    Parameters:
    -----------
    obj : FluorescenceDataLoader
        Object containing fluorescence data and metadata.
    
    identifier : str
        Identifier for the dataset to plot.

    Returns:
    --------
    go.Figure
        Plotly contour plot showing intensity as a function of 
        excitation and emission wavelengths.
    """
    
    z = obj.data[identifier]
    x = obj.metadata[identifier]['Signal Metadata']['Emission']
    y = obj.metadata[identifier]['Signal Metadata']['Excitation']

    fig = go.Figure()
    fig.add_trace(go.Contour(
        z=z,
        x=x, 
        y=y, 
        colorscale="Cividis", 
        colorbar=dict(title="Intensity")
    ))

    fig.update_xaxes(nticks=10, title_text='Emission')
    fig.update_yaxes(nticks=10, title_text='Excitation')
    fig.update_layout(
        height=500, 
        width=600
    )
    
    return fig



def spectrum(
        obj: Union[FTIRDataLoader, NMRDataLoader]
) -> go.Figure:
    """
    Create a spectral plot from FTIR or NMR data.

    Args:
        obj (Union[FTIRDataLoader, NMRDataLoader]): Data loader object with spectral data.

    Returns:
        go.Figure: Plotly figure with the spectral plot.

    Raises:
        TypeError: If `obj` is neither `FTIRDataLoader` nor `NMRDataLoader`.
    """
    
    if isinstance(obj, FTIRDataLoader): 
        x = obj.metadata["Signal Metadata"]["Wavenumbers"]
        x_label = "Wavenumbers"
        y_label = "Transmittance"
    elif isinstance(obj, NMRDataLoader): 
        x = obj.metadata["Signal Metadata"]["ppm"]
        x_label = "ppm"
        y_label = "Intensity"
    else: 
        raise TypeError("The object shuold be an instance of `FTIRDataLoader` or `NMRDataLoader`.")
    
    y = obj.data

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=np.array(x, dtype=str),   # to avoid sorting
            y=y, 
            mode="lines"
        )
    )
        
    fig.update_layout(
                      height=500, 
                      width=600, 
                      plot_bgcolor='white'
                      )
    
    for axis in ['xaxis', 'yaxis']:
        fig.update_layout({
            axis: dict(
                mirror=True,
                title = x_label if axis == "xaxis" else y_label,
                ticks='outside',
                showline=True,
                linecolor='black',
                showgrid=False,
                nticks=10 if axis == 'xaxis' else 5
            )})
    
    return fig
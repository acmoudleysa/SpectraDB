from spectradb.dataloaders import FluorescenceDataLoader
import plotly.graph_objects as go


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

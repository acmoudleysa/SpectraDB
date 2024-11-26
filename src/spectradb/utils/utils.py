from spectradb.dataloaders import FluorescenceDataLoader, FTIRDataLoader, NMRDataLoader  # noqa: E501
import plotly.graph_objects as go
from typing import Union, Literal, overload, Optional, Iterable, Dict, List
import plotly_express as px
import pandas as pd


def _plot_fluorescence_spectrum(
        obj: FluorescenceDataLoader | Dict[str, FluorescenceDataLoader],
        identifier: str | List[str] | Dict[str, List[str]] | Dict[str, str],
        plot_type: str = "1D") -> go.Figure | List[go.Figure]:
    if plot_type not in ["1D", "2D"]:
        raise ValueError("Type of plot can only be 1D or 2D")

    if not isinstance(obj, dict):
        obj = {"obj1": obj}

    if isinstance(identifier, (str, list)):
        identifier = {"obj1": [identifier] if isinstance(identifier, str)
                      else identifier}

    plot_data = []
    for obj_name, dataloader in obj.items():
        selected_identifier = identifier.get(obj_name)
        if not selected_identifier:
            raise ValueError(f"No identifier specified for object {obj_name}")
        if isinstance(selected_identifier, str):
            selected_identifier = [selected_identifier]
        invalid_ids = set(selected_identifier) - dataloader.metadata.keys()
        if invalid_ids:
            raise ValueError(f"Invalid identifiers {invalid_ids} "
                             f"for {obj_name}.")

        for id_ in selected_identifier:
            data = dataloader.data[id_]
            em = dataloader.metadata[id_]['Signal Metadata']['Emission']
            ex = dataloader.metadata[id_]['Signal Metadata']['Excitation']  # noqa E501
            name = dataloader.metadata[id_]['Sample name']
            plot_data.append((data, em, ex, name))

    if plot_type == "1D":
        combined_df = pd.concat([(pd.DataFrame(data, columns=em)
                                  .assign(Excitation=ex, Identifier=name)
                                  .melt(id_vars=['Excitation', 'Identifier'],
                                        value_name='Intensity',
                                        var_name='Emission'))
                                for data, em, ex, name in plot_data],
                                ignore_index=True)
        single_identifier = (combined_df['Identifier'].nunique() == 1)
        fig = px.line(
            combined_df,
            x="Emission",
            y="Intensity",
            line_group="Excitation",
            **({"color": "Identifier"} if not single_identifier else {})
        )
        fig.update_traces(line=dict(width=1.5))
        return fig

    elif plot_type == "2D":
        figures = []
        for data, em, ex, name in plot_data:
            fig = go.Figure()
            fig.add_trace(go.Contour(
                z=data,
                x=em,
                y=ex,
                colorscale="Cividis",
                colorbar=dict(title="Intensity")
            ))
            fig.update_xaxes(nticks=10, title_text='Emission')
            fig.update_yaxes(nticks=10, title_text='Excitation')
            fig.update_layout(
                title=name,
                height=500,
                width=600
            )
            figures.append(fig)
        return figures


def _plot_spectrum_NMR_FTIR(
        obj: Union[FTIRDataLoader,
                   NMRDataLoader,
                   Iterable[FTIRDataLoader],
                   Iterable[NMRDataLoader]
                   ]
) -> go.Figure:
    """
    Create a spectral plot from FTIR or NMR data.

    Args:
        obj (Union[FTIRDataLoader, NMRDataLoader]): Data loader object
        with spectral data.

    Returns:
        go.Figure: Plotly figure with the spectral plot.

    Raises:
        TypeError: If `obj` is neither `FTIRDataLoader` nor `NMRDataLoader`.
    """
    # Checking types of objects and updating the plot labels
    if isinstance(obj[0], FTIRDataLoader):
        x_label = "Wavenumbers"
        y_label = "Transmittance"
    elif isinstance(obj[0], NMRDataLoader):
        x_label = "ppm"
        y_label = "Intensity"
    else:
        raise TypeError("The object shuold be an instance of `FTIRDataLoader` or `NMRDataLoader`.")  # noqa E501

    # Creating a figure
    fig = go.Figure()
    for i, object in enumerate(obj):
        # Fetching the x values
        x_data = object.metadata['Signal Metadata'][x_label]
        # Make sure the plot follows the order in which the wavelength
        # is provided in the original file
        if i == 0:
            reverse_x = x_data[1] < x_data[0]
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=object.data,
                mode="lines",
                name=object.metadata['Sample name']
                if object.metadata['Sample name']
                else object.metadata['Filename']
                )
                )
    # Since x ticks are float, we need to reverse it
    # if the wavenumbers in original file were in
    # descending order
    if reverse_x:
        fig.update_layout(xaxis_autorange='reversed')

# Update all traces with the same hover template
    for trace in fig.data:
        trace.hovertemplate = 'Name: %{data.name}<br>' + \
                            f'{x_label}: %{{x}}<br>' + \
                            f'{y_label}: %{{y}}<extra></extra>'
    fig.update_layout(
                    height=500,
                    width=600,
                    plot_bgcolor='white',
                    showlegend=True
                    )
    for axis in ['xaxis', 'yaxis']:
        fig.update_layout({
            axis: dict(
                mirror=True,
                title=x_label if axis == "xaxis" else y_label,
                ticks='outside',
                showline=True,
                linecolor='black',
                showgrid=False,
                nticks=10 if axis == 'xaxis' else 5
            )})
    return fig


@overload
def spectrum(
    obj: FTIRDataLoader | NMRDataLoader | Iterable[FTIRDataLoader]
    | Iterable[NMRDataLoader]
) -> go.Figure:
    ...


@overload
def spectrum(
    obj: FluorescenceDataLoader | Dict[str, FluorescenceDataLoader],
    identifier: str | List[str] | Dict[str, List[str]] | Dict[str, str],
    plot_type: Literal["1D", "2D"]
) -> go.Figure | List[go.Figure]:
    ...


def spectrum(
    obj: (
        FTIRDataLoader
        | NMRDataLoader
        | FluorescenceDataLoader
        | Iterable[FTIRDataLoader]
        | Iterable[NMRDataLoader]
        | Dict[str, FluorescenceDataLoader]
    ),
    identifier: Optional[str
                         | list[str]
                         | Dict[str, list[str]]
                         | Dict[str, str]] = None,
    plot_type: Optional[Literal["1D", "2D"]] = None
) -> go.Figure | List[go.Figure]:
    """
    Create a spectral plot from FTIR, NMR, or Fluorescence data.

    Args:
        obj: The data loader object. Can be FTIRDataLoader, NMRDataLoader, or FluorescenceDataLoader.
        identifier (str, optional): The identifier for the sample (only required for FluorescenceDataLoader).
        plot_type (str, optional): The type of plot to generate ("1D" or "2D", only required for FluorescenceDataLoader).

    Returns:
        go.Figure: A plotly figure object.

    Raises:
        TypeError: If the object type is unsupported.
        ValueError: If identifier or plot_type is missing for FluorescenceDataLoader.
    """  # noqa: E501
    if isinstance(obj, (FTIRDataLoader, NMRDataLoader)) or (
        isinstance(obj, list) and
        all(isinstance(o, (FTIRDataLoader, NMRDataLoader)) for o in obj)
    ):
        # Route to NMR/FTIR plotting function
        return _plot_spectrum_NMR_FTIR(obj)
    if isinstance(obj, (FluorescenceDataLoader, dict)):
        if not identifier or not plot_type:
            raise ValueError("For FluorescenceDataLoader, 'identifier' "
                             "and 'plot_type' are required.")
        return _plot_fluorescence_spectrum(obj, identifier, plot_type)

    raise TypeError("Unsupported object types")

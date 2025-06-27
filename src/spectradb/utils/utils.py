from spectradb.dataloaders import (
    FluorescenceDataLoader,
    FTIRDataLoader,
    NMRDataLoader,
)  # noqa: E501
import plotly.graph_objects as go
from typing import Union, Literal, Iterable, Dict, List, overload
import plotly_express as px
import pandas as pd
from functools import singledispatch


@singledispatch
def spectrum(obj, **kwargs):
    """
    Generic spectrum function for dispatching based on object type.

    Parameters:
    obj (object): The object representing spectral data.
    This should be passed as a **positional argument**.

    Keyword Arguments:
    - identifier: (Optional) A string or list of strings
    - plot_type: (Optional) Type of plot either "1D" or "2D" (default is "1D").

    Raises:
    TypeError: If the object type is unsupported or incorrectly passed.
    """
    if "obj" in kwargs:
        raise TypeError("The 'obj' argument must be passed "
                        "as a positional argument, not as a keyword argument. "
                        "Example: spectrum(FTIRDataLoader())")

    raise TypeError(f"Unsupported object type: {type(obj)}")


@spectrum.register
def _(obj: FTIRDataLoader) -> go.Figure:
    return _plot_spectrum_NMR_FTIR(obj)


@spectrum.register
def _(obj: NMRDataLoader) -> go.Figure:
    return _plot_spectrum_NMR_FTIR(obj)


@overload
def _(obj: tuple):
    ...


@spectrum.register
def _(obj: list) -> go.Figure:
    if all(isinstance(o, (FTIRDataLoader, NMRDataLoader)) for o in obj):
        return _plot_spectrum_NMR_FTIR(obj)
    raise TypeError("Unsupported iterable type")


@spectrum.register
def _(obj: FluorescenceDataLoader, *,
      identifier: Union[str, List[str]] = None,
      plot_type: Literal["1D", "2D"] = "1D") -> Union[go.Figure,
                                                      List[go.Figure]]:
    return _plot_fluorescence_spectrum(obj, identifier, plot_type)


@spectrum.register
def _(obj: dict, *,
      identifier: Union[Dict[str, List[str]], Dict[str, str]] = None,
      plot_type: Literal["1D", "2D"] = "1D") -> Union[go.Figure,
                                                      List[go.Figure]]:
    if all(isinstance(v, FluorescenceDataLoader) for v in obj.values()):
        return _plot_fluorescence_spectrum(obj,
                                           identifier,
                                           plot_type)
    raise TypeError("Unsupported dictionary type")


def _plot_fluorescence_spectrum(
<<<<<<< HEAD
    obj: FluorescenceDataLoader, identifier: str, plot_type: Literal["1D", "2D"]
) -> go.Figure:
    """
    Plot fluorescence spectrum using either 1D or 2D representation.
=======
        obj: FluorescenceDataLoader | Dict[str, FluorescenceDataLoader],
        identifier: str | List[str] | Dict[str, List[str]] | Dict[str, str],
        plot_type: str) -> go.Figure | List[go.Figure]:
    if plot_type not in ["1D", "2D"]:
        raise ValueError("Type of plot can only be 1D or 2D")
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac

    if not isinstance(obj, dict):
        obj = {"obj1": obj}

<<<<<<< HEAD
    Returns:
        go.Figure: A plotly figure object.
    """  # noqa: E501
    # fetching the data from the object
    data = obj.data[identifier]
    em = obj.metadata[identifier]["Signal Metadata"]["Emission"]
    ex = obj.metadata[identifier]["Signal Metadata"]["Excitation"]
=======
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
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac

    if plot_type == "1D":
<<<<<<< HEAD
        df = (
            pd.DataFrame(data, columns=em)
            .assign(Excitation=ex)
            .melt(id_vars=["Excitation"], value_name="Intensity", var_name="Emission")
        )
        fig = px.line(df, x="Emission", y="Intensity", line_group="Excitation")
        fig.update_traces(line=dict(width=1.2, color="rgb(49,130,189)"))
=======
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
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac
        return fig

    elif plot_type == "2D":
<<<<<<< HEAD
        fig = go.Figure()
        fig.add_trace(
            go.Contour(
=======
        figures = []
        for data, em, ex, name in plot_data:
            fig = go.Figure()
            fig.add_trace(go.Contour(
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac
                z=data,
                x=em,
                y=ex,
                colorscale="Cividis",
<<<<<<< HEAD
                colorbar=dict(title="Intensity"),
            )
        )

        fig.update_xaxes(nticks=10, title_text="Emission")
        fig.update_yaxes(nticks=10, title_text="Excitation")
        fig.update_layout(height=500, width=600)
        return fig
    else:
        raise TypeError("Type of plot can only be 1D or 2D.")
=======
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
        if len(figures) == 1:
            return figures[0]
        return figures
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac


def _plot_spectrum_NMR_FTIR(
    obj: Union[
        FTIRDataLoader, NMRDataLoader, Iterable[FTIRDataLoader], Iterable[NMRDataLoader]
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
    if isinstance(obj, (FTIRDataLoader, NMRDataLoader)):
        obj = [obj]
    if isinstance(obj[0], FTIRDataLoader):
        x_label = "Wavenumbers"
        y_label = "Transmittance"
    elif isinstance(obj[0], NMRDataLoader):
        x_label = "ppm"
        y_label = "Intensity"
    else:
        raise TypeError(
            "The object shuold be an instance of `FTIRDataLoader` or `NMRDataLoader`."
        )  # noqa E501

    # Creating a figure
    fig = go.Figure()
    for i, object in enumerate(obj):
        # Fetching the x values
        x_data = object.metadata["Signal Metadata"][x_label]
        # Make sure the plot follows the order in which the wavelength
        # is provided in the original file
        if i == 0:
            reverse_x = x_data[1] < x_data[0]
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=object.data,
                mode="lines",
                name=(
                    object.metadata["Sample name"]
                    if object.metadata["Sample name"]
                    else object.metadata["Filename"]
                ),
            )
        )
    # Since x ticks are float, we need to reverse it
    # if the wavenumbers in original file were in
    # descending order
    if reverse_x:
        fig.update_layout(xaxis_autorange="reversed")

<<<<<<< HEAD
    # updating the figure
    fig.update_layout(height=500, width=600, plot_bgcolor="white", showlegend=True)
    for axis in ["xaxis", "yaxis"]:
        fig.update_layout(
            {
                axis: dict(
                    mirror=True,
                    title=x_label if axis == "xaxis" else y_label,
                    ticks="outside",
                    showline=True,
                    linecolor="black",
                    showgrid=False,
                    nticks=10 if axis == "xaxis" else 5,
                )
            }
        )
    return fig


@overload
def spectrum(
    obj: Union[
        FTIRDataLoader, NMRDataLoader, Iterable[FTIRDataLoader], Iterable[NMRDataLoader]
    ]
) -> go.Figure: ...


@overload
def spectrum(
    obj: FluorescenceDataLoader, identifier: str, plot_type: Literal["1D", "2D"]
) -> go.Figure: ...


def spectrum(
    obj: Union[
        FTIRDataLoader,
        NMRDataLoader,
        FluorescenceDataLoader,
        Iterable[FTIRDataLoader],
        Iterable[NMRDataLoader],
    ],
    identifier: Optional[str] = None,
    plot_type: Optional[str] = None,
) -> go.Figure:
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
    # Checking if the provided object is an iterable or an element
    if not isinstance(obj, abc.Iterable):
        obj = [obj]

    # if it's an iterable we need to make sure they are of same type
    # Also need to make sure the user accidentally doesn't pass
    # mutliple Fluorescence objects. It's clear from the
    # function's type hints but just to make sure its robust.
    else:
        if not all(isinstance(object, type(obj[0])) for object in obj):
            raise TypeError(
                "Objects should all be of the same type "
                "(either FTIRDataLoader or NMRDataLoader)"
            )
        elif isinstance(obj[0], FluorescenceDataLoader) and len(obj) > 1:
            raise TypeError(
                "Multiple FluorescencenDataLoader objects " "not supported."
            )

    # if the object is of type FTIR or NMR
    if isinstance(obj[0], (FTIRDataLoader, NMRDataLoader)):
        return _plot_spectrum_NMR_FTIR(obj)

    # If the object is of type Fluorescence
    elif isinstance(obj[0], FluorescenceDataLoader):
        if not identifier or not plot_type:
            raise ValueError(
                "Identifier or plot_type must be provided "
                "for FluorescenceDataLoader object."
            )
        return _plot_fluorescence_spectrum(obj[0], identifier, plot_type)

    # Raising an error if its none of above
    else:
        raise TypeError(f"Unsupported object type: {type(obj[0])}")
=======
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
>>>>>>> a64c8437b8c6743b1f6032e236cc0d4e99dbc3ac

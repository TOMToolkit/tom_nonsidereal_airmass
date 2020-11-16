from django import template
from django.conf import settings
from dateutil.parser import parse
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly import offline

from tom_nonsidereal_airmass.utils import get_visibility
from tom_nonsidereal_airmass.forms import NonsiderealTargetVisibilityForm
from tom_targets.models import Target

from importlib import import_module
try:
    PLOTTING_FUNCTIONS_FOR_SCHEME = settings.PLOTTING_FUNCTIONS_FOR_SCHEME
except AttributeError:
    PLOTTING_FUNCTIONS_FOR_SCHEME = {
        'MPC_MINOR_PLANET': ['tom_nonsidereal_airmass.utils.get_arc',
                             'tom_nonsidereal_airmass.utils.get_visibility'],
        'EPHEMERIS': ['tom_nonsidereal_airmass.utils.get_eph_scheme_arc',
                      'tom_nonsidereal_airmass.utils.get_eph_scheme_visibility'],
    }

ARC_FUNCTIONS = {}
VIS_FUNCTIONS = {}
for p in PLOTTING_FUNCTIONS_FOR_SCHEME:
    module_name, function_name_arc = PLOTTING_FUNCTIONS_FOR_SCHEME.get(p)[0].rsplit('.', 1)
    function_name_vis = PLOTTING_FUNCTIONS_FOR_SCHEME.get(p)[1].rsplit('.', 1)[1]
    try:
        mod = import_module(module_name)
        arc_func = getattr(mod, function_name_arc)
        ARC_FUNCTIONS[p] = arc_func
        vis_func = getattr(mod, function_name_vis)
        VIS_FUNCTIONS[p] = vis_func
    except:
        pass

register = template.Library()


@register.inclusion_tag('tom_targets/partials/target_plan.html', takes_context=True)
def nonsidereal_target_plan(context):
    """
    Displays form and renders plot for visibility calculation. Using this templatetag to render a plot requires that
    the context of the parent view have values for start_time, end_time, and airmass.
    """
    request = context['request']
    plan_form = NonsiderealTargetVisibilityForm()
    visibility_graph = ''
    if all(request.GET.get(x) for x in ['start_time', 'end_time']):
        plan_form = NonsiderealTargetVisibilityForm({
            'start_time': request.GET.get('start_time'),
            'end_time': request.GET.get('end_time'),
            'airmass': request.GET.get('airmass'),
            'target': context['object'] if 'object' in context else context['target']
        })
        if plan_form.is_valid():
            start_time = parse(request.GET['start_time'])
            end_time = parse(request.GET['end_time'])
            if request.GET.get('airmass'):
                airmass_limit = float(request.GET.get('airmass'))
            else:
                airmass_limit = None
            visibility_data = VIS_FUNCTIONS.get(context['object'].scheme)(context['object'], start_time, end_time, 10, airmass_limit)
            plot_data = [
                go.Scatter(x=data[0], y=data[1], mode='lines', name=site) for site, data in visibility_data.items()
            ]
            layout = go.Layout(yaxis=dict(autorange='reversed'))
            visibility_graph = offline.plot(
                go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False
            )
    return {
        'form': plan_form,
        'target': context['object'] if 'object' in context else context['target'],
        'visibility_graph': visibility_graph
    }


@register.inclusion_tag('tom_targets/partials/target_distribution_nonsidereal.html')
def target_distribution_nonsidereal(targets):
    """
    Displays a plot showing on a map the locations of ALL targets in the TOM.
    Positions are plotted every ten days.
    """
    locations = targets.filter(type=Target.SIDEREAL).values_list('ra', 'dec', 'name')
    data = []
    for target in targets:
        if target.type == Target.NON_SIDEREAL:
            (ra, dec) = ARC_FUNCTIONS.get(target.scheme)(target)
            data.append(
                dict(
                    lon=ra,
                    lat=dec,
                    text=target.name,
                    hoverinfo='text',
                    mode='lines',
                    type='scattergeo'
                ))

    # still show the sidereal targets
    data.append(
        dict(
            lon=[location[0] for location in locations],
            lat=[location[1] for location in locations],
            text=[location[2] for location in locations],
            hoverinfo='lon+lat+text',
            mode='markers',
            type='scattergeo'
        ))
    data.append(
        dict(
            lon=list(range(0, 360, 60))+[180]*4,
            lat=[0]*6+[-60, -30, 30, 60],
            text=list(range(0, 360, 60))+[-60, -30, 30, 60],
            hoverinfo='none',
            mode='text',
            type='scattergeo'
        ))

    layout = {
        'title': 'Target Distribution (all targets)',
        'hovermode': 'closest',
        'showlegend': False,
        'geo': {
            'projection': {
                'type': 'mollweide',
            },
            'showcoastlines': False,
            'showland': False,
            'lonaxis': {
                'showgrid': True,
                'range': [0, 360],
            },
            'lataxis': {
                'showgrid': True,
                'range': [-90, 90],
            },
        }
    }
    figure = offline.plot(go.Figure(data=data, layout=layout), output_type='div', show_link=False)
    return {'figure': figure}


@register.inclusion_tag('tom_observations/partials/observation_plan_nonsidereal.html')
def observation_plan_nonsidereal(target, facility, length=7, interval=60, airmass_limit=None):
    """
    Displays form and renders plot for visibility calculation. Using this templatetag to render a plot requires that
    the context of the parent view have values for start_time, end_time, and airmass.
    """

    visibility_graph = ''
    start_time = datetime.now()
    end_time = start_time + timedelta(days=length)

    visibility_data = VIS_FUNCTIONS.get(target.scheme)(target, start_time, end_time, interval, airmass_limit)
    plot_data = [
        go.Scatter(x=data[0], y=data[1], mode='lines', name=site) for site, data in visibility_data.items()
    ]
    layout = go.Layout(yaxis=dict(autorange='reversed'))
    visibility_graph = offline.plot(
        go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False
    )

    return {
        'visibility_graph': visibility_graph
    }

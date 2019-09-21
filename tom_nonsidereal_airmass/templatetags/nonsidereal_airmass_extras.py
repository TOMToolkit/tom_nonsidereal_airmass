from django import template
from dateutil.parser import parse
import plotly.graph_objs as go
from plotly import offline

from tom_nonsidereal_airmass.utils import get_visibility
from tom_nonsidereal_airmass.forms import NonsiderealTargetVisibilityForm

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
            'airmass': request.GET.get('airmass')
        })
        if plan_form.is_valid():
            start_time = parse(request.GET['start_time'])
            end_time = parse(request.GET['end_time'])
            if request.GET.get('airmass'):
                airmass_limit = float(request.GET.get('airmass'))
            else:
                airmass_limit = None
            visibility_data = get_visibility(context['object'], start_time, end_time, 10, airmass_limit)
            plot_data = [
                go.Scatter(x=data[0], y=data[1], mode='lines', name=site) for site, data in visibility_data.items()
            ]
            layout = go.Layout(yaxis=dict(autorange='reversed'))
            visibility_graph = offline.plot(
                go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False
            )
    return {
        'form': plan_form,
        'target': context['object'],
        'visibility_graph': visibility_graph
    }

# Nonsidereal Target Airmass TOM Module

This module adds support to generate nonsidereal airmass plots
to the TOM Toolkit.

## Installation:

Install the module into your TOM environment:

    pip install tom-nonsidereal-airmass

or from github by:

    git clone https://github.com/TOMToolkit/tom_nonsidereal_airmass.git

In your TOM's `settings.py`, add this to `INSTALLED_APPS`:

    ...
    'tom_nonsidereal_airmass',

If you have already customized your `target_detail.html`
template you can skip ahead to "At the top of the file."

`cd` into the `templates` directory in the main directory of
your project. Make a directory called `tom_targets` and `cd` into it.

If you installed by git clone, then added the path to your local repo to your
PYTHONPATH variable.

If you installed by pip, you need to find where pip installed the `tomtoolkit`
in the virtual environment you use for your TOM. If you don't remember
where that is, you can do

    pip show tomtoolkit

and the `Location` will tell you where it is.
Copy the following file into your `templates/tom_targets` dir:

    {tomtoolkit location}/tom_targets/templates/tom_targets/target_detail.html

At the top of the file (I put it after the first `{% load %}`),
paste the following line

    {% load nonsidereal_airmass_extras %}

Then to actually display the plots, find the line that says

    {% elif target.type == 'NON_SIDEREAL' %}

and delete the next line with the `<p>...</p>` about not being able to plot non-sidereal airmass.
Change it to

    {% nonsidereal_target_plan %}

In a similar fashion, if you wish to show NON_SIDEREAL targets in the target
distribution plot, you need to two lines to your `templates/tom_targets/target_list.html`.

Copy:

    {% load nonsidereal_airmass_extras %}

into `target_list.html` below `{% load bootstrap4 targets_extras %}`.


Then replace `{% target_distribution filter.qs %}` with:

    {% target_distribution_nonsidereal filter.qs %}


And you're done!
